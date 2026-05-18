from django.urls import path
from .views import (
    StatsDashboardView,
    StatsLeaderboardView,
    StatsTrendsView,
    StatsPlayerCompareView,
    StatsWarLogView,
    StatsPlayerView,
)

urlpatterns = [
    # ===== Dashboard y KPIs =====
    path('dashboard/', StatsDashboardView.as_view(), name='stats-dashboard'),
    path('leaderboard/', StatsLeaderboardView.as_view(), name='stats-leaderboard'),

    # ===== Tendencias =====
    path('trends/', StatsTrendsView.as_view(), name='stats-trends'),
    path('war-log/', StatsWarLogView.as_view(), name='stats-war-log'),

    # ===== Jugadores =====
    path('player/<str:player_tag>/', StatsPlayerView.as_view(), name='stats-player'),
    path('compare/', StatsPlayerCompareView.as_view(), name='stats-compare'),
]