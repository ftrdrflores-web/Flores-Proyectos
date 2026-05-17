from django.contrib import admin
from .models import War, WarParticipant, Attack, Defense

@admin.register(War)
class WarAdmin(admin.ModelAdmin):
    list_display = ['clan', 'opponent_name', 'result', 'team_size', 'clan_stars', 'opponent_stars', 'end_time']
    list_filter = ['result', 'state', 'clan']
    search_fields = ['opponent_name', 'opponent_tag']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(WarParticipant)
class WarParticipantAdmin(admin.ModelAdmin):
    list_display = ['player', 'war', 'map_position', 'attacks_used', 'total_stars']
    list_filter = ['war__clan']
    search_fields = ['player__name']

@admin.register(Attack)
class AttackAdmin(admin.ModelAdmin):
    list_display = ['attacker_name', 'defender_name', 'stars', 'destruction_percentage', 'order']
    list_filter = ['stars']
    search_fields = ['attacker_name', 'defender_name']

@admin.register(Defense)
class DefenseAdmin(admin.ModelAdmin):
    list_display = ['player', 'war', 'times_attacked', 'stars_received']
    search_fields = ['player__name']