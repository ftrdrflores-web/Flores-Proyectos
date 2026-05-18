from rest_framework import serializers
from .models import PlayerStats, ClanStats, WarLog, PlayerMonthlyStats


# =====================================================
# SERIALIZER: ClanStats
# =====================================================

class ClanStatsSerializer(serializers.ModelSerializer):
    win_rate_display = serializers.SerializerMethodField()
    clan_name = serializers.CharField(source='clan.clan_name', read_only=True)
    clan_tag = serializers.CharField(source='clan.clan_tag', read_only=True)

    class Meta:
        model = ClanStats
        fields = [
            'clan_tag',
            'clan_name',
            'total_wars',
            'total_wins',
            'total_losses',
            'total_ties',
            'win_rate',
            'win_rate_display',
            'avg_stars_per_war',
            'avg_destruction_per_war',
            'active_players_this_war',
            'avg_participation_rate',
            'best_attacker_tag',
            'best_attacker_name',
            'best_attacker_stars',
            'calculated_at',
        ]

    def get_win_rate_display(self, obj):
        return obj.get_win_rate_display()


# =====================================================
# SERIALIZER: PlayerStats
# =====================================================

class PlayerStatsSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.name', read_only=True)
    player_tag = serializers.CharField(source='player.player_tag', read_only=True)
    town_hall_level = serializers.IntegerField(source='player.town_hall_level', read_only=True)
    overall_rating = serializers.SerializerMethodField()
    perfect_attack_rate = serializers.SerializerMethodField()

    class Meta:
        model = PlayerStats
        fields = [
            'player_tag',
            'player_name',
            'town_hall_level',
            'total_wars',
            'wars_participated',
            'war_participation_rate',
            'total_attacks',
            'avg_stars_per_attack',
            'avg_destruction_per_attack',
            'perfect_attacks',
            'perfect_attack_rate',
            'total_defenses',
            'avg_stars_lost',
            'avg_destruction_suffered',
            'defensive_efficiency',
            'successful_defenses',
            'total_donations',
            'total_donations_received',
            'donation_balance',
            'current_rank',
            'overall_rating',
            'calculated_at',
        ]

    def get_overall_rating(self, obj):
        return obj.get_overall_rating()

    def get_perfect_attack_rate(self, obj):
        if obj.total_attacks == 0:
            return 0.0
        return round((obj.perfect_attacks / obj.total_attacks) * 100, 1)


# =====================================================
# SERIALIZER: WarLog
# =====================================================

class WarLogSerializer(serializers.ModelSerializer):
    win_rate = serializers.SerializerMethodField()
    month_label = serializers.SerializerMethodField()

    class Meta:
        model = WarLog
        fields = [
            'id',
            'war_date',
            'month_label',
            'total_wars_this_period',
            'total_wins',
            'total_losses',
            'total_ties',
            'win_rate',
            'avg_stars',
            'avg_destruction',
        ]

    def get_win_rate(self, obj):
        return round(obj.get_win_rate(), 1)

    def get_month_label(self, obj):
        months = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        return f"{months.get(obj.war_date.month, '')} {obj.war_date.year}"


# =====================================================
# SERIALIZER: PlayerMonthlyStats
# =====================================================

class PlayerMonthlyStatsSerializer(serializers.ModelSerializer):
    month_label = serializers.SerializerMethodField()
    avg_stars = serializers.SerializerMethodField()

    class Meta:
        model = PlayerMonthlyStats
        fields = [
            'year',
            'month',
            'month_label',
            'total_attacks',
            'total_stars',
            'avg_stars',
            'avg_destruction',
            'perfect_attacks',
            'total_donations',
            'total_donations_received',
            'trophy_change',
            'town_hall_change',
        ]

    def get_month_label(self, obj):
        months = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        return f"{months.get(obj.month, '')} {obj.year}"

    def get_avg_stars(self, obj):
        if obj.total_attacks == 0:
            return 0.0
        return round(obj.total_stars / obj.total_attacks, 2)