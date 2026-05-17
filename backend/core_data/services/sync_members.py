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
    1. Obtiene miembros actuales desde la API
    2. Compara con los miembros en BD
    3. Crea nuevos jugadores
    4. Actualiza jugadores existentes
    5. Marca como inactivos los que ya no están en el clan
    """
    
    def __init__(self, clan: Clan):
        """
        Inicializa el servicio con el clan a sincronizar.
        
        Args:
            clan: Objeto Clan de la BD
        """
        self.clan = clan
        self.client = ClashAPIClient(clan.api_token)
        
        # Contadores para el reporte final
        self.created = 0
        self.updated = 0
        self.deactivated = 0
        self.errors = []
    
    def sync(self) -> dict:
        """
        Ejecuta la sincronización completa de miembros.
        
        Returns:
            Diccionario con el resultado de la sincronización
        """
        logger.info(f"Iniciando sync de miembros para clan: {self.clan.clan_name}")
        
        # ===== PASO 1: Obtener miembros desde la API =====
        response = self.client.get_clan_members(self.clan.clan_tag)
        
        if not response['success']:
            logger.error(f"Error al obtener miembros: {response['error']}")
            return {
                'success': False,
                'error': response['error'],
                'clan': self.clan.clan_name
            }
        
        # Extraer lista de miembros del JSON
        api_members = response['data'].get('items', [])
        
        if not api_members:
            logger.warning(f"No se encontraron miembros para {self.clan.clan_name}")
            return {
                'success': False,
                'error': 'No se encontraron miembros en la API',
                'clan': self.clan.clan_name
            }
        
        logger.info(f"Miembros obtenidos desde API: {len(api_members)}")
        
        # ===== PASO 2: Obtener tags actuales en BD =====
        existing_tags = set(
            Player.objects.filter(
                clan=self.clan,
                status='active'
            ).values_list('player_tag', flat=True)
        )
        
        # Tags que vienen de la API
        api_tags = set(member['tag'] for member in api_members)
        
        # ===== PASO 3: Procesar cada miembro de la API =====
        for member_data in api_members:
            try:
                self._process_member(member_data)
            except Exception as e:
                error_msg = f"Error procesando {member_data.get('name', 'desconocido')}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)
        
        # ===== PASO 4: Marcar como inactivos los que ya no están =====
        tags_that_left = existing_tags - api_tags
        
        if tags_that_left:
            deactivated = Player.objects.filter(
                clan=self.clan,
                player_tag__in=tags_that_left
            ).update(
                status='left',
                left_date=timezone.now()
            )
            self.deactivated = deactivated
            logger.info(f"Jugadores que salieron del clan: {deactivated}")
        
        # ===== PASO 5: Actualizar contador de miembros en el clan =====
        self.clan.members_count = len(api_members)
        self.clan.last_sync = timezone.now()
        self.clan.save(update_fields=['members_count', 'last_sync'])
        
        # ===== RESULTADO FINAL =====
        result = {
            'success': True,
            'clan': self.clan.clan_name,
            'total_api_members': len(api_members),
            'created': self.created,
            'updated': self.updated,
            'deactivated': self.deactivated,
            'errors': self.errors,
            'synced_at': timezone.now().isoformat()
        }
        
        logger.info(f"Sync completado: {result}")
        return result
    
    def _process_member(self, member_data: dict):
        """
        Procesa un miembro individual: crea o actualiza en BD.
        
        Args:
            member_data: Datos del miembro desde la API
        """
        player_tag = member_data['tag']
        
        # Preparar datos del jugador
        player_defaults = {
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
            'status': 'active',
        }
        
        # ===== Crear o actualizar el jugador =====
        player, created = Player.objects.update_or_create(
            clan=self.clan,
            player_tag=player_tag,
            defaults=player_defaults
        )
        
        if created:
            self.created += 1
            logger.debug(f"Nuevo jugador creado: {player.name} ({player_tag})")
        else:
            self.updated += 1
            logger.debug(f"Jugador actualizado: {player.name} ({player_tag})")


# =====================================================
# FUNCIÓN HELPER: Fácil de llamar desde cualquier lugar
# =====================================================

def sync_clan_members(clan_id: int) -> dict:
    """
    Función helper para sincronizar miembros de un clan por ID.
    
    Args:
        clan_id: ID del clan en la BD
    
    Returns:
        Diccionario con el resultado de la sincronización
    
    Ejemplo de uso:
        result = sync_clan_members(1)
        print(result)
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