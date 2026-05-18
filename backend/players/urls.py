from django.urls import path
from .views import (
    PlayerListView,
    PlayerDetailView,
    PlayerDetailByTagView,
    PlayerRankingView,
    PlayerStatsView,
    PlayerMonthlyStatsView,
    PlayerCompareView,
)

urlpatterns = [
    # ===== Lista y detalle =====
    path('', PlayerListView.as_view(), name='player-list'),
    path('<int:pk>/', PlayerDetailView.as_view(), name='player-detail'),
    path('tag/<str:player_tag>/', PlayerDetailByTagView.as_view(), name='player-detail-by-tag'),

    # ===== Ranking =====
    path('ranking/', PlayerRankingView.as_view(), name='player-ranking'),

    # ===== Comparación =====
    path('compare/', PlayerCompareView.as_view(), name='player-compare'),

    # ===== Stats individuales =====
    path('<int:pk>/stats/', PlayerStatsView.as_view(), name='player-stats'),
    path('<int:pk>/monthly/', PlayerMonthlyStatsView.as_view(), name='player-monthly'),
]