from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings

# =====================================================
# MODELO 1: Clan (MULTI-TENANT KEY)
# =====================================================

class Clan(models.Model):
    """
    Representa un clan de Clash of Clans.
    Es la clave de multi-tenancy - todos los datos se asocian a un clan.
    """
    
    SYNC_INTERVAL_CHOICES = [
        (24, '24 horas'),
        (48, '48 horas'),
    ]
    
    # Identificadores únicos
    clan_tag = models.CharField(
        max_length=10, 
        unique=True,
        help_text="Tag único del clan en Clash (ej: #2C29G2RJL)"
    )
    clan_name = models.CharField(max_length=255)
    
    # API Token (encriptado)
    _api_token = models.TextField(db_column='api_token')
    
    # Admin del clan
    admin_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='clans_administered'
    )
    
    # ===== Datos del Clan (desde API) =====
    clan_level = models.IntegerField(default=0)
    clan_points = models.IntegerField(default=0)
    clan_builder_base_points = models.IntegerField(default=0)
    clan_capital_points = models.IntegerField(default=0)
    required_trophies = models.IntegerField(default=0)
    
    # Guerra
    war_frequency = models.CharField(
        max_length=20,
        choices=[
            ('always', 'Siempre'),
            ('sometimes', 'A veces'),
            ('never', 'Nunca'),
        ],
        default='always'
    )
    is_war_log_public = models.BooleanField(default=True)
    
    # Recuento de miembros
    members_count = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    badge_url = models.CharField(max_length=500, blank=True)
    
    # ===== Configuración de sincronización =====
    sync_interval = models.IntegerField(
        choices=SYNC_INTERVAL_CHOICES, 
        default=24,
        help_text="Intervalo en horas para sincronizar con la API"
    )
    last_sync = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Última sincronización exitosa"
    )
    next_sync_scheduled = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Próxima sincronización programada"
    )
    
    # ===== Estadísticas generales =====
    war_wins = models.IntegerField(default=0)
    war_losses = models.IntegerField(default=0)
    war_ties = models.IntegerField(default=0)
    war_win_streak = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Clan"
        verbose_name_plural = "Clanes"
    
    def __str__(self):
        return f"{self.clan_name} ({self.clan_tag})"
    
    # ===== Encriptación del API Token =====
    @property
    def api_token(self):
        """Desencripta el API token"""
        if not self._api_token:
            return None
        try:
            cipher = Fernet(settings.ENCRYPTION_KEY)
            return cipher.decrypt(self._api_token.encode()).decode()
        except:
            return None
    
    @api_token.setter
    def api_token(self, value):
        """Encripta y guarda el API token"""
        if value:
            cipher = Fernet(settings.ENCRYPTION_KEY)
            self._api_token = cipher.encrypt(value.encode()).decode()
        else:
            self._api_token = None


# =====================================================
# MODELO 2: UserProfile (User extendido para multi-tenant)
# =====================================================

class UserProfile(models.Model):
    """
    Extiende el User de Django para agregar información de rol y clan.
    """
    
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('member', 'Miembro'),
        ('observer', 'Observador'),
    ]
    
    # Relaciones
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    clan = models.ForeignKey(
        Clan,
        on_delete=models.CASCADE,
        related_name='user_profiles'
    )
    
    # Rol del usuario en el clan
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='member'
    )
    
    # Vinculación opcional con un jugador del clan
    player_tag = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        help_text="Tag del jugador si el usuario es miembro activo"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'clan')
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
    
    def __str__(self):
        return f"{self.user.username} - {self.clan.clan_name} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_member(self):
        return self.role == 'member'
    
    def is_observer(self):
        return self.role == 'observer'