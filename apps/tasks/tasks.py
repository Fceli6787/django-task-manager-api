"""
Celery tasks for the Tasks app.
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta


@shared_task
def check_overdue_tasks():
    """
    Check for overdue tasks and create notifications.
    """
    from apps.tasks.models import Task
    from apps.notifications.models import Notification
    
    now = timezone.now()
    
    # Find tasks that just became overdue (within the last hour)
    one_hour_ago = now - timedelta(hours=1)
    
    overdue_tasks = Task.objects.filter(
        due_date__lt=now,
        due_date__gte=one_hour_ago,
        status__in=['pending', 'in_progress', 'on_hold']
    )
    
    notifications_created = 0
    for task in overdue_tasks:
        # Notify owner
        Notification.objects.create(
            recipient=task.owner,
            notification_type='task_overdue',
            title='Task Overdue',
            message=f'Your task "{task.title}" is now overdue.',
            task=task,
            priority='high'
        )
        notifications_created += 1
        
        # Notify assigned users
        for user in task.assigned_to.all():
            if user != task.owner:
                Notification.objects.create(
                    recipient=user,
                    notification_type='task_overdue',
                    title='Assigned Task Overdue',
                    message=f'The task "{task.title}" assigned to you is now overdue.',
                    task=task,
                    priority='high'
                )
                notifications_created += 1
    
    return f'Created {notifications_created} overdue notifications'


@shared_task
def process_recurring_tasks():
    """
    Process recurring tasks and create new instances.
    """
    from apps.tasks.models import Task
    
    now = timezone.now()
    today = now.date()
    
    # Find recurring tasks that need new instances
    recurring_tasks = Task.objects.filter(
        is_recurring=True,
        status='completed',
        recurrence_pattern__in=['daily', 'weekly', 'monthly', 'yearly']
    ).exclude(
        recurrence_end_date__lt=now
    )
    
    tasks_created = 0
    for task in recurring_tasks:
        # Calculate next due date based on pattern
        if task.recurrence_pattern == 'daily':
            next_due = task.due_date + timedelta(days=1) if task.due_date else now + timedelta(days=1)
        elif task.recurrence_pattern == 'weekly':
            next_due = task.due_date + timedelta(weeks=1) if task.due_date else now + timedelta(weeks=1)
        elif task.recurrence_pattern == 'monthly':
            next_due = task.due_date + timedelta(days=30) if task.due_date else now + timedelta(days=30)
        elif task.recurrence_pattern == 'yearly':
            next_due = task.due_date + timedelta(days=365) if task.due_date else now + timedelta(days=365)
        else:
            continue
        
        # Check if we should create the new task
        if task.recurrence_end_date and next_due > task.recurrence_end_date:
            continue
        
        # Create new task instance
        new_task = Task.objects.create(
            title=task.title,
            description=task.description,
            owner=task.owner,
            category=task.category,
            priority=task.priority,
            due_date=next_due,
            is_recurring=True,
            recurrence_pattern=task.recurrence_pattern,
            recurrence_end_date=task.recurrence_end_date,
            estimated_hours=task.estimated_hours,
        )
        
        # Copy tags and assignees
        new_task.tags.set(task.tags.all())
        new_task.assigned_to.set(task.assigned_to.all())
        
        tasks_created += 1
    
    return f'Created {tasks_created} recurring tasks'


@shared_task
def send_task_assignment_notification(task_id, assigned_user_ids):
    """
    Send notifications when users are assigned to a task.
    """
    from apps.tasks.models import Task
    from apps.users.models import User
    from apps.notifications.models import Notification
    
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return 'Task not found'
    
    users = User.objects.filter(id__in=assigned_user_ids)
    
    for user in users:
        Notification.objects.create(
            recipient=user,
            sender=task.owner,
            notification_type='task_assigned',
            title='New Task Assignment',
            message=f'You have been assigned to "{task.title}"',
            task=task,
            priority='medium'
        )
    
    return f'Sent {users.count()} assignment notifications'
