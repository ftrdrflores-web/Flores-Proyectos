from django.urls import path
from .views import (
    WarListView,
    WarDetailView,
    CurrentWarView,
    WarAttacksView,
    WarDefensesView,
    WarPerformanceView,
    PlayerWarHistoryView,
)

urlpatterns = [
    # ===== Historial =====
    path('', WarListView.as_view(), name='war-list'),
    path('<int:pk>/', WarDetailView.as_view(), name='war-detail'),

    # ===== Guerra actual =====
    path('current/', CurrentWarView.as_view(), name='war-current'),

    # ===== Detalle de guerra =====
    path('<int:pk>/attacks/', WarAttacksView.as_view(), name='war-attacks'),
    path('<int:pk>/defenses/', WarDefensesView.as_view(), name='war-defenses'),
    path('<int:pk>/performance/', WarPerformanceView.as_view(), name='war-performance'),

    # ===== Historial por jugador =====
    path('player/<str:player_tag>/history/', PlayerWarHistoryView.as_view(), name='player-war-history'),
]