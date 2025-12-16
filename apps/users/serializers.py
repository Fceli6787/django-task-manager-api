"""
Serializers for the Users app.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import UserActivity

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details.
    """
    full_name = serializers.ReadOnlyField()
    team_members_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'avatar', 'bio', 'phone', 'manager',
            'email_notifications', 'push_notifications',
            'created_at', 'updated_at', 'last_login_at',
            'team_members_count'
        ]
        read_only_fields = ['id', 'email', 'created_at', 'updated_at', 'last_login_at']

    def get_team_members_count(self, obj):
        return obj.team_members.count()


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'password', 'password_confirm',
            'phone', 'bio'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields don't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'avatar', 'bio', 'phone',
            'email_notifications', 'push_notifications'
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields don't match."})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class UserListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for user lists.
    """
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'avatar', 'role']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer with additional user data.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = user.full_name
        
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user data to response
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'full_name': self.user.full_name,
            'role': self.user.role,
            'avatar': self.user.avatar.url if self.user.avatar else None,
        }
        
        # Update last login
        from django.utils import timezone
        self.user.last_login_at = timezone.now()
        self.user.save(update_fields=['last_login_at'])
        
        return data


class UserActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for user activity log.
    """
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'user_email', 'action', 'description',
            'ip_address', 'metadata', 'created_at'
        ]
        read_only_fields = fields


class TeamMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for team member management.
    """
    full_name = serializers.ReadOnlyField()
    tasks_count = serializers.SerializerMethodField()
    completed_tasks_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'avatar', 'tasks_count', 'completed_tasks_count'
        ]

    def get_tasks_count(self, obj):
        return obj.assigned_tasks.filter(is_deleted=False).count()

    def get_completed_tasks_count(self, obj):
        return obj.assigned_tasks.filter(is_deleted=False, status='completed').count()
