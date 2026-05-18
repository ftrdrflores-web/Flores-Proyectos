from django.contrib.auth.models import User
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import UserProfile
from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    ClanUserListSerializer,
    UpdateUserRoleSerializer,
)
from .permissions import IsClanAdmin, IsSameClan, IsOwnerOrAdmin


# =====================================================
# VIEW: Login (JWT personalizado)
# =====================================================

class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    
    Body: { "username": "...", "password": "..." }
    
    Response: {
        "access": "eyJ...",
        "refresh": "eyJ...",
        "user": {
            "id": 1,
            "username": "omar",
            "email": "omar@example.com",
            "full_name": "Omar Flores",
            "role": "admin",
            "clan_id": 1,
            "clan_name": "FamiliaPerfecta",
            "clan_tag": "#2C29G2RJL",
            "player_tag": "#PYU89U08L"
        }
    }
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


# =====================================================
# VIEW: Registro de usuario
# =====================================================

class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    
    Body: {
        "username": "jugador1",
        "email": "jugador@gmail.com",
        "first_name": "Juan",
        "last_name": "García",
        "password": "mipassword123",
        "password_confirm": "mipassword123",
        "clan_tag": "#2C29G2RJL",
        "player_tag": "#ABC123"   (opcional)
    }
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generar tokens automáticamente al registrar
        refresh = RefreshToken.for_user(user)

        # Obtener datos del perfil creado
        try:
            profile = user.profile
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'role': profile.role,
                'clan_id': profile.clan.id,
                'clan_name': profile.clan.clan_name,
                'clan_tag': profile.clan.clan_tag,
                'player_tag': profile.player_tag,
            }
        except Exception:
            user_data = {'id': user.id, 'username': user.username}

        return Response({
            'message': '¡Cuenta creada exitosamente!',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user_data,
        }, status=status.HTTP_201_CREATED)


# =====================================================
# VIEW: Logout
# =====================================================

class LogoutView(APIView):
    """
    POST /api/auth/logout/
    
    Invalida el refresh token (blacklist).
    Body: { "refresh": "eyJ..." }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Se requiere el refresh token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {'message': 'Sesión cerrada exitosamente.'},
                status=status.HTTP_200_OK
            )
        except TokenError:
            return Response(
                {'error': 'Token inválido o ya expirado.'},
                status=status.HTTP_400_BAD_REQUEST
            )


# =====================================================
# VIEW: Mi perfil (usuario autenticado)
# =====================================================

class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/me/   → Ver mi perfil
    PUT  /api/auth/me/   → Actualizar mi perfil
    PATCH /api/auth/me/  → Actualizar parcialmente
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


# =====================================================
# VIEW: Cambiar contraseña
# =====================================================

class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    
    Body: {
        "old_password": "...",
        "new_password": "...",
        "new_password_confirm": "..."
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        # Cambiar contraseña
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Invalidar tokens existentes (forzar re-login)
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        return Response(
            {'message': 'Contraseña cambiada exitosamente. Por favor inicia sesión de nuevo.'},
            status=status.HTTP_200_OK
        )


# =====================================================
# VIEW: Gestión de usuarios del clan (solo admins)
# =====================================================

class ClanUsersView(generics.ListAPIView):
    """
    GET /api/auth/clan-users/
    
    Lista todos los usuarios del clan del admin autenticado.
    Solo accesible por admins.
    """
    serializer_class = ClanUserListSerializer
    permission_classes = [IsAuthenticated, IsClanAdmin]

    def get_queryset(self):
        clan = self.request.user.profile.clan
        return UserProfile.objects.filter(clan=clan).select_related('user').order_by('role', 'user__first_name')


class UpdateUserRoleView(generics.UpdateAPIView):
    """
    PATCH /api/auth/clan-users/{id}/role/
    
    Cambia el rol de un usuario del clan.
    Solo accesible por admins.
    
    Body: { "role": "admin" | "member" | "observer" }
    """
    serializer_class = UpdateUserRoleSerializer
    permission_classes = [IsAuthenticated, IsClanAdmin]

    def get_queryset(self):
        clan = self.request.user.profile.clan
        return UserProfile.objects.filter(clan=clan)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Un admin no puede quitarse a sí mismo el rol de admin
        if instance.user == request.user and request.data.get('role') != 'admin':
            return Response(
                {'error': 'No puedes quitarte el rol de administrador a ti mismo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': f'Rol actualizado a {instance.get_role_display()} exitosamente.',
            'user': instance.user.username,
            'new_role': instance.role,
        })


class DeactivateUserView(APIView):
    """
    POST /api/auth/clan-users/{id}/deactivate/
    
    Desactiva la cuenta de un usuario del clan.
    Solo accesible por admins.
    """
    permission_classes = [IsAuthenticated, IsClanAdmin]

    def post(self, request, pk):
        try:
            clan = request.user.profile.clan
            profile = UserProfile.objects.get(pk=pk, clan=clan)

            # No puede desactivarse a sí mismo
            if profile.user == request.user:
                return Response(
                    {'error': 'No puedes desactivar tu propia cuenta.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            profile.user.is_active = False
            profile.user.save()

            return Response({
                'message': f'Usuario {profile.user.username} desactivado exitosamente.'
            })

        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado en tu clan.'},
                status=status.HTTP_404_NOT_FOUND
            )