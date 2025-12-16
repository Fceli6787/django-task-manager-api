"""
Tests for the Users app.
"""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestUserRegistration:
    """Tests for user registration endpoint."""
    
    def test_register_user_success(self, api_client, user_data):
        """Test successful user registration."""
        url = reverse('register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['email'] == user_data['email']
    
    def test_register_user_password_mismatch(self, api_client, user_data):
        """Test registration fails with mismatched passwords."""
        user_data['password_confirm'] = 'DifferentPass123!'
        url = reverse('register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_user_weak_password(self, api_client, user_data):
        """Test registration fails with weak password."""
        user_data['password'] = '123'
        user_data['password_confirm'] = '123'
        url = reverse('register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_duplicate_email(self, api_client, user_data, regular_user):
        """Test registration fails with duplicate email."""
        user_data['email'] = regular_user.email
        url = reverse('register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserAuthentication:
    """Tests for user authentication endpoints."""
    
    def test_login_success(self, api_client, regular_user):
        """Test successful login."""
        url = reverse('token_obtain_pair')
        response = api_client.post(url, {
            'email': regular_user.email,
            'password': 'UserPass123!'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data
    
    def test_login_invalid_credentials(self, api_client, regular_user):
        """Test login fails with invalid credentials."""
        url = reverse('token_obtain_pair')
        response = api_client.post(url, {
            'email': regular_user.email,
            'password': 'WrongPassword!'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_refresh(self, api_client, regular_user):
        """Test token refresh."""
        # First, login to get tokens
        login_url = reverse('token_obtain_pair')
        login_response = api_client.post(login_url, {
            'email': regular_user.email,
            'password': 'UserPass123!'
        }, format='json')
        
        refresh_token = login_response.data['refresh']
        
        # Then refresh
        refresh_url = reverse('token_refresh')
        response = api_client.post(refresh_url, {
            'refresh': refresh_token
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data


@pytest.mark.django_db
class TestUserProfile:
    """Tests for user profile endpoints."""
    
    def test_get_current_user(self, authenticated_client, regular_user):
        """Test getting current user profile."""
        url = reverse('user-me')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == regular_user.email
    
    def test_update_profile(self, authenticated_client, regular_user):
        """Test updating user profile."""
        url = reverse('user-update-profile')
        response = authenticated_client.patch(url, {
            'first_name': 'Updated',
            'bio': 'New bio'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'
    
    def test_change_password(self, authenticated_client, regular_user):
        """Test changing password."""
        url = reverse('user-change-password')
        response = authenticated_client.post(url, {
            'old_password': 'UserPass123!',
            'new_password': 'NewPass456!',
            'new_password_confirm': 'NewPass456!'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_unauthenticated_access(self, api_client):
        """Test unauthenticated access is denied."""
        url = reverse('user-me')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserRoles:
    """Tests for role-based access control."""
    
    def test_admin_can_list_users(self, admin_client):
        """Test admin can list all users."""
        url = reverse('user-list')
        response = admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_regular_user_cannot_list_users(self, authenticated_client):
        """Test regular user cannot list all users."""
        url = reverse('user-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_manager_can_view_team(self, manager_client):
        """Test manager can view team members."""
        url = reverse('user-team')
        response = manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
