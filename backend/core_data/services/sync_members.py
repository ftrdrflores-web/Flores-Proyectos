import logging
from django.utils import timezone
from users.models import Clan
from players.models import Player
from .clash_api import ClashAPIClient

logger = logging.getLogger(__name__)


# =====================================================
# SERVICIO: Sincronización de Miembros
# =====================================================

class SyncMembersService:
    """
    Servicio que sincroniza los miembros del clan
    desde la API de Clash of Clans hacia PostgreSQL.

    Flujo:
    1. Actualiza info general del clan (nivel, badge, descripción)
    2. Obtiene miembros actuales desde la API
    3. Crea jugadores nuevos (con joined_date)
    4. Actualiza jugadores existentes
    5. Reactiva jugadores que regresan (conservando sus stats)
    6. Marca como 'left' los que ya no están (sin borrar stats)
    """

    def __init__(self, clan: Clan):
        self.clan = clan
        self.client = ClashAPIClient(clan.api_token)

        self.created = 0
        self.updated = 0
        self.reactivated = 0
        self.deactivated = 0
        self.errors = []

    def sync(self) -> dict:
        logger.info(f"Iniciando sync de miembros para clan: {self.clan.clan_name}")

        # ===== PASO 1: Actualizar datos generales del clan =====
        self._sync_clan_info()

        # ===== PASO 2: Obtener miembros desde la API =====
        response = self.client.get_clan_members(self.clan.clan_tag)

        if not response['success']:
            logger.error(f"Error al obtener miembros: {response['error']}")
            return {
                'success': False,
                'error': response['error'],
                'clan': self.clan.clan_name
            }

        api_members = response['data'].get('items', [])

        if not api_members:
            logger.warning(f"No se encontraron miembros para {self.clan.clan_name}")
            return {
                'success': False,
                'error': 'No se encontraron miembros en la API',
                'clan': self.clan.clan_name
            }

        logger.info(f"Miembros obtenidos desde API: {len(api_members)}")

        # ===== PASO 3: Tags activos actuales en BD =====
        existing_active_tags = set(
            Player.objects.filter(
                clan=self.clan,
                status='active'
            ).values_list('player_tag', flat=True)
        )

        api_tags = set(member['tag'] for member in api_members)

        # ===== PASO 4: Procesar cada miembro de la API =====
        for member_data in api_members:
            try:
                self._process_member(member_data)
            except Exception as e:
                error_msg = f"Error procesando {member_data.get('name', 'desconocido')}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)

        # ===== PASO 5: Marcar como 'left' los que ya no están =====
        tags_that_left = existing_active_tags - api_tags

        if tags_that_left:
            left_players = Player.objects.filter(
                clan=self.clan,
                player_tag__in=tags_that_left,
                status='active'
            )
            for player in left_players:
                player.status = 'left'
                player.left_date = timezone.now()
                player.save(update_fields=['status', 'left_date'])
                logger.info(f"👋 Jugador salió del clan: {player.name} ({player.player_tag})")

            self.deactivated = len(tags_that_left)

        # ===== PASO 6: Actualizar clan =====
        self.clan.members_count = len(api_members)
        self.clan.last_sync = timezone.now()
        self.clan.save(update_fields=['members_count', 'last_sync', 'updated_at'])

        result = {
            'success': True,
            'clan': self.clan.clan_name,
            'total_api_members': len(api_members),
            'created': self.created,
            'updated': self.updated,
            'reactivated': self.reactivated,
            'deactivated': self.deactivated,
            'errors': self.errors,
            'synced_at': timezone.now().isoformat()
        }

        logger.info(f"Sync completado: {result}")
        return result

    def _sync_clan_info(self):
        """
        Actualiza datos generales del clan desde la API:
        nivel, badge, descripción, puntos, etc.
        """
        try:
            response = self.client.get_clan_info(self.clan.clan_tag)

            if not response['success']:
                logger.warning(f"No se pudo actualizar info del clan: {response['error']}")
                return

            data = response['data']

            self.clan.clan_name = data.get('name', self.clan.clan_name)
            self.clan.clan_level = data.get('clanLevel', 0)
            self.clan.clan_points = data.get('clanPoints', 0)
            self.clan.clan_builder_base_points = data.get('clanBuilderBasePoints', 0)
            self.clan.clan_capital_points = data.get('clanCapitalPoints', 0)
            self.clan.description = data.get('description', '')
            self.clan.required_trophies = data.get('requiredTrophies', 0)
            self.clan.war_frequency = data.get('warFrequency', 'always')
            self.clan.is_war_log_public = data.get('isWarLogPublic', True)
            self.clan.members_count = data.get('members', 0)

            # War record (solo actualizar si viene en la respuesta)
            if 'warWins' in data:
                self.clan.war_wins = data['warWins']
            if 'warLosses' in data:
                self.clan.war_losses = data['warLosses']
            if 'warTies' in data:
                self.clan.war_ties = data['warTies']
            if 'warWinStreak' in data:
                self.clan.war_win_streak = data['warWinStreak']

            # Badge URL (medium por defecto)
            badge_urls = data.get('badgeUrls', {})
            self.clan.badge_url = badge_urls.get('medium', badge_urls.get('large', ''))

            self.clan.save(update_fields=[
                'clan_name', 'clan_level', 'clan_points',
                'clan_builder_base_points', 'clan_capital_points',
                'description', 'required_trophies', 'war_frequency',
                'is_war_log_public', 'members_count', 'badge_url',
                'war_wins', 'war_losses', 'war_ties', 'war_win_streak',
                'updated_at',
            ])

            logger.info(
                f"✅ Clan actualizado: {self.clan.clan_name} "
                f"Nivel {self.clan.clan_level} | {self.clan.members_count} miembros"
            )

        except Exception as e:
            logger.error(f"Error en _sync_clan_info: {e}")
            self.errors.append(f"Error actualizando info del clan: {str(e)}")

    def _process_member(self, member_data: dict):
        """
        Procesa un miembro:
        - Nuevo → crea con joined_date
        - Activo → actualiza datos
        - Inactivo/left/expelled → REACTIVA conservando todas sus stats
        """
        player_tag = member_data['tag']

        new_data = {
            'name': member_data.get('name', ''),
            'role': member_data.get('role', 'member'),
            'town_hall_level': member_data.get('townHallLevel', 0),
            'exp_level': member_data.get('expLevel', 0),
            'trophies': member_data.get('trophies', 0),
            'builder_base_trophies': member_data.get('builderBaseTrophies', 0),
            'donations': member_data.get('donations', 0),
            'donations_received': member_data.get('donationsReceived', 0),
            'clan_rank': member_data.get('clanRank'),
            'previous_clan_rank': member_data.get('previousClanRank'),
            'league_info': member_data.get('league', {}),
            'league_tier_info': member_data.get('leagueTier', {}),
            'builder_base_league': member_data.get('builderBaseLeague', {}),
            'player_house_elements': member_data.get('playerHouse', {}).get('elements', []),
        }

        try:
            # Jugador ya existe en BD
            player = Player.objects.get(clan=self.clan, player_tag=player_tag)
            prev_status = player.status

            # Actualizar datos actuales
            for field, value in new_data.items():
                setattr(player, field, value)

            if prev_status in ['left', 'expelled', 'inactive']:
                # ===== REACTIVAR: regresó al clan =====
                # Sus stats (PlayerStats, WarParticipant, attacks) se conservan intactos
                player.status = 'active'
                player.left_date = None
                player.joined_date = timezone.now()  # Nueva fecha de ingreso
                player.save()
                self.reactivated += 1
                logger.info(
                    f"🔄 REACTIVADO: {player.name} ({player_tag}) "
                    f"[venía como '{prev_status}'] → stats conservadas"
                )
            else:
                player.status = 'active'
                player.save()
                self.updated += 1

        except Player.DoesNotExist:
            # ===== NUEVO jugador =====
            Player.objects.create(
                clan=self.clan,
                player_tag=player_tag,
                status='active',
                joined_date=timezone.now(),
                **new_data
            )
            self.created += 1
            logger.debug(f"➕ Nuevo: {member_data.get('name')} ({player_tag})")


# =====================================================
# FUNCIÓN HELPER
# =====================================================

def sync_clan_members(clan_id: int) -> dict:
    """
    Sincroniza miembros y datos del clan por ID.

    Uso:
        from core_data.services.sync_members import sync_clan_members
        sync_clan_members(1)
    """
    try:
        clan = Clan.objects.get(id=clan_id)
    except Clan.DoesNotExist:
        return {
            'success': False,
            'error': f'Clan con ID {clan_id} no encontrado en la BD'
        }

    service = SyncMembersService(clan)
    return service.sync()