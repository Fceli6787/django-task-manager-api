"""
Views for the Users app.
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.permissions import IsAdminUser, IsManagerOrAdmin
from core.pagination import StandardResultsSetPagination
from .models import UserActivity
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    UserListSerializer, PasswordChangeSerializer, CustomTokenObtainPairSerializer,
    UserActivitySerializer, TeamMemberSerializer
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token view with additional user data in response.
    """
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_description="Obtain JWT token pair for authentication",
        responses={
            200: openapi.Response(
                description="JWT tokens and user data",
                examples={
                    "application/json": {
                        "access": "eyJ0...",
                        "refresh": "eyJ0...",
                        "user": {
                            "id": 1,
                            "email": "user@example.com",
                            "full_name": "John Doe",
                            "role": "user"
                        }
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Log activity
        if response.status_code == 200:
            email = request.data.get('email')
            try:
                user = User.objects.get(email=email)
                UserActivity.objects.create(
                    user=user,
                    action='login',
                    description='User logged in',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except User.DoesNotExist:
                pass
        
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user account",
        responses={
            201: UserSerializer,
            400: "Validation errors"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users (Admin only for list/create/delete).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action in ['list', 'create', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'list':
            return UserListSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        elif user.role == 'manager':
            # Managers can see themselves and their team
            return User.objects.filter(id=user.id) | user.team_members.all()
        return User.objects.filter(id=user.id)

    @swagger_auto_schema(
        operation_description="Get current authenticated user profile"
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update current user profile",
        request_body=UserUpdateSerializer
    )
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update current user profile."""
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    @swagger_auto_schema(
        operation_description="Change current user password",
        request_body=PasswordChangeSerializer
    )
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change current user password."""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response({'message': 'Password changed successfully'})

    @swagger_auto_schema(
        operation_description="Get team members (for managers and admins)"
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsManagerOrAdmin])
    def team(self, request):
        """Get team members for current manager."""
        team_members = request.user.get_team_members()
        serializer = TeamMemberSerializer(team_members, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get user activity log"
    )
    @action(detail=False, methods=['get'])
    def activity(self, request):
        """Get current user's activity log."""
        activities = UserActivity.objects.filter(user=request.user)[:50]
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)


class TeamMemberViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing team members (for managers).
    """
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return self.request.user.get_team_members()

    @swagger_auto_schema(
        operation_description="Assign a user to manager's team"
    )
    @action(detail=True, methods=['post'])
    def assign_to_team(self, request, pk=None):
        """Assign a user to manager's team."""
        if request.user.role not in ['admin', 'manager']:
            return Response(
                {'error': 'Only managers and admins can assign team members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(pk=pk)
            user.manager = request.user
            user.save()
            return Response({'message': f'User {user.email} assigned to your team'})
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Remove a user from manager's team"
    )
    @action(detail=True, methods=['post'])
    def remove_from_team(self, request, pk=None):
        """Remove a user from manager's team."""
        try:
            user = User.objects.get(pk=pk, manager=request.user)
            user.manager = None
            user.save()
            return Response({'message': f'User {user.email} removed from your team'})
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found in your team'},
                status=status.HTTP_404_NOT_FOUND
            )
