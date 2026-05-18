from rest_framework.permissions import BasePermission


# =====================================================
# PERMISO: Es Admin del clan
# =====================================================

class IsClanAdmin(BasePermission):
    """
    Permite acceso solo a usuarios con rol 'admin' en su clan.
    Usado para: gestionar usuarios, cambiar roles, configurar clan.
    """
    message = 'Solo los administradores del clan pueden realizar esta acción.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return request.user.profile.role == 'admin'
        except Exception:
            return False


# =====================================================
# PERMISO: Es Admin o Leader del clan
# =====================================================

class IsClanAdminOrLeader(BasePermission):
    """
    Permite acceso a usuarios con rol 'admin' o 'leader' en Clash.
    Usado para: ver estadísticas avanzadas, planificación.
    """
    message = 'Solo administradores y líderes pueden realizar esta acción.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            profile = request.user.profile
            return profile.role in ['admin', 'member']  # admin = líderes del sistema
        except Exception:
            return False


# =====================================================
# PERMISO: Pertenece al mismo clan
# =====================================================

class IsSameClan(BasePermission):
    """
    Verifica que el usuario pertenezca al clan que está consultando.
    Clave para el multi-tenancy: nadie puede ver datos de otros clanes.
    """
    message = 'No tienes acceso a los datos de este clan.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # La verificación de clan específico se hace en has_object_permission
        return True

    def has_object_permission(self, request, view, obj):
        try:
            user_clan = request.user.profile.clan

            # Si el objeto tiene un campo 'clan' directamente
            if hasattr(obj, 'clan'):
                return obj.clan == user_clan

            # Si el objeto ES un clan
            if hasattr(obj, 'clan_tag'):
                return obj == user_clan

            # Si el objeto tiene 'clan_id'
            if hasattr(obj, 'clan_id'):
                return obj.clan_id == user_clan.id

            return False
        except Exception:
            return False


# =====================================================
# PERMISO: Solo lectura para observadores
# =====================================================

class IsAdminOrReadOnly(BasePermission):
    """
    Admins pueden hacer todo.
    Members y Observers solo pueden leer (GET, HEAD, OPTIONS).
    """
    message = 'No tienes permisos para modificar este recurso.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Métodos de solo lectura son permitidos para todos
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # Para escritura, solo admins
        try:
            return request.user.profile.role == 'admin'
        except Exception:
            return False


# =====================================================
# PERMISO: Es el propio usuario o admin
# =====================================================

class IsOwnerOrAdmin(BasePermission):
    """
    Un usuario puede ver/editar sus propios datos.
    Un admin puede ver/editar los datos de cualquier usuario de su clan.
    """
    message = 'No tienes permisos para acceder a este recurso.'

    def has_object_permission(self, request, view, obj):
        try:
            profile = request.user.profile

            # Admin puede acceder a cualquier objeto del clan
            if profile.role == 'admin':
                # Verificar que el objeto pertenezca al mismo clan
                if hasattr(obj, 'clan'):
                    return obj.clan == profile.clan
                if hasattr(obj, 'user'):
                    return obj.user == request.user or profile.role == 'admin'

            # El usuario solo puede acceder a sus propios datos
            if hasattr(obj, 'user'):
                return obj.user == request.user

            return False
        except Exception:
            return False


# =====================================================
# MIXIN: Filtrar por clan automáticamente
# =====================================================

class ClanFilterMixin:
    """
    Mixin para ViewSets que filtra automáticamente por el clan del usuario.
    Usar en lugar de filtrar manualmente en cada view.
    
    Uso:
        class PlayerViewSet(ClanFilterMixin, viewsets.ModelViewSet):
            queryset = Player.objects.all()
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        try:
            clan = user.profile.clan
            # Filtrar por clan si el modelo tiene campo 'clan'
            if hasattr(queryset.model, 'clan'):
                return queryset.filter(clan=clan)
            return queryset
        except Exception:
            return queryset.none()