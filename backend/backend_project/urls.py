from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Admin de Django
    path('admin/', admin.site.urls),

    # ===== API v1 =====
    path('api/auth/', include('users.urls')),

    # Los siguientes se agregarán en cada fase:
    # path('api/clan/', include('users.urls_clan')),     # FASE 2
    # path('api/players/', include('players.urls')),     # FASE 3
    # path('api/wars/', include('wars.urls')),            # FASE 4
    # path('api/stats/', include('stats.urls')),          # FASE 5
]