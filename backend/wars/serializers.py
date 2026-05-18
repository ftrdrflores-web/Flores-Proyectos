from rest_framework import serializers
from .models import War, WarParticipant, Attack, Defense


# =====================================================
# SERIALIZER: War (lista - resumen)
# =====================================================

class WarListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para historial de guerras.
    """
    result_display = serializers.SerializerMethodField()
    duration_hours = serializers.SerializerMethodField()
    stars_difference = serializers.SerializerMethodField()

    class Meta:
        model = War
        fields = [
            'id',
            'war_id',
            'state',
            'opponent_name',
            'opponent_tag',
            'opponent_clan_level',
            'team_size',
            'clan_stars',
            'opponent_stars',
            'stars_difference',
            'clan_destruction_percentage',
            'opponent_destruction_percentage',
            'result',
            'result_display',
            'is_league_war',
            'start_time',
            'end_time',
            'duration_hours',
        ]

    def get_result_display(self, obj):
        labels = {
            'win': 'Victoria',
            'loss': 'Derrota',
            'tie': 'Empate',
        }
        return labels.get(obj.result, '⏳ En progreso')

    def get_duration_hours(self, obj):
        if obj.start_time and obj.end_time:
            delta = obj.end_time - obj.start_time
            return round(delta.total_seconds() / 3600, 1)
        return None

    def get_stars_difference(self, obj):
        return obj.clan_stars - obj.opponent_stars


# =====================================================
# SERIALIZER: Attack
# =====================================================

class AttackSerializer(serializers.ModelSerializer):
    """
    Serializer para ataques individuales.
    """
    is_perfect = serializers.SerializerMethodField()

    class Meta:
        model = Attack
        fields = [
            'id',
            'attacker_tag',
            'attacker_name',
            'defender_tag',
            'defender_name',
            'defender_position',
            'stars',
            'destruction_percentage',
            'duration',
            'order',
            'is_perfect',
        ]

    def get_is_perfect(self, obj):
        return obj.is_perfect()


# =====================================================
# SERIALIZER: Defense
# =====================================================

class DefenseSerializer(serializers.ModelSerializer):
    """
    Serializer para defensas sufridas.
    """
    defense_rating = serializers.SerializerMethodField()
    player_name = serializers.CharField(source='player.name', read_only=True)
    player_tag = serializers.CharField(source='player.player_tag', read_only=True)

    class Meta:
        model = Defense
        fields = [
            'id',
            'player_tag',
            'player_name',
            'times_attacked',
            'stars_received',
            'destruction_received',
            'successful_defenses',
            'defense_rating',
        ]

    def get_defense_rating(self, obj):
        return obj.get_defense_rating()


# =====================================================
# SERIALIZER: WarParticipant
# =====================================================

class WarParticipantSerializer(serializers.ModelSerializer):
    """
    Serializer para participantes en una guerra con sus ataques.
    """
    player_name = serializers.CharField(source='player.name', read_only=True)
    player_tag = serializers.CharField(source='player.player_tag', read_only=True)
    town_hall_level = serializers.IntegerField(read_only=True)
    attacks = AttackSerializer(many=True, read_only=True)
    attack_status = serializers.SerializerMethodField()

    class Meta:
        model = WarParticipant
        fields = [
            'id',
            'player_tag',
            'player_name',
            'map_position',
            'town_hall_level',
            'attacks_used',
            'total_stars',
            'total_destruction_percentage',
            'opponent_attacks',
            'attack_status',
            'attacks',
        ]

    def get_attack_status(self, obj):
        return obj.get_attack_status()


# =====================================================
# SERIALIZER: War (detalle completo)
# =====================================================

class WarDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el detalle de una guerra.
    Incluye participantes y ataques.
    """
    result_display = serializers.SerializerMethodField()
    stars_difference = serializers.SerializerMethodField()
    participants = WarParticipantSerializer(many=True, read_only=True)
    attack_efficiency = serializers.SerializerMethodField()
    state_label = serializers.SerializerMethodField()

    class Meta:
        model = War
        fields = [
            'id',
            'war_id',
            'state',
            'state_label',
            'clan_tag',
            'clan_name',
            'opponent_tag',
            'opponent_name',
            'opponent_clan_level',
            'team_size',
            'attacks_per_member',
            'battle_modifier',
            'preparation_start_time',
            'start_time',
            'end_time',
            'clan_attacks',
            'clan_stars',
            'clan_destruction_percentage',
            'clan_exp_earned',
            'opponent_stars',
            'opponent_destruction_percentage',
            'stars_difference',
            'result',
            'result_display',
            'attack_efficiency',
            'is_league_war',
            'participants',
        ]

    def get_result_display(self, obj):
        labels = {
            'win': 'Victoria',
            'loss': 'Derrota',
            'tie': 'Empate',
        }
        return labels.get(obj.result, '⏳ En progreso')

    def get_stars_difference(self, obj):
        return obj.clan_stars - obj.opponent_stars

    def get_state_label(self, obj):
        labels = {
            'preparation': 'En Preparación',
            'inWar': 'Guerra en Progreso',
            'warEnded': 'Guerra Terminada',
        }
        return labels.get(obj.state, obj.state)

    def get_attack_efficiency(self, obj):
        """Porcentaje de ataques usados vs disponibles"""
        available = obj.team_size * obj.attacks_per_member
        if available == 0:
            return 0
        return round((obj.clan_attacks / available) * 100, 1)


# =====================================================
# SERIALIZER: Guerra actual (simplificado para dashboard)
# =====================================================

class CurrentWarSerializer(serializers.ModelSerializer):
    """
    Serializer para la guerra actual con datos en tiempo real.
    Incluye quién NO ha atacado (útil para líderes).
    """
    state_label = serializers.SerializerMethodField()
    attacks_remaining = serializers.SerializerMethodField()
    attack_efficiency = serializers.SerializerMethodField()
    pending_attackers = serializers.SerializerMethodField()
    participants = WarParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = War
        fields = [
            'id',
            'state',
            'state_label',
            'opponent_name',
            'opponent_tag',
            'opponent_clan_level',
            'team_size',
            'attacks_per_member',
            'clan_stars',
            'opponent_stars',
            'clan_destruction_percentage',
            'opponent_destruction_percentage',
            'start_time',
            'end_time',
            'clan_attacks',
            'attacks_remaining',
            'attack_efficiency',
            'is_league_war',
            'pending_attackers',
            'participants',
        ]

    def get_state_label(self, obj):
        labels = {
            'preparation': 'En Preparación',
            'inWar': 'Guerra en Progreso',
            'warEnded': 'Guerra Terminada',
        }
        return labels.get(obj.state, obj.state)

    def get_attacks_remaining(self, obj):
        available = obj.team_size * obj.attacks_per_member
        return available - obj.clan_attacks

    def get_attack_efficiency(self, obj):
        available = obj.team_size * obj.attacks_per_member
        if available == 0:
            return 0
        return round((obj.clan_attacks / available) * 100, 1)

    def get_pending_attackers(self, obj):
        """Lista de jugadores que NO han usado todos sus ataques."""
        pending = []
        participants = obj.participants.filter(
            attacks_used__lt=obj.attacks_per_member
        ).select_related('player').order_by('map_position')

        for p in participants:
            pending.append({
                'player_tag': p.player.player_tag,
                'name': p.player.name,
                'map_position': p.map_position,
                'town_hall_level': p.town_hall_level,
                'attacks_used': p.attacks_used,
                'attacks_remaining': obj.attacks_per_member - p.attacks_used,
            })
        return pending