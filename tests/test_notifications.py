"""
Tests for the Notifications app.
"""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.fixture
def notification(db, regular_user, task):
    """Create and return a notification."""
    from apps.notifications.models import Notification
    return Notification.objects.create(
        recipient=regular_user,
        notification_type='task_assigned',
        title='Test Notification',
        message='This is a test notification',
        task=task,
        priority='medium'
    )


@pytest.mark.django_db
class TestNotificationAPI:
    """Tests for Notification endpoints."""
    
    def test_list_notifications(self, authenticated_client, notification):
        """Test listing notifications."""
        url = reverse('notification-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
    
    def test_get_notification_detail(self, authenticated_client, notification):
        """Test getting notification detail."""
        url = reverse('notification-detail', args=[notification.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == notification.title
    
    def test_get_unread_count(self, authenticated_client, notification):
        """Test getting unread notification count."""
        url = reverse('notification-unread-count')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'unread_count' in response.data
        assert response.data['unread_count'] >= 1
    
    def test_get_unread_notifications(self, authenticated_client, notification):
        """Test getting unread notifications."""
        url = reverse('notification-unread')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_mark_notification_as_read(self, authenticated_client, notification):
        """Test marking a notification as read."""
        url = reverse('notification-mark-read', args=[notification.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_read'] is True
    
    def test_mark_all_as_read(self, authenticated_client, notification):
        """Test marking all notifications as read."""
        url = reverse('notification-mark-all-read')
        response = authenticated_client.post(url, {
            'mark_all': True
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'marked_read' in response.data
    
    def test_dismiss_notification(self, authenticated_client, notification):
        """Test dismissing a notification."""
        url = reverse('notification-dismiss', args=[notification.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_clear_all_notifications(self, authenticated_client, notification):
        """Test clearing all notifications."""
        url = reverse('notification-clear-all')
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'deleted' in response.data


@pytest.mark.django_db
class TestNotificationPreferencesAPI:
    """Tests for Notification Preferences endpoints."""
    
    def test_get_preferences(self, authenticated_client):
        """Test getting notification preferences."""
        url = reverse('notification-preference-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'email_task_assigned' in response.data
    
    def test_update_preferences(self, authenticated_client):
        """Test updating notification preferences."""
        url = reverse('notification-preference-list')
        response = authenticated_client.post(url, {
            'email_task_assigned': False,
            'push_task_assigned': True
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email_task_assigned'] is False
