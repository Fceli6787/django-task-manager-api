"""
pytest configuration and fixtures for the Task Manager API tests.
"""
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an API client instance."""
    return APIClient()


@pytest.fixture
def user_data():
    """Return sample user data for registration."""
    return {
        'email': 'testuser@example.com',
        'password': 'TestPass123!',
        'password_confirm': 'TestPass123!',
        'first_name': 'Test',
        'last_name': 'User',
    }


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    return User.objects.create_superuser(
        email='admin@example.com',
        password='AdminPass123!',
        first_name='Admin',
        last_name='User'
    )


@pytest.fixture
def manager_user(db):
    """Create and return a manager user."""
    return User.objects.create_user(
        email='manager@example.com',
        password='ManagerPass123!',
        first_name='Manager',
        last_name='User',
        role='manager'
    )


@pytest.fixture
def regular_user(db):
    """Create and return a regular user."""
    return User.objects.create_user(
        email='user@example.com',
        password='UserPass123!',
        first_name='Regular',
        last_name='User',
        role='user'
    )


@pytest.fixture
def authenticated_client(api_client, regular_user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=regular_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return an admin-authenticated API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def manager_client(api_client, manager_user):
    """Return a manager-authenticated API client."""
    api_client.force_authenticate(user=manager_user)
    return api_client


@pytest.fixture
def category(db, regular_user):
    """Create and return a category."""
    from apps.tasks.models import Category
    return Category.objects.create(
        name='Test Category',
        description='A test category',
        color='#3498db',
        owner=regular_user
    )


@pytest.fixture
def tag(db, regular_user):
    """Create and return a tag."""
    from apps.tasks.models import Tag
    return Tag.objects.create(
        name='test-tag',
        color='#9b59b6',
        owner=regular_user
    )


@pytest.fixture
def task(db, regular_user, category):
    """Create and return a task."""
    from apps.tasks.models import Task
    from django.utils import timezone
    from datetime import timedelta
    
    return Task.objects.create(
        title='Test Task',
        description='A test task description',
        owner=regular_user,
        category=category,
        priority='medium',
        status='pending',
        due_date=timezone.now() + timedelta(days=7)
    )


@pytest.fixture
def completed_task(db, regular_user, category):
    """Create and return a completed task."""
    from apps.tasks.models import Task
    from django.utils import timezone
    
    task = Task.objects.create(
        title='Completed Task',
        description='A completed task',
        owner=regular_user,
        category=category,
        priority='high',
        status='completed',
        completed_at=timezone.now()
    )
    return task


@pytest.fixture
def overdue_task(db, regular_user):
    """Create and return an overdue task."""
    from apps.tasks.models import Task
    from django.utils import timezone
    from datetime import timedelta
    
    return Task.objects.create(
        title='Overdue Task',
        description='An overdue task',
        owner=regular_user,
        priority='urgent',
        status='pending',
        due_date=timezone.now() - timedelta(days=1)
    )
