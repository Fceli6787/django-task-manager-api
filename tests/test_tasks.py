"""
Tests for the Tasks app.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
class TestCategoryAPI:
    """Tests for Category endpoints."""
    
    def test_list_categories(self, authenticated_client, category):
        """Test listing categories."""
        url = reverse('category-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_create_category(self, authenticated_client):
        """Test creating a category."""
        url = reverse('category-list')
        response = authenticated_client.post(url, {
            'name': 'New Category',
            'description': 'A new category',
            'color': '#e74c3c'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Category'
    
    def test_update_category(self, authenticated_client, category):
        """Test updating a category."""
        url = reverse('category-detail', args=[category.id])
        response = authenticated_client.patch(url, {
            'name': 'Updated Category'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Category'
    
    def test_delete_category(self, authenticated_client, category):
        """Test deleting a category."""
        url = reverse('category-detail', args=[category.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestTagAPI:
    """Tests for Tag endpoints."""
    
    def test_list_tags(self, authenticated_client, tag):
        """Test listing tags."""
        url = reverse('tag-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_tag(self, authenticated_client):
        """Test creating a tag."""
        url = reverse('tag-list')
        response = authenticated_client.post(url, {
            'name': 'new-tag',
            'color': '#2ecc71'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestTaskAPI:
    """Tests for Task endpoints."""
    
    def test_list_tasks(self, authenticated_client, task):
        """Test listing tasks."""
        url = reverse('task-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
    
    def test_create_task(self, authenticated_client, category):
        """Test creating a task."""
        url = reverse('task-list')
        due_date = (timezone.now() + timedelta(days=7)).isoformat()
        
        response = authenticated_client.post(url, {
            'title': 'New Task',
            'description': 'Task description',
            'priority': 'high',
            'status': 'pending',
            'category': category.id,
            'due_date': due_date
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Task'
    
    def test_get_task_detail(self, authenticated_client, task):
        """Test getting task details."""
        url = reverse('task-detail', args=[task.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == task.title
    
    def test_update_task(self, authenticated_client, task):
        """Test updating a task."""
        url = reverse('task-detail', args=[task.id])
        response = authenticated_client.patch(url, {
            'title': 'Updated Task Title',
            'priority': 'urgent'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Task Title'
        assert response.data['priority'] == 'urgent'
    
    def test_delete_task_soft_delete(self, authenticated_client, task):
        """Test that deleting a task performs soft delete."""
        url = reverse('task-detail', args=[task.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify soft delete
        from apps.tasks.models import Task
        deleted_task = Task.all_objects.get(id=task.id)
        assert deleted_task.is_deleted is True
    
    def test_complete_task(self, authenticated_client, task):
        """Test completing a task."""
        url = reverse('task-complete', args=[task.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'completed'
        assert response.data['progress'] == 100
    
    def test_restore_task(self, authenticated_client, task):
        """Test restoring a soft-deleted task."""
        # First soft delete
        task.delete()
        
        url = reverse('task-restore', args=[task.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_deleted'] is False
    
    def test_get_my_tasks(self, authenticated_client, task):
        """Test getting own tasks."""
        url = reverse('task-my-tasks')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_overdue_tasks(self, authenticated_client, overdue_task):
        """Test getting overdue tasks."""
        url = reverse('task-overdue')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_get_trash(self, authenticated_client, task):
        """Test getting deleted tasks."""
        task.delete()
        
        url = reverse('task-trash')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestTaskFiltering:
    """Tests for task filtering."""
    
    def test_filter_by_status(self, authenticated_client, task, completed_task):
        """Test filtering tasks by status."""
        url = reverse('task-list') + '?status=completed'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        for task_data in response.data['results']:
            assert task_data['status'] == 'completed'
    
    def test_filter_by_priority(self, authenticated_client, task):
        """Test filtering tasks by priority."""
        url = reverse('task-list') + '?priority=medium'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_search_tasks(self, authenticated_client, task):
        """Test searching tasks."""
        url = reverse('task-list') + f'?search={task.title[:5]}'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTaskHistory:
    """Tests for task history tracking."""
    
    def test_task_history_created_on_create(self, authenticated_client, category):
        """Test that history is created when task is created."""
        from apps.tasks.models import TaskHistory
        
        url = reverse('task-list')
        response = authenticated_client.post(url, {
            'title': 'History Test Task',
            'description': 'Testing history',
            'priority': 'low'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        task_id = response.data['id']
        history = TaskHistory.objects.filter(task_id=task_id)
        assert history.exists()
        assert history.first().action == 'created'
    
    def test_get_task_history(self, authenticated_client, task):
        """Test getting task history."""
        url = reverse('task-history', args=[task.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
