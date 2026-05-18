from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    RegisterView,
    LogoutView,
    MeView,
    ChangePasswordView,
    ClanUsersView,
    UpdateUserRoleView,
    DeactivateUserView,
)

urlpatterns = [
    # ===== Autenticación =====
    path('login/', LoginView.as_view(), name='auth-login'),
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('refresh/', TokenRefreshView.as_view(), name='auth-refresh'),

    # ===== Perfil propio =====
    path('me/', MeView.as_view(), name='auth-me'),
    path('change-password/', ChangePasswordView.as_view(), name='auth-change-password'),

    # ===== Gestión de usuarios del clan (solo admins) =====
    path('clan-users/', ClanUsersView.as_view(), name='clan-users-list'),
    path('clan-users/<int:pk>/role/', UpdateUserRoleView.as_view(), name='clan-users-role'),
    path('clan-users/<int:pk>/deactivate/', DeactivateUserView.as_view(), name='clan-users-deactivate'),
]