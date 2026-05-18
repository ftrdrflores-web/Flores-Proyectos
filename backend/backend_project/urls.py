from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Admin de Django
    path('admin/', admin.site.urls),

    # ===== API v1 =====
    path('api/auth/', include('users.urls')),
    path('api/clan/', include('users.urls_clan')),
    path('api/players/', include('players.urls')),
    path('api/wars/', include('wars.urls')),
    path('api/stats/', include('stats.urls')),     
]