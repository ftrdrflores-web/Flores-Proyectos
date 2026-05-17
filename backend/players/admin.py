from django.contrib import admin
from .models import Player

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'player_tag', 'clan', 'role', 'town_hall_level', 'trophies', 'status']
    list_filter = ['status', 'role', 'town_hall_level', 'clan']
    search_fields = ['name', 'player_tag']
    readonly_fields = ['created_at', 'last_updated']