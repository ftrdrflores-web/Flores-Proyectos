from django.db import models
from django.db.models import Avg, Count, Q
from users.models import Clan
from players.models import Player


# =====================================================
# MODELO 8: PlayerStats (Estadísticas agregadas)
# =====================================================

class PlayerStats(models.Model):
    """
    Estadísticas agregadas de un jugador para optimizar queries en dashboards.
    Se calcula periódicamente desde los datos de ataques y defensas.
    """
    
    # ===== Relaciones =====
    player = models.OneToOneField(
        Player,
        on_delete=models.CASCADE,
        related_name='stats'
    )
    clan = models.ForeignKey(
        Clan,
        on_delete=models.CASCADE,
        related_name='player_stats'
    )
    
    # ===== Estadísticas de Guerras =====
    total_wars = models.IntegerField(
        default=0,
        help_text="Total de guerras en las que ha participado"
    )
    wars_participated = models.IntegerField(
        default=0,
        help_text="Guerras donde atacó al menos una vez"
    )
    war_participation_rate = models.FloatField(
        default=0.0,
        help_text="Porcentaje de participación en guerras del clan"
    )
    
    # ===== Estadísticas de Ataques =====
    total_attacks = models.IntegerField(default=0)
    avg_stars_per_attack = models.FloatField(default=0.0)
    avg_destruction_per_attack = models.FloatField(default=0.0)
    perfect_attacks = models.IntegerField(
        default=0,
        help_text="Ataques de 3 estrellas + 100% destrucción"
    )
    
    # ===== Estadísticas de Defensas =====
    total_defenses = models.IntegerField(default=0)
    avg_stars_lost = models.FloatField(default=0.0)
    avg_destruction_suffered = models.FloatField(default=0.0)
    defensive_efficiency = models.FloatField(
        default=0.0,
        help_text="Porcentaje - qué tan bien se defiende"
    )
    successful_defenses = models.IntegerField(default=0)
    
    # ===== Estadísticas de Donaciones =====
    total_donations = models.IntegerField(default=0)
    total_donations_received = models.IntegerField(default=0)
    donation_balance = models.IntegerField(default=0)  # donaciones - recibidas
    
    # ===== Rankings =====
    current_rank = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Ranking basado en estrellas totales"
    )
    
    # ===== Timestamps =====
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Estadística de Jugador"
        verbose_name_plural = "Estadísticas de Jugadores"
        indexes = [
            models.Index(fields=['clan', '-total_attacks']),
            models.Index(fields=['clan', '-current_rank']),
        ]
    
    def __str__(self):
        return f"Stats: {self.player.name}"
    
    def get_overall_rating(self):
        """Califica el desempeño general del jugador"""
        if self.total_attacks == 0:
            return "Sin datos"
        
        score = (
            self.avg_stars_per_attack * 1.0 +  # max 3
            (self.avg_destruction_per_attack / 33.33) +  # max 100/33.33 = ~3
            (self.perfect_attacks / max(self.total_attacks / 10, 1))  # max 3
        ) / 3
        
        if score >= 2.5:
            return "Excelente"
        elif score >= 2.0:
            return "Muy Bueno"
        elif score >= 1.5:
            return "Bueno"
        elif score >= 1.0:
            return "Regular"
        else:
            return "Necesita mejorar"


# =====================================================
# MODELO 9: WarLog (Histórico de guerras)
# =====================================================

