from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Clan, UserProfile


# =====================================================
# SERIALIZER: JWT personalizado (agrega datos extra al token)
# =====================================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extiende el token JWT para incluir datos útiles del usuario.
    El frontend recibirá: access, refresh, y datos del usuario.
    """

    def validate(self, attrs):
        data = super().validate(attrs)

        # Obtener perfil del usuario
        try:
            profile = self.user.profile
            clan = profile.clan
            data['user'] = {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'full_name': f"{self.user.first_name} {self.user.last_name}".strip(),
                'role': profile.role,
                'clan_id': clan.id,
                'clan_name': clan.clan_name,
                'clan_tag': clan.clan_tag,
                'player_tag': profile.player_tag,
            }
        except UserProfile.DoesNotExist:
            # Usuario sin perfil (superadmin del sistema)
            data['user'] = {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'full_name': f"{self.user.first_name} {self.user.last_name}".strip(),
                'role': 'superadmin',
                'clan_id': None,
                'clan_name': None,
                'clan_tag': None,
                'player_tag': None,
            }

        return data


# =====================================================
# SERIALIZER: Registro de usuario
# =====================================================

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para registrar un nuevo usuario en un clan existente.
    El clan debe existir previamente.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    # Campos del perfil
    clan_tag = serializers.CharField(
        required=True,
        help_text="Tag del clan al que pertenece (ej: #2C29G2RJL)"
    )
    player_tag = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Tag del jugador en Clash (opcional)"
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'password_confirm',
            'clan_tag',
            'player_tag',
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }

    def validate(self, attrs):
        # Verificar que las contraseñas coincidan
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password': 'Las contraseñas no coinciden.'
            })

        # Verificar que el clan exista
        clan_tag = attrs.get('clan_tag', '').upper()
        if not clan_tag.startswith('#'):
            clan_tag = f'#{clan_tag}'

        try:
            clan = Clan.objects.get(clan_tag=clan_tag)
            attrs['clan'] = clan
        except Clan.DoesNotExist:
            raise serializers.ValidationError({
                'clan_tag': f'No existe ningún clan con el tag {clan_tag}.'
            })

        # Verificar que el email no esté en uso
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({
                'email': 'Ya existe una cuenta con este email.'
            })

        return attrs

    def create(self, validated_data):
        # Extraer campos del perfil
        clan = validated_data.pop('clan')
        player_tag = validated_data.pop('player_tag', None)
        validated_data.pop('password_confirm')

        # Crear el usuario
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
        )

        # Crear el perfil vinculado al clan
        # Por defecto: rol 'member', el admin del clan puede cambiarlo después
        UserProfile.objects.create(
            user=user,
            clan=clan,
            role='member',
            player_tag=player_tag or None,
        )

        return user


# =====================================================
# SERIALIZER: Perfil de usuario (lectura y actualización)
# =====================================================

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para ver y actualizar el perfil de usuario.
    """

    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    full_name = serializers.SerializerMethodField()
    clan_name = serializers.CharField(source='clan.clan_name', read_only=True)
    clan_tag = serializers.CharField(source='clan.clan_tag', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'role_display',
            'clan_name',
            'clan_tag',
            'player_tag',
            'created_at',
        ]
        read_only_fields = ['role', 'clan_name', 'clan_tag', 'created_at']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

    def update(self, instance, validated_data):
        # Actualizar campos del User si vienen
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.save()

        # Actualizar perfil
        instance.player_tag = validated_data.get('player_tag', instance.player_tag)
        instance.save()
        return instance


# =====================================================
# SERIALIZER: Cambio de contraseña
# =====================================================

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para cambiar la contraseña del usuario autenticado.
    """

    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password': 'Las contraseñas no coinciden.'
            })
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value


# =====================================================
# SERIALIZER: Lista de usuarios del clan (para admins)
# =====================================================

class ClanUserListSerializer(serializers.ModelSerializer):
    """
    Serializer para que los admins vean los usuarios del clan.
    """

    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'username',
            'email',
            'full_name',
            'role',
            'role_display',
            'player_tag',
            'last_login',
            'is_active',
            'created_at',
        ]

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()


# =====================================================
# SERIALIZER: Actualizar rol de usuario (solo admins)
# =====================================================

class UpdateUserRoleSerializer(serializers.ModelSerializer):
    """
    Serializer para que los admins cambien el rol de un usuario.
    """

    class Meta:
        model = UserProfile
        fields = ['role']

    def validate_role(self, value):
        valid_roles = ['admin', 'member', 'observer']
        if value not in valid_roles:
            raise serializers.ValidationError(
                f'Rol inválido. Opciones: {", ".join(valid_roles)}'
            )
        return value