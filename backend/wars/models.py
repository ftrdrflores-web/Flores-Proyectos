from django.db import models
from django.utils import timezone
from users.models import Clan
from players.models import Player


# =====================================================
# MODELO 4: War (Guerra)
# =====================================================

class War(models.Model):
    """
    Representa una guerra de clan.
    Contiene información general de la guerra y datos agregados.
    """
    
    RESULT_CHOICES = [
        ('win', 'Victoria'),
        ('loss', 'Derrota'),
        ('tie', 'Empate'),
    ]
    
    STATE_CHOICES = [
        ('preparation', 'Preparación'),
        ('inWar', 'En Guerra'),
        ('warEnded', 'Terminada'),
    ]
    
    # ===== Identificadores =====
    clan = models.ForeignKey(
        Clan,
        on_delete=models.CASCADE,
        related_name='wars'
    )
    war_id = models.CharField(
        max_length=100, 
        unique=True,
        help_text="ID único de la guerra en Clash"
    )
    state = models.CharField(
        max_length=20, 
        choices=STATE_CHOICES
    )
    
    # ===== Información del clan =====
    clan_tag = models.CharField(max_length=10)
    clan_name = models.CharField(max_length=255)
    
    # ===== Información del enemigo =====
    opponent_tag = models.CharField(max_length=10)
    opponent_name = models.CharField(max_length=255)
    opponent_clan_level = models.IntegerField(default=0)
    
    # ===== Configuración de la guerra =====
    team_size = models.IntegerField()  # 5, 10, 15, 20, 25, 30, 35, 40, 50
    attacks_per_member = models.IntegerField()  # 1 o 2
    battle_modifier = models.CharField(
        max_length=50, 
        default='none',
        help_text="none, quartermaster, etc."
    )
    
    # ===== Timestamps de la guerra =====
    preparation_start_time = models.DateTimeField(null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    # ===== Resultados del clan =====
    clan_attacks = models.IntegerField(default=0)
    clan_stars = models.IntegerField(default=0)
    clan_destruction_percentage = models.FloatField(default=0.0)
    clan_exp_earned = models.IntegerField(default=0)
    
    # ===== Resultados del enemigo =====
    opponent_stars = models.IntegerField(default=0)
    opponent_destruction_percentage = models.FloatField(default=0.0)
    
    # ===== Resultado final =====
    result = models.CharField(
        max_length=10, 
        choices=RESULT_CHOICES, 
        null=True, 
        blank=True,
        help_text="Se calcula al finalizar la guerra"
    )
    
    # ===== Flags =====
    is_league_war = models.BooleanField(
        default=False,
        help_text="¿Es una guerra de liga de guerra?"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-end_time']
        verbose_name = "Guerra"
        verbose_name_plural = "Guerras"
        indexes = [
            models.Index(fields=['clan', '-end_time']),
            models.Index(fields=['state']),
        ]
    
    def __str__(self):
        return f"{self.clan_name} vs {self.opponent_name} ({self.start_time.strftime('%Y-%m-%d')})"
    
    def is_finished(self):
        """Verifica si la guerra ha terminado"""
        return self.state == 'warEnded' or timezone.now() > self.end_time
    
    def get_result_display_with_stars(self):
        """Retorna un resumen del resultado"""
        if self.result == 'win':
            return f"✓ Victoria ({self.clan_stars}-{self.opponent_stars})"
        elif self.result == 'loss':
            return f"✗ Derrota ({self.clan_stars}-{self.opponent_stars})"
        else:
            return f"= Empate ({self.clan_stars}-{self.opponent_stars})"


# =====================================================
# MODELO 5: WarParticipant (Participación en guerra)
# =====================================================

class WarParticipant(models.Model):
    """
    Representa la participación de un jugador en una guerra.
    Conecta un jugador con una guerra específica.
    """
    
    # ===== Relaciones =====
    war = models.ForeignKey(
        War,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='war_participations'
    )
    
    # ===== Información del participante =====
    map_position = models.IntegerField(
        help_text="Posición en el mapa (1-50)"
    )
    town_hall_level = models.IntegerField()
    
    # ===== Ataques realizados =====
    attacks_used = models.IntegerField(
        default=0,
        help_text="0, 1, o 2 ataques"
    )
    total_stars = models.IntegerField(default=0)
    total_destruction_percentage = models.FloatField(default=0.0)
    
    # ===== Defensas sufridas =====
    opponent_attacks = models.IntegerField(
        default=0,
        help_text="Cuántas veces fue atacado este jugador"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('war', 'player')
        ordering = ['map_position']
        verbose_name = "Participante en Guerra"
        verbose_name_plural = "Participantes en Guerras"
    
    def __str__(self):
        return f"{self.player.name} en {self.war} (Pos: {self.map_position})"
    
    def get_attack_status(self):
        """Retorna el estado de ataques"""
        max_attacks = self.war.attacks_per_member
        if self.attacks_used >= max_attacks:
            return f"✓ Completado ({self.attacks_used}/{max_attacks})"
        else:
            return f"⏳ En progreso ({self.attacks_used}/{max_attacks})"


# =====================================================
# MODELO 6: Attack (Ataque individual)
# =====================================================

class Attack(models.Model):
    """
    Representa un ataque individual en una guerra.
    Cada participante puede tener hasta 2 ataques.
    """
    
    # ===== Relaciones =====
    war = models.ForeignKey(
        War,
        on_delete=models.CASCADE,
        related_name='attacks'
    )
    war_participant = models.ForeignKey(
        WarParticipant,
        on_delete=models.CASCADE,
        related_name='attacks'
    )
    
    # ===== Información del atacante =====
    attacker_tag = models.CharField(max_length=20)
    attacker_name = models.CharField(max_length=255)
    
    # ===== Información del defensor =====
    defender_tag = models.CharField(max_length=20)
    defender_name = models.CharField(max_length=255, blank=True)
    defender_position = models.IntegerField()
    
    # ===== Resultados del ataque =====
    stars = models.IntegerField(
        choices=[(0, '0 estrellas'), (1, '1 estrella'), (2, '2 estrellas'), (3, '3 estrellas')]
    )
    destruction_percentage = models.FloatField()
    
    # ===== Información de orden =====
    order = models.IntegerField(
        help_text="Orden en el que se realizó el ataque en la guerra"
    )
    duration = models.IntegerField(
        help_text="Duración del ataque en segundos"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Ataque"
        verbose_name_plural = "Ataques"
        indexes = [
            models.Index(fields=['war', 'order']),
            models.Index(fields=['attacker_tag']),
        ]
    
    def __str__(self):
        return f"{self.attacker_name} → {self.defender_name} ({self.stars}⭐)"
    
    def is_perfect(self):
        """¿Fue un ataque perfecto? (3 estrellas + 100% destrucción)"""
        return self.stars == 3 and self.destruction_percentage == 100.0


# =====================================================
# MODELO 7: Defense (Defensas sufridas)
# =====================================================

class Defense(models.Model):
    """
    Representa las defensas sufridas por un jugador en una guerra.
    Se calcula agregando datos de los ataques recibidos.
    """
    
    # ===== Relaciones =====
    war = models.ForeignKey(
        War,
        on_delete=models.CASCADE,
        related_name='defenses'
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='defenses'
    )
    
    # ===== Estadísticas de defensa =====
    times_attacked = models.IntegerField(
        default=0,
        help_text="Cuántas veces fue atacado"
    )
    stars_received = models.IntegerField(
        default=0,
        help_text="Total de estrellas recibidas"
    )
    destruction_received = models.FloatField(
        default=0.0,
        help_text="Promedio de destrucción recibida"
    )
    successful_defenses = models.IntegerField(
        default=0,
        help_text="Ataques defendidos con éxito (0 estrellas)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('war', 'player')
        verbose_name = "Defensa"
        verbose_name_plural = "Defensas"
    
    def __str__(self):
        return f"{self.player.name} - Ataques recibidos: {self.times_attacked}"
    
    def get_defense_rating(self):
        """Calcula una calificación de defensa"""
        if self.times_attacked == 0:
            return "N/A"
        avg_stars_per_attack = self.stars_received / self.times_attacked
        if avg_stars_per_attack < 1:
            return "Excelente"
        elif avg_stars_per_attack < 2:
            return "Buena"
        elif avg_stars_per_attack < 3:
            return "Regular"
        else:
            return "Débil"