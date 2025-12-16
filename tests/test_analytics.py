"""
Tests for the Analytics app.
"""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestDashboardAPI:
    """Tests for Dashboard endpoint."""
    
    def test_get_dashboard(self, authenticated_client, task, completed_task, overdue_task):
        """Test getting dashboard data."""
        url = reverse('dashboard')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_tasks' in response.data
        assert 'completed_tasks' in response.data
        assert 'pending_tasks' in response.data
        assert 'overdue_tasks' in response.data
        assert 'completion_rate' in response.data
    
    def test_dashboard_counts_correct(self, authenticated_client, task, completed_task):
        """Test that dashboard counts are correct."""
        url = reverse('dashboard')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['completed_tasks'] >= 1
        assert response.data['pending_tasks'] >= 1


@pytest.mark.django_db
class TestTrendsAPI:
    """Tests for Trends endpoint."""
    
    def test_get_task_trends(self, authenticated_client, task):
        """Test getting task trends."""
        url = reverse('task-trends')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
    
    def test_get_trends_with_days_param(self, authenticated_client):
        """Test getting trends with custom days parameter."""
        url = reverse('task-trends') + '?days=7'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) <= 8  # 7 days + today


@pytest.mark.django_db
class TestTasksByStatusAPI:
    """Tests for Tasks by Status endpoint."""
    
    def test_get_tasks_by_status(self, authenticated_client, task, completed_task):
        """Test getting tasks grouped by status."""
        url = reverse('tasks-by-status')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


@pytest.mark.django_db
class TestTasksByPriorityAPI:
    """Tests for Tasks by Priority endpoint."""
    
    def test_get_tasks_by_priority(self, authenticated_client, task):
        """Test getting tasks grouped by priority."""
        url = reverse('tasks-by-priority')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


@pytest.mark.django_db
class TestTeamAnalyticsAPI:
    """Tests for Team Analytics endpoint."""
    
    def test_team_analytics_requires_manager(self, authenticated_client):
        """Test that team analytics requires manager role."""
        url = reverse('team-analytics')
        response = authenticated_client.get(url)
        
        # Regular user should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_manager_can_access_team_analytics(self, manager_client, regular_user):
        """Test that manager can access team analytics."""
        # Assign regular user to manager's team
        from django.contrib.auth import get_user_model
        User = get_user_model()
        manager = User.objects.get(email='manager@example.com')
        regular_user.manager = manager
        regular_user.save()
        
        url = reverse('team-analytics')
        response = manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'team_size' in response.data
        assert 'members' in response.data
