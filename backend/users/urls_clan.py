from django.urls import path
from .views_clan import (
    MyClanView,
    ClanStatsView,
    ClanMembersView,
    ClanDashboardView,
)

urlpatterns = [
    # ===== Clan =====
    path('', MyClanView.as_view(), name='clan-detail'),
    path('stats/', ClanStatsView.as_view(), name='clan-stats'),
    path('members/', ClanMembersView.as_view(), name='clan-members'),
    path('dashboard/', ClanDashboardView.as_view(), name='clan-dashboard'),
]