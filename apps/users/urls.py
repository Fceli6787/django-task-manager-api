"""
URL patterns for the Users app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserViewSet, TeamMemberViewSet,
    CustomTokenObtainPairView, UserRegistrationView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'team', TeamMemberViewSet, basename='team')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    
    # User endpoints
    path('', include(router.urls)),
]