class WarLog(models.Model):
    """
    Histórico agregado de guerras por período de tiempo.
    Útil para gráficas de tendencia y análisis histórico.
    """
    
    # ===== Relaciones =====
    clan = models.ForeignKey(
        Clan,
        on_delete=models.CASCADE,
        related_name='war_logs'
    )
    
    # ===== Período =====
    war_date = models.DateField(
        help_text="Fecha de la guerra"
    )
    
    # ===== Resultados =====
    total_wars_this_period = models.IntegerField(
        default=0,
        help_text="Total de guerras en este período"
    )
    total_wins = models.IntegerField(default=0)
    total_losses = models.IntegerField(default=0)
    total_ties = models.IntegerField(default=0)
    
    # ===== Agregados =====
    avg_stars = models.FloatField(
        default=0.0,
        help_text="Promedio de estrellas obtenidas"
    )
    avg_destruction = models.FloatField(
        default=0.0,
        help_text="Promedio de destrucción lograda"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('clan', 'war_date')
        ordering = ['-war_date']
        verbose_name = "Registro de Guerra"
        verbose_name_plural = "Registros de Guerras"
    
    def __str__(self):
        return f"{self.clan.clan_name} - {self.war_date}: {self.total_wins}W-{self.total_losses}L-{self.total_ties}T"
    
    def get_win_rate(self):
        """Calcula el porcentaje de victorias"""
        total = self.total_wars_this_period
        if total == 0:
            return 0
        return (self.total_wins / total) * 100


# =====================================================
# MODELO 10: ClanStats (Estadísticas del clan)
# =====================================================

class ClanStats(models.Model):
    """
    Estadísticas agregadas del clan para dashboards generales.
    """
    
    # ===== Relaciones =====
    clan = models.OneToOneField(
        Clan,
        on_delete=models.CASCADE,
        related_name='clan_stats'
    )
    
    # ===== Estadísticas Generales =====
    total_wars = models.IntegerField(default=0)
    total_wins = models.IntegerField(default=0)
    total_losses = models.IntegerField(default=0)
    total_ties = models.IntegerField(default=0)
    
    win_rate = models.FloatField(
        default=0.0,
        help_text="Porcentaje de victorias"
    )
    
    # ===== Desempeño General =====
    avg_stars_per_war = models.FloatField(default=0.0)
    avg_destruction_per_war = models.FloatField(default=0.0)
    
    # ===== Participación =====
    active_players_this_war = models.IntegerField(
        default=0,
        help_text="Jugadores activos en la guerra actual"
    )
    avg_participation_rate = models.FloatField(
        default=0.0,
        help_text="Promedio de participación de todos"
    )
    
    # ===== Top performers =====
    best_attacker_tag = models.CharField(max_length=20, blank=True)
    best_attacker_name = models.CharField(max_length=255, blank=True)
    best_attacker_stars = models.IntegerField(default=0)
    
    best_defender_tag = models.CharField(max_length=20, blank=True)
    best_defender_name = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Estadística de Clan"
        verbose_name_plural = "Estadísticas de Clan"
    
    def __str__(self):
        return f"Stats: {self.clan.clan_name}"
    
    def get_win_rate_display(self):
        """Retorna el porcentaje con formato"""
        return f"{self.win_rate:.1f}%"


# =====================================================
# MODELO 11: PlayerMonthlyStats (Estadísticas mensuales)
# =====================================================

class PlayerMonthlyStats(models.Model):
    """
    Estadísticas mensuales de un jugador para análisis de tendencias.
    """
    
    # ===== Relaciones =====
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='monthly_stats'
    )
    clan = models.ForeignKey(
        Clan,
        on_delete=models.CASCADE,
        related_name='player_monthly_stats'
    )
    
    # ===== Período =====
    year = models.IntegerField()
    month = models.IntegerField()  # 1-12
    
    # ===== Estadísticas del mes =====
    total_attacks = models.IntegerField(default=0)
    total_stars = models.IntegerField(default=0)
    avg_destruction = models.FloatField(default=0.0)
    perfect_attacks = models.IntegerField(default=0)
    
    total_donations = models.IntegerField(default=0)
    total_donations_received = models.IntegerField(default=0)
    
    # ===== Cambios =====
    trophy_change = models.IntegerField(default=0)
    town_hall_change = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('player', 'year', 'month')
        ordering = ['-year', '-month']
        verbose_name = "Estadística Mensual de Jugador"
        verbose_name_plural = "Estadísticas Mensuales de Jugadores"
    
    def __str__(self):
        return f"{self.player.name} - {self.year}/{self.month}"