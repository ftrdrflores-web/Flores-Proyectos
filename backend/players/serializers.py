from rest_framework import serializers
from .models import Player


# =====================================================
# SERIALIZER: Player (lista - datos resumidos)
# =====================================================

class PlayerListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listas de jugadores.
    Usado en: lista de miembros del clan, rankings.
    """
    league_name = serializers.SerializerMethodField()
    overall_rating = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            'id',
            'player_tag',
            'name',
            'role',
            'clan_rank',
            'town_hall_level',
            'exp_level',
            'trophies',
            'donations',
            'donations_received',
            'league_name',
            'status',
            'overall_rating',
        ]

    def get_league_name(self, obj):
        return obj.get_league_name()

    def get_overall_rating(self, obj):
        try:
            return obj.stats.get_overall_rating()
        except Exception:
            return 'Sin datos'


# =====================================================
# SERIALIZER: Player (detalle completo)
# =====================================================

class PlayerDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el detalle de un jugador.
    Incluye stats si existen.
    """
    league_name = serializers.SerializerMethodField()
    league_tier_name = serializers.SerializerMethodField()
    overall_rating = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            'id',
            'player_tag',
            'name',
            'role',
            'clan_rank',
            'previous_clan_rank',
            'town_hall_level',
            'exp_level',
            'trophies',
            'builder_base_trophies',
            'donations',
            'donations_received',
            'league_name',
            'league_tier_name',
            'league_info',
            'builder_base_league',
            'status',
            'joined_date',
            'overall_rating',
            'stats',
            'last_updated',
        ]

    def get_league_name(self, obj):
        return obj.get_league_name()

    def get_league_tier_name(self, obj):
        return obj.get_league_tier_name()

    def get_overall_rating(self, obj):
        try:
            return obj.stats.get_overall_rating()
        except Exception:
            return 'Sin datos'

    def get_stats(self, obj):
        try:
            s = obj.stats
            return {
                'total_wars': s.total_wars,
                'wars_participated': s.wars_participated,
                'war_participation_rate': s.war_participation_rate,
                'total_attacks': s.total_attacks,
                'avg_stars_per_attack': s.avg_stars_per_attack,
                'avg_destruction_per_attack': s.avg_destruction_per_attack,
                'perfect_attacks': s.perfect_attacks,
                'total_defenses': s.total_defenses,
                'avg_stars_lost': s.avg_stars_lost,
                'defensive_efficiency': s.defensive_efficiency,
                'total_donations': s.total_donations,
                'donation_balance': s.donation_balance,
                'current_rank': s.current_rank,
                'calculated_at': s.calculated_at,
            }
        except Exception:
            return None