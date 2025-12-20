"""
User-related serializers for the Kibray API
"""
from django.contrib.auth.models import User
from rest_framework import serializers

from core.models import Profile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""

    class Meta:
        model = Profile
    fields = ['id', 'role', 'language']


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user serializer for nested representations"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class UserListSerializer(serializers.ModelSerializer):
    """User list serializer with basic info"""
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'is_active', 'date_joined', 'profile', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class UserDetailSerializer(UserListSerializer):
    """Detailed user serializer with permissions and projects"""
    assigned_projects_count = serializers.SerializerMethodField()
    observer_projects_count = serializers.SerializerMethodField()

    class Meta(UserListSerializer.Meta):
        fields = UserListSerializer.Meta.fields + [
            'groups', 'user_permissions', 'last_login',
            'assigned_projects_count', 'observer_projects_count'
        ]

    def get_assigned_projects_count(self, obj):
        return obj.led_projects.count() if hasattr(obj, 'led_projects') else 0

    def get_observer_projects_count(self, obj):
        return obj.observer_projects.count() if hasattr(obj, 'observer_projects') else 0


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True, 'required': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users (without password)"""

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']


class CurrentUserSerializer(UserDetailSerializer):
    """Serializer for current authenticated user with all details"""
    permissions_detail = serializers.SerializerMethodField()

    class Meta(UserDetailSerializer.Meta):
        fields = UserDetailSerializer.Meta.fields + ['permissions_detail']

    def get_permissions_detail(self, obj):
        return {
            'is_superuser': obj.is_superuser,
            'is_staff': obj.is_staff,
            'is_active': obj.is_active,
        }
