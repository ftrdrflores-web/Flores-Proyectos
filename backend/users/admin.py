from django.contrib import admin
from .models import Clan, UserProfile

@admin.register(Clan)
class ClanAdmin(admin.ModelAdmin):
    list_display = ['clan_name', 'clan_tag', 'members_count', 'war_wins', 'war_losses', 'last_sync']
    search_fields = ['clan_name', 'clan_tag']
    readonly_fields = ['created_at', 'updated_at', 'last_sync']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'clan', 'role', 'player_tag']
    list_filter = ['role', 'clan']
    search_fields = ['user__username', 'player_tag']