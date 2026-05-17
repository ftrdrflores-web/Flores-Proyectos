import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# =====================================================
# CLASE BASE: Conexión con la API de Clash of Clans
# =====================================================

class ClashAPIClient:
    """
    Cliente base para consumir la API oficial de Clash of Clans.
    Maneja autenticación, errores y formato de respuestas.
    """
    
    BASE_URL = "https://api.clashofclans.com/v1"
    
    def __init__(self, api_token: str):
        """
        Inicializa el cliente con el API token del clan.
        
        Args:
            api_token: Token de autenticación del clan
        """
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _format_tag(self, tag: str) -> str:
        """
        Formatea el tag para usarlo en URLs.
        El # se convierte en %23 para URLs.
        
        Args:
            tag: Tag del clan o jugador (ej: #2C29G2RJL)
        
        Returns:
            Tag formateado para URL (ej: %232C29G2RJL)
        """
        return tag.replace('#', '%23')
    
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """
        Realiza una petición GET a la API de Clash.
        
        Args:
            endpoint: Endpoint de la API (ej: /clans/%232C29G2RJL/members)
            params: Parámetros opcionales de la petición
        
        Returns:
            Diccionario con la respuesta JSON o None si hay error
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            # ===== Manejo de errores HTTP =====
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': 200
                }
            
            elif response.status_code == 403:
                logger.error(f"API Error 403: Token inválido o sin permisos para {url}")
                return {
                    'success': False,
                    'error': 'Token inválido o sin permisos',
                    'status_code': 403
                }
            
            elif response.status_code == 404:
                logger.error(f"API Error 404: Recurso no encontrado en {url}")
                return {
                    'success': False,
                    'error': 'Clan o jugador no encontrado',
                    'status_code': 404
                }
            
            elif response.status_code == 429:
                logger.warning(f"API Error 429: Rate limit alcanzado para {url}")
                return {
                    'success': False,
                    'error': 'Límite de peticiones alcanzado, intenta más tarde',
                    'status_code': 429
                }
            
            elif response.status_code == 503:
                logger.warning(f"API Error 503: Servicio no disponible en {url}")
                return {
                    'success': False,
                    'error': 'API de Clash temporalmente no disponible',
                    'status_code': 503
                }
            
            else:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return {
                    'success': False,
                    'error': f'Error inesperado: {response.status_code}',
                    'status_code': response.status_code
                }
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout al conectar con {url}")
            return {
                'success': False,
                'error': 'Timeout: La API tardó demasiado en responder',
                'status_code': None
            }
        
        except requests.exceptions.ConnectionError:
            logger.error(f"Error de conexión al conectar con {url}")
            return {
                'success': False,
                'error': 'Error de conexión: Verifica tu internet',
                'status_code': None
            }
        
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return {
                'success': False,
                'error': f'Error inesperado: {str(e)}',
                'status_code': None
            }
    
    # =====================================================
    # ENDPOINTS DISPONIBLES
    # =====================================================
    
    def get_clan_info(self, clan_tag: str) -> dict:
        """
        Obtiene información general del clan.
        Endpoint: GET /clans/{clanTag}
        """
        formatted_tag = self._format_tag(clan_tag)
        return self._make_request(f"/clans/{formatted_tag}")
    
    def get_clan_members(self, clan_tag: str, limit: int = 50) -> dict:
        """
        Obtiene la lista de miembros actuales del clan.
        Endpoint: GET /clans/{clanTag}/members
        """
        formatted_tag = self._format_tag(clan_tag)
        return self._make_request(
            f"/clans/{formatted_tag}/members",
            params={'limit': limit}
        )
    
    def get_war_log(self, clan_tag: str, limit: int = 20) -> dict:
        """
        Obtiene el historial de guerras del clan.
        Endpoint: GET /clans/{clanTag}/warlog
        """
        formatted_tag = self._format_tag(clan_tag)
        return self._make_request(
            f"/clans/{formatted_tag}/warlog",
            params={'limit': limit}
        )
    
    def get_current_war(self, clan_tag: str) -> dict:
        """
        Obtiene la guerra actual del clan.
        Endpoint: GET /clans/{clanTag}/currentwar
        """
        formatted_tag = self._format_tag(clan_tag)
        return self._make_request(f"/clans/{formatted_tag}/currentwar")
    
    def get_player_info(self, player_tag: str) -> dict:
        """
        Obtiene información detallada de un jugador.
        Endpoint: GET /players/{playerTag}
        """
        formatted_tag = self._format_tag(player_tag)
        return self._make_request(f"/players/{formatted_tag}")
    
    def validate_clan_tag(self, clan_tag: str) -> bool:
        """
        Valida que un clan tag exista en la API.
        Retorna True si existe, False si no.
        """
        result = self.get_clan_info(clan_tag)
        return result['success']
    
    def validate_player_tag(self, player_tag: str) -> bool:
        """
        Valida que un player tag exista en la API.
        Retorna True si existe, False si no.
        """
        result = self.get_player_info(player_tag)
        return result['success']