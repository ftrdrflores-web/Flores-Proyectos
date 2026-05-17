from django.contrib import admin
from .models import PlayerStats, ClanStats, WarLog, PlayerMonthlyStats

@admin.register(PlayerStats)
class PlayerStatsAdmin(admin.ModelAdmin):
    list_display = ['player', 'total_attacks', 'avg_stars_per_attack', 'war_participation_rate', 'current_rank']
    list_filter = ['clan']
    search_fields = ['player__name']

@admin.register(ClanStats)
class ClanStatsAdmin(admin.ModelAdmin):
    list_display = ['clan', 'total_wars', 'win_rate', 'avg_stars_per_war']
    search_fields = ['clan__clan_name']

@admin.register(WarLog)
class WarLogAdmin(admin.ModelAdmin):
    list_display = ['clan', 'war_date', 'total_wins', 'total_losses', 'total_ties']
    list_filter = ['clan']

@admin.register(PlayerMonthlyStats)
class PlayerMonthlyStatsAdmin(admin.ModelAdmin):
    list_display = ['player', 'year', 'month', 'total_attacks', 'total_stars']
    list_filter = ['year', 'month', 'clan']
    search_fields = ['player__name']