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
# SERVICIO: Sincronización de Guerra Actual
# =====================================================

class SyncCurrentWarService:
    """
    Servicio que sincroniza la guerra actual del clan
    desde la API de Clash of Clans hacia PostgreSQL.

    A diferencia del warlog, este endpoint provee:
    - Ataques individuales detallados
    - Posiciones en el mapa
    - Defensas recibidas
    - Estado en tiempo real

    Flujo:
    1. Obtiene guerra actual desde /currentwar
    2. Verifica si ya existe en BD
    3. Crea o actualiza la guerra
    4. Procesa participantes
    5. Procesa ataques individuales
    6. Calcula defensas
    """

    def __init__(self, clan: Clan):
        self.clan = clan
        self.client = ClashAPIClient(clan.api_token)

        # Contadores
        self.attacks_created = 0
        self.participants_created = 0
        self.participants_updated = 0
        self.errors = []

    def sync(self) -> dict:
        """
        Ejecuta la sincronización de la guerra actual.

        Returns:
            Diccionario con el resultado
        """
        logger.info(f"Iniciando sync de guerra actual para: {self.clan.clan_name}")

        # ===== PASO 1: Obtener guerra actual desde API =====
        response = self.client.get_current_war(self.clan.clan_tag)

        if not response['success']:
            logger.error(f"Error al obtener guerra actual: {response['error']}")
            return {
                'success': False,
                'error': response['error'],
                'clan': self.clan.clan_name
            }

        war_data = response['data']
        state = war_data.get('state', '')

        # ===== PASO 2: Verificar si hay guerra activa =====
        if state == 'notInWar':
            logger.info(f"{self.clan.clan_name} no está en guerra actualmente")
            return {
                'success': True,
                'state': 'notInWar',
                'message': 'El clan no está en guerra actualmente',
                'clan': self.clan.clan_name
            }

        # ===== PASO 3: Crear o actualizar la guerra =====
        war = self._process_war(war_data)

        if not war:
            return {
                'success': False,
                'error': 'No se pudo crear/actualizar la guerra',
                'clan': self.clan.clan_name
            }

        # ===== PASO 4: Procesar participantes y ataques =====
        clan_members = war_data.get('clan', {}).get('members', [])
        opponent_members = war_data.get('opponent', {}).get('members', [])

        # Procesar miembros del clan (con sus ataques)
        for member_data in clan_members:
            try:
                self._process_participant(war, member_data, opponent_members)
            except Exception as e:
                error_msg = f"Error procesando participante {member_data.get('name')}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)

        # ===== PASO 5: Calcular defensas =====
        try:
            self._process_defenses(war, clan_members, opponent_members)
        except Exception as e:
            logger.error(f"Error calculando defensas: {str(e)}")
            self.errors.append(f"Error en defensas: {str(e)}")

        # ===== RESULTADO FINAL =====
        result = {
            'success': True,
            'clan': self.clan.clan_name,
            'war_state': state,
            'war_id': war.war_id,
            'participants_created': self.participants_created,
            'participants_updated': self.participants_updated,
            'attacks_created': self.attacks_created,
            'errors': self.errors,
            'synced_at': timezone.now().isoformat()
        }

        logger.info(f"Sync de guerra actual completado: {result}")
        return result

    def _generate_war_id(self, war_data: dict) -> str:
        """Genera ID único para la guerra actual."""
        clan_tag = self.clan.clan_tag
        start_time = war_data.get('startTime', '')
        end_time = war_data.get('endTime', '')
        opponent_tag = war_data.get('opponent', {}).get('tag', 'unknown')

        unique_string = f"{clan_tag}_{start_time}_{end_time}_{opponent_tag}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def _parse_clash_datetime(self, datetime_str: str):
        """Convierte formato de fecha de Clash al formato de Django."""
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

    def _process_war(self, war_data: dict) -> War:
        """
        Crea o actualiza la guerra actual en BD.

        Args:
            war_data: Datos completos de la guerra

        Returns:
            Objeto War creado o actualizado
        """
        war_id = self._generate_war_id(war_data)
        state = war_data.get('state', 'inWar')

        clan_data = war_data.get('clan', {})
        opponent_data = war_data.get('opponent', {})

        start_time = self._parse_clash_datetime(war_data.get('startTime'))
        end_time = self._parse_clash_datetime(war_data.get('endTime'))
        prep_time = self._parse_clash_datetime(war_data.get('preparationStartTime'))

        # Determinar resultado si la guerra terminó
        result = None
        if state == 'warEnded':
            clan_stars = clan_data.get('stars', 0)
            opponent_stars = opponent_data.get('stars', 0)
            clan_destruction = clan_data.get('destructionPercentage', 0)
            opponent_destruction = opponent_data.get('destructionPercentage', 0)

            if clan_stars > opponent_stars:
                result = 'win'
            elif clan_stars < opponent_stars:
                result = 'loss'
            elif clan_destruction > opponent_destruction:
                result = 'win'
            elif clan_destruction < opponent_destruction:
                result = 'loss'
            else:
                result = 'tie'

        war_defaults = {
            'state': state,
            'clan_tag': clan_data.get('tag', self.clan.clan_tag),
            'clan_name': clan_data.get('name', self.clan.clan_name),
            'opponent_tag': opponent_data.get('tag', 'unknown'),
            'opponent_name': opponent_data.get('name', 'Desconocido'),
            'opponent_clan_level': opponent_data.get('clanLevel', 0),
            'team_size': war_data.get('teamSize', 0),
            'attacks_per_member': war_data.get('attacksPerMember', 2),
            'battle_modifier': war_data.get('battleModifier', 'none'),
            'preparation_start_time': prep_time,
            'start_time': start_time or timezone.now(),
            'end_time': end_time or timezone.now(),
            'clan_attacks': clan_data.get('attacks', 0),
            'clan_stars': clan_data.get('stars', 0),
            'clan_destruction_percentage': clan_data.get('destructionPercentage', 0.0),
            'opponent_stars': opponent_data.get('stars', 0),
            'opponent_destruction_percentage': opponent_data.get('destructionPercentage', 0.0),
            'result': result,
        }

        war, created = War.objects.update_or_create(
            war_id=war_id,
            clan=self.clan,
            defaults=war_defaults
        )

        action = "creada" if created else "actualizada"
        logger.info(f"Guerra {action}: {self.clan.clan_name} vs {war.opponent_name} (Estado: {state})")
        return war

    def _process_participant(self, war: War, member_data: dict, opponent_members: list):
        """
        Procesa un participante del clan y sus ataques.

        Args:
            war: Objeto War
            member_data: Datos del miembro desde la API
            opponent_members: Lista de miembros del oponente
        """
        player_tag = member_data.get('tag')

        # Buscar jugador en BD
        try:
            player = Player.objects.get(clan=self.clan, player_tag=player_tag)
        except Player.DoesNotExist:
            # Jugador no está en BD (puede ser nuevo), crearlo básico
            player = Player.objects.create(
                clan=self.clan,
                player_tag=player_tag,
                name=member_data.get('name', 'Desconocido'),
                role='member',
                town_hall_level=member_data.get('townhallLevel', 0),
                exp_level=0,
                status='active'
            )
            logger.info(f"Nuevo jugador creado desde guerra: {player.name}")

        # Obtener ataques realizados
        attacks_data = member_data.get('attacks', [])

        # Crear o actualizar participante
        participant_defaults = {
            'map_position': member_data.get('mapPosition', 0),
            'town_hall_level': member_data.get('townhallLevel', 0),
            'attacks_used': len(attacks_data),
            'total_stars': sum(a.get('stars', 0) for a in attacks_data),
            'total_destruction_percentage': sum(
                a.get('destructionPercentage', 0) for a in attacks_data
            ),
            'opponent_attacks': member_data.get('opponentAttacks', 0),
        }

        participant, created = WarParticipant.objects.update_or_create(
            war=war,
            player=player,
            defaults=participant_defaults
        )

        if created:
            self.participants_created += 1
        else:
            self.participants_updated += 1

        # ===== Procesar ataques individuales =====
        for attack_data in attacks_data:
            self._process_attack(war, participant, attack_data, opponent_members)

    def _process_attack(
        self,
        war: War,
        participant: WarParticipant,
        attack_data: dict,
        opponent_members: list
    ):
        """
        Procesa un ataque individual.

        Args:
            war: Objeto War
            participant: Objeto WarParticipant
            attack_data: Datos del ataque desde la API
            opponent_members: Lista de miembros del oponente para obtener nombres
        """
        attacker_tag = attack_data.get('attackerTag', '')
        defender_tag = attack_data.get('defenderTag', '')
        order = attack_data.get('order', 0)

        # Verificar si el ataque ya existe
        if Attack.objects.filter(
            war=war,
            attacker_tag=attacker_tag,
            order=order
        ).exists():
            return

        # Buscar nombre del defensor
        defender_name = ''
        defender_position = 0
        for opponent in opponent_members:
            if opponent.get('tag') == defender_tag:
                defender_name = opponent.get('name', '')
                defender_position = opponent.get('mapPosition', 0)
                break

        Attack.objects.create(
            war=war,
            war_participant=participant,
            attacker_tag=attacker_tag,
            attacker_name=participant.player.name,
            defender_tag=defender_tag,
            defender_name=defender_name,
            defender_position=defender_position,
            stars=attack_data.get('stars', 0),
            destruction_percentage=attack_data.get('destructionPercentage', 0.0),
            order=order,
            duration=attack_data.get('duration', 0),
        )

        self.attacks_created += 1
        logger.debug(
            f"Ataque creado: {participant.player.name} → "
            f"{defender_name} ({attack_data.get('stars')}⭐)"
        )

    def _process_defenses(
        self,
        war: War,
        clan_members: list,
        opponent_members: list
    ):
        """
        Calcula y guarda las defensas de cada jugador del clan.
        Se basa en los ataques recibidos del oponente.

        Args:
            war: Objeto War
            clan_members: Miembros del clan
            opponent_members: Miembros del oponente (con sus ataques)
        """
        # Construir mapa de defensas: {player_tag: [ataques_recibidos]}
        defenses_map = {}

        for opponent in opponent_members:
            for attack in opponent.get('attacks', []):
                defender_tag = attack.get('defenderTag')
                if defender_tag not in defenses_map:
                    defenses_map[defender_tag] = []
                defenses_map[defender_tag].append(attack)

        # Guardar defensas para cada jugador del clan
        for member_data in clan_members:
            player_tag = member_data.get('tag')
            attacks_received = defenses_map.get(player_tag, [])

            try:
                player = Player.objects.get(clan=self.clan, player_tag=player_tag)
            except Player.DoesNotExist:
                continue

            stars_received = sum(a.get('stars', 0) for a in attacks_received)
            destruction_received = sum(
                a.get('destructionPercentage', 0) for a in attacks_received
            )
            times_attacked = len(attacks_received)
            successful_defenses = sum(
                1 for a in attacks_received if a.get('stars', 0) == 0
            )

            Defense.objects.update_or_create(
                war=war,
                player=player,
                defaults={
                    'times_attacked': times_attacked,
                    'stars_received': stars_received,
                    'destruction_received': (
                        destruction_received / times_attacked
                        if times_attacked > 0 else 0.0
                    ),
                    'successful_defenses': successful_defenses,
                }
            )


# =====================================================
# FUNCIÓN HELPER
# =====================================================

def sync_current_war(clan_id: int) -> dict:
    """
    Función helper para sincronizar la guerra actual de un clan.

    Args:
        clan_id: ID del clan en la BD

    Returns:
        Diccionario con el resultado

    Ejemplo de uso:
        result = sync_current_war(1)
        print(result)
    """
    try:
        clan = Clan.objects.get(id=clan_id)
    except Clan.DoesNotExist:
        return {
            'success': False,
            'error': f'Clan con ID {clan_id} no encontrado en la BD'
        }

    service = SyncCurrentWarService(clan)
    return service.sync()