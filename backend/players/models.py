from django.db import models
from django.contrib.postgres.fields import JSONField
from users.models import Clan


# =====================================================
# MODELO 3: Player (Jugador del clan)
# =====================================================

class Player(models.Model):
    """
    Representa un jugador del clan.
    Cada jugador pertenece a exactamente un clan (multi-tenant).
    """
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('coLeader', 'Co-líder'),
        ('leader', 'Líder'),
        ('member', 'Miembro'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('expelled', 'Expulsado'),
        ('left', 'Se fue'),
    ]
    
    # ===== Identificadores =====
    clan = models.ForeignKey(
        Clan,
        on_delete=models.CASCADE,
        related_name='players'
    )
    player_tag = models.CharField(
        max_length=20,
        help_text="Tag único del jugador en Clash (ej: #PYU89U08L)"
    )
    name = models.CharField(max_length=255)  # Gamertag o nombre
    
    # ===== Información del clan =====
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES
    )
    clan_rank = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Rango en el clan (1 = Líder, 2 = siguiente, etc.)"
    )
    previous_clan_rank = models.IntegerField(null=True, blank=True)
    
    # ===== Niveles =====
    town_hall_level = models.IntegerField()  # 1-18
    exp_level = models.IntegerField()        # Experiencia total
    
    # ===== Trofeos =====
    trophies = models.IntegerField(default=0)
    builder_base_trophies = models.IntegerField(default=0)
    
    # ===== Donaciones =====
    donations = models.IntegerField(default=0)
    donations_received = models.IntegerField(default=0)
    
    # ===== Información de Ligas (JSON para flexibilidad) =====
    league_info = models.JSONField(
        default=dict, 
        blank=True,
        help_text="{ 'id': 29000020, 'name': 'Titan League II', 'iconUrls': {...} }"
    )
    league_tier_info = models.JSONField(default=dict, blank=True)
    builder_base_league = models.JSONField(default=dict, blank=True)
    
    # ===== Casa del Jugador (Player House) =====
    player_house_elements = models.JSONField(
        default=list, 
        blank=True,
        help_text="Elementos decorativos de la casa del jugador"
    )
    
    # ===== Estado =====
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active'
    )
    joined_date = models.DateTimeField(null=True, blank=True)
    left_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('clan', 'player_tag')
        ordering = ['clan_rank']
        verbose_name = "Jugador"
        verbose_name_plural = "Jugadores"
        indexes = [
            models.Index(fields=['clan', 'status']),
            models.Index(fields=['clan', 'clan_rank']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.player_tag}) - {self.clan.clan_name}"
    
    def get_league_name(self):
        """Retorna el nombre de la liga actual"""
        if self.league_info:
            return self.league_info.get('name', 'Unranked')
        return 'Unranked'
    
    def get_league_tier_name(self):
        """Retorna el tier de la liga actual"""
        if self.league_tier_info:
            return self.league_tier_info.get('name', 'N/A')
        return 'N/A'