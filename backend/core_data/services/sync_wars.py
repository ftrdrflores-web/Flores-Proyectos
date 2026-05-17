import logging
import hashlib
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from users.models import Clan
from players.models import Player
from wars.models import War, WarParticipant, Attack, Defense
from .clash_api import ClashAPIClient

logger = logging.getLogger(__name__)


# =====================================================
# SERVICIO: Sincronización de Historial de Guerras
# =====================================================

class SyncWarsService:
    """
    Servicio que sincroniza el historial de guerras del clan
    desde la API de Clash of Clans hacia PostgreSQL.

    Flujo:
    1. Obtiene historial de guerras desde la API (/warlog)
    2. Por cada guerra, verifica si ya existe en BD
    3. Si no existe, la crea con sus datos generales
    4. Evita duplicados automáticamente
    """

    def __init__(self, clan: Clan):
        self.clan = clan
        self.client = ClashAPIClient(clan.api_token)

        # Contadores
        self.created = 0
        self.skipped = 0
        self.errors = []

    def sync(self, limit: int = 20) -> dict:
        """
        Ejecuta la sincronización del historial de guerras.

        Args:
            limit: Número máximo de guerras a obtener (default 20)

        Returns:
            Diccionario con el resultado
        """
        logger.info(f"Iniciando sync de guerras para: {self.clan.clan_name}")

        # ===== PASO 1: Obtener historial desde la API =====
        response = self.client.get_war_log(self.clan.clan_tag, limit=limit)

        if not response['success']:
            logger.error(f"Error al obtener guerras: {response['error']}")
            return {
                'success': False,
                'error': response['error'],
                'clan': self.clan.clan_name
            }

        wars_data = response['data'].get('items', [])

        if not wars_data:
            logger.warning(f"No se encontraron guerras para {self.clan.clan_name}")
            return {
                'success': False,
                'error': 'No se encontraron guerras en la API',
                'clan': self.clan.clan_name
            }

        logger.info(f"Guerras obtenidas desde API: {len(wars_data)}")

        # ===== PASO 2: Procesar cada guerra =====
        for war_data in wars_data:
            try:
                self._process_war(war_data)
            except Exception as e:
                error_msg = f"Error procesando guerra: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)

        # ===== RESULTADO FINAL =====
        result = {
            'success': True,
            'clan': self.clan.clan_name,
            'total_api_wars': len(wars_data),
            'created': self.created,
            'skipped': self.skipped,
            'errors': self.errors,
            'synced_at': timezone.now().isoformat()
        }

        logger.info(f"Sync de guerras completado: {result}")
        return result

    def _generate_war_id(self, war_data: dict) -> str:
        """
        Genera un ID único para la guerra basado en sus datos.
        La API de warlog NO provee un ID único, así que lo generamos.

        Args:
            war_data: Datos de la guerra desde la API

        Returns:
            String con el ID único generado
        """
        clan_tag = self.clan.clan_tag
        end_time = war_data.get('endTime', '')
        opponent_tag = war_data.get('opponent', {}).get('tag', 'unknown')
        team_size = war_data.get('teamSize', 0)

        unique_string = f"{clan_tag}_{end_time}_{opponent_tag}_{team_size}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def _parse_clash_datetime(self, datetime_str: str):
        """
        Convierte el formato de fecha de Clash (20260515T013333.000Z)
        al formato de Django.

        Args:
            datetime_str: Fecha en formato Clash

        Returns:
            Objeto datetime o None
        """
        if not datetime_str:
            return None
        try:
            # Convertir formato Clash a ISO: 20260515T013333.000Z → 2026-05-15T01:33:33Z
            formatted = (
                f"{datetime_str[:4]}-{datetime_str[4:6]}-{datetime_str[6:8]}"
                f"T{datetime_str[9:11]}:{datetime_str[11:13]}:{datetime_str[13:15]}Z"
            )
            return parse_datetime(formatted)
        except Exception as e:
            logger.error(f"Error parseando fecha {datetime_str}: {e}")
            return None

    def _process_war(self, war_data: dict):
        war_id = self._generate_war_id(war_data)

        if War.objects.filter(war_id=war_id).exists():
            self.skipped += 1
            return

        clan_data = war_data.get('clan', {})
        opponent_data = war_data.get('opponent', {})
        end_time = self._parse_clash_datetime(war_data.get('endTime'))

        if not end_time:
            self.errors.append(f"Fecha inválida: {war_data.get('endTime')}")
            return

        # ===== DETECTAR SI ES GUERRA DE LIGA =====
        opponent_tag = opponent_data.get('tag', '')
        opponent_name = opponent_data.get('name', '')
        is_league = not opponent_tag or not opponent_name

        War.objects.create(
            clan=self.clan,
            war_id=war_id,
            state='warEnded',

            clan_tag=clan_data.get('tag', self.clan.clan_tag),
            clan_name=clan_data.get('name', self.clan.clan_name),

            # Si es liga, marcar claramente
            opponent_tag=opponent_tag if opponent_tag else 'CWL',
            opponent_name=opponent_name if opponent_name else 'Liga de Guerra (CWL)',
            opponent_clan_level=opponent_data.get('clanLevel', 0),

            team_size=war_data.get('teamSize', 0),
            attacks_per_member=war_data.get('attacksPerMember', 2),
            battle_modifier=war_data.get('battleModifier', 'none'),

            preparation_start_time=None,
            start_time=end_time,
            end_time=end_time,

            clan_attacks=clan_data.get('attacks', 0),
            clan_stars=clan_data.get('stars', 0),
            clan_destruction_percentage=clan_data.get('destructionPercentage', 0.0),
            clan_exp_earned=clan_data.get('expEarned', 0),

            opponent_stars=opponent_data.get('stars', 0),
            opponent_destruction_percentage=opponent_data.get('destructionPercentage', 0.0),

            result=self._parse_result(war_data.get('result')),

            # ===== FLAG DE LIGA =====
            is_league_war=is_league,
        )

        self.created += 1
    def _parse_result(self, result: str) -> str:
        """
        Traduce el resultado de la API al formato del modelo.
        API usa 'lose', modelo usa 'loss'.
        """
        mapping = {
            'win': 'win',
            'lose': 'loss',
            'tie': 'tie',
        }
        return mapping.get(result, None)

# =====================================================
# FUNCIÓN HELPER
# =====================================================

def sync_clan_wars(clan_id: int, limit: int = 20) -> dict:
    """
    Función helper para sincronizar guerras de un clan por ID.

    Args:
        clan_id: ID del clan en la BD
        limit: Número máximo de guerras a sincronizar

    Returns:
        Diccionario con el resultado

    Ejemplo de uso:
        result = sync_clan_wars(1, limit=20)
        print(result)
    """
    try:
        clan = Clan.objects.get(id=clan_id)
    except Clan.DoesNotExist:
        return {
            'success': False,
            'error': f'Clan con ID {clan_id} no encontrado en la BD'
        }

    service = SyncWarsService(clan)
    return service.sync(limit=limit)