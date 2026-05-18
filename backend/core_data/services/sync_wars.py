import logging
import hashlib
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db.models import Count, Q
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
    4. Actualiza contadores del clan (war_wins, war_losses, war_ties)
    5. Evita duplicados automáticamente
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

        # ===== PASO 3: Actualizar contadores del clan =====
        self._update_clan_war_counters()

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

    def _update_clan_war_counters(self):
        """
        Recalcula y actualiza war_wins, war_losses, war_ties en el modelo Clan
        basándose en las guerras terminadas almacenadas en la BD.
        """
        try:
            # Contar resultados desde las guerras en BD (solo guerras terminadas)
            wars_finished = War.objects.filter(
                clan=self.clan,
                state='warEnded',
                result__isnull=False
            )

            wins   = wars_finished.filter(result='win').count()
            losses = wars_finished.filter(result='loss').count()
            ties   = wars_finished.filter(result='tie').count()

            # Calcular racha de victorias actual (guerras consecutivas más recientes)
            win_streak = self._calculate_win_streak()

            # Actualizar el clan
            self.clan.war_wins = wins
            self.clan.war_losses = losses
            self.clan.war_ties = ties
            self.clan.war_win_streak = win_streak
            self.clan.save(update_fields=['war_wins', 'war_losses', 'war_ties', 'war_win_streak', 'updated_at'])

            logger.info(
                f"Contadores actualizados → "
                f"V:{wins} D:{losses} E:{ties} Racha:{win_streak}"
            )

        except Exception as e:
            logger.error(f"Error actualizando contadores del clan: {e}")
            self.errors.append(f"Error actualizando contadores: {str(e)}")

    def _calculate_win_streak(self) -> int:
        """
        Calcula la racha de victorias consecutivas más reciente.
        Recorre las guerras terminadas de más reciente a más antigua.
        """
        try:
            recent_wars = War.objects.filter(
                clan=self.clan,
                state='warEnded',
                result__isnull=False
            ).order_by('-end_time').values_list('result', flat=True)

            streak = 0
            for result in recent_wars:
                if result == 'win':
                    streak += 1
                else:
                    break  # Se rompió la racha

            return streak
        except Exception:
            return 0

    def _generate_war_id(self, war_data: dict) -> str:
        """
        Genera un ID único para la guerra basado en sus datos.
        La API de warlog NO provee un ID único, así que lo generamos.
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
        """
        if not datetime_str:
            return None
        try:
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

        opponent_tag = opponent_data.get('tag', '')
        opponent_name = opponent_data.get('name', '')
        is_league = not opponent_tag or not opponent_name

        War.objects.create(
            clan=self.clan,
            war_id=war_id,
            state='warEnded',

            clan_tag=clan_data.get('tag', self.clan.clan_tag),
            clan_name=clan_data.get('name', self.clan.clan_name),

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
            is_league_war=is_league,
        )

        self.created += 1

    def _parse_result(self, result: str) -> str:
        mapping = {
            'win': 'win',
            'lose': 'loss',
            'tie': 'tie',
        }
        return mapping.get(result, None)


# =====================================================
# SERVICIO: Fix de contadores (para corregir datos existentes)
# =====================================================

class FixClanWarCountersService:
    """
    Servicio para recalcular y corregir los contadores de guerra
    de un clan usando los datos ya almacenados en la BD.

    Usar cuando los contadores están en 0 pero las guerras existen.
    """

    def __init__(self, clan: Clan):
        self.clan = clan

    def fix(self) -> dict:
        try:
            wars_finished = War.objects.filter(
                clan=self.clan,
                state='warEnded',
                result__isnull=False
            )

            wins   = wars_finished.filter(result='win').count()
            losses = wars_finished.filter(result='loss').count()
            ties   = wars_finished.filter(result='tie').count()
            total  = wins + losses + ties

            # Calcular racha
            streak = 0
            recent = wars_finished.order_by('-end_time').values_list('result', flat=True)
            for r in recent:
                if r == 'win':
                    streak += 1
                else:
                    break

            win_rate = round((wins / total) * 100, 1) if total > 0 else 0.0

            self.clan.war_wins = wins
            self.clan.war_losses = losses
            self.clan.war_ties = ties
            self.clan.war_win_streak = streak
            self.clan.save(update_fields=[
                'war_wins', 'war_losses', 'war_ties',
                'war_win_streak', 'updated_at'
            ])

            logger.info(f"Fix contadores {self.clan.clan_name}: V:{wins} D:{losses} E:{ties} Racha:{streak}")

            return {
                'success': True,
                'clan': self.clan.clan_name,
                'wins': wins,
                'losses': losses,
                'ties': ties,
                'total': total,
                'win_rate': win_rate,
                'win_streak': streak,
            }

        except Exception as e:
            logger.error(f"Error en fix de contadores: {e}")
            return {'success': False, 'error': str(e)}


# =====================================================
# FUNCIONES HELPER
# =====================================================

def sync_clan_wars(clan_id: int, limit: int = 20) -> dict:
    """
    Sincroniza guerras de un clan por ID.
    """
    try:
        clan = Clan.objects.get(id=clan_id)
    except Clan.DoesNotExist:
        return {'success': False, 'error': f'Clan con ID {clan_id} no encontrado'}

    service = SyncWarsService(clan)
    return service.sync(limit=limit)


def fix_clan_war_counters(clan_id: int) -> dict:
    """
    Corrige los contadores de guerra de un clan usando datos existentes en BD.

    Usar en Django shell:
        from core_data.services.sync_wars import fix_clan_war_counters
        fix_clan_war_counters(1)
    """
    try:
        clan = Clan.objects.get(id=clan_id)
    except Clan.DoesNotExist:
        return {'success': False, 'error': f'Clan con ID {clan_id} no encontrado'}

    service = FixClanWarCountersService(clan)
    return service.fix()