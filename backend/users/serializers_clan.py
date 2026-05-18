from rest_framework import serializers
from .models import Clan, UserProfile


# =====================================================
# SERIALIZER: Clan (detalle completo)
# =====================================================

class ClanSerializer(serializers.ModelSerializer):
    """
    Serializer completo del clan para admins y líderes.
    """
    win_rate = serializers.SerializerMethodField()
    total_wars = serializers.SerializerMethodField()
    admin_username = serializers.CharField(source='admin_user.username', read_only=True)

    class Meta:
        model = Clan
        fields = [
            'id',
            'clan_tag',
            'clan_name',
            'description',
            'badge_url',
            'clan_level',
            'clan_points',
            'clan_capital_points',
            'members_count',
            'required_trophies',
            'war_frequency',
            'is_war_log_public',
            'war_wins',
            'war_losses',
            'war_ties',
            'war_win_streak',
            'win_rate',
            'total_wars',
            'admin_username',
            'last_sync',
            'next_sync_scheduled',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'clan_tag', 'clan_level', 'clan_points', 'members_count',
            'war_wins', 'war_losses', 'war_ties', 'war_win_streak',
            'last_sync', 'next_sync_scheduled', 'created_at', 'updated_at',
        ]

    def get_win_rate(self, obj):
        total = obj.war_wins + obj.war_losses + obj.war_ties
        if total == 0:
            return 0.0
        return round((obj.war_wins / total) * 100, 1)

    def get_total_wars(self, obj):
        return obj.war_wins + obj.war_losses + obj.war_ties


# =====================================================
# SERIALIZER: Clan (resumen público para members)
# =====================================================

class ClanPublicSerializer(serializers.ModelSerializer):
    """
    Serializer reducido del clan para members y observers.
    No expone datos sensibles de configuración.
    """
    win_rate = serializers.SerializerMethodField()
    total_wars = serializers.SerializerMethodField()

    class Meta:
        model = Clan
        fields = [
            'id',
            'clan_tag',
            'clan_name',
            'description',
            'badge_url',
            'clan_level',
            'clan_points',
            'members_count',
            'war_wins',
            'war_losses',
            'war_ties',
            'war_win_streak',
            'win_rate',
            'total_wars',
            'last_sync',
        ]

    def get_win_rate(self, obj):
        total = obj.war_wins + obj.war_losses + obj.war_ties
        if total == 0:
            return 0.0
        return round((obj.war_wins / total) * 100, 1)

    def get_total_wars(self, obj):
        return obj.war_wins + obj.war_losses + obj.war_ties


# =====================================================
# SERIALIZER: Clan (update - solo campos editables)
# =====================================================

class ClanUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar configuración del clan.
    Solo el admin puede usar esto.
    """

    class Meta:
        model = Clan
        fields = [
            'description',
            'war_frequency',
            'sync_interval',
        ]