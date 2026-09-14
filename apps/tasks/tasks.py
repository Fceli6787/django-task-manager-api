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
    Check for overdue tasks and create notifications (idempotente + bulk).
    """
    from apps.tasks.models import Task
    from apps.notifications.models import Notification
    
    now = timezone.now()
    
    # FIX: no ventana de 1h (perdía tareas si Beat caía). Marca idempotente.
    overdue_tasks = Task.objects.select_related('owner').prefetch_related('assigned_to').filter(
        due_date__lt=now,
        overdue_notified_at__isnull=True,
        status__in=['pending', 'in_progress', 'on_hold']
    )[:2000]
    
    to_create = []
    to_mark_ids = []
    for task in overdue_tasks:
        to_create.append(Notification(
            recipient=task.owner,
            notification_type='task_overdue',
            title='Task Overdue',
            message=f'Your task "{task.title}" is now overdue.',
            task=task,
            priority='high'
        ))
        to_mark_ids.append(task.id)
        for user in task.assigned_to.all():
            if user.id != task.owner_id:
                to_create.append(Notification(
                    recipient=user,
                    notification_type='task_overdue',
                    title='Assigned Task Overdue',
                    message=f'The task "{task.title}" assigned to you is now overdue.',
                    task=task,
                    priority='high'
                ))
    
    if to_create:
        Notification.objects.bulk_create(to_create, batch_size=500, ignore_conflicts=True)
    if to_mark_ids:
        Task.objects.filter(id__in=to_mark_ids).update(overdue_notified_at=now)
    
    return f'Created {len(to_create)} overdue notifications'


@shared_task
def process_recurring_tasks():
    """
    Process recurring tasks and create new instances (idempotente, fechas reales).
    """
    from apps.tasks.models import Task
    from dateutil.relativedelta import relativedelta
    
    now = timezone.now()
    
    # FIX: solo genera si no se generó en las últimas 20h (evita duplicado diario).
    cutoff = now - timedelta(hours=20)
    recurring_tasks = Task.objects.select_related('category', 'owner').prefetch_related('tags', 'assigned_to').filter(
        is_recurring=True,
        status='completed',
        recurrence_pattern__in=['daily', 'weekly', 'monthly', 'yearly']
    ).filter(
        Q(last_recurrence_at__isnull=True) | Q(last_recurrence_at__lt=cutoff)
    ).exclude(
        recurrence_end_date__lt=now
    )[:500]
    
    tasks_created = 0
    for task in recurring_tasks:
        base = task.due_date or now
        # FIX: relativedelta para monthly/yearly (antes +30/+365 fijos).
        if task.recurrence_pattern == 'daily':
            next_due = base + timedelta(days=1)
        elif task.recurrence_pattern == 'weekly':
            next_due = base + timedelta(weeks=1)
        elif task.recurrence_pattern == 'monthly':
            next_due = base + relativedelta(months=1)
        elif task.recurrence_pattern == 'yearly':
            next_due = base + relativedelta(years=1)
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

        task.last_recurrence_at = now
        task.save(update_fields=['last_recurrence_at', 'updated_at'])
        
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
