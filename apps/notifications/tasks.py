"""
Celery tasks for the Notifications app.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def send_due_date_reminders():
    """
    Send reminders for tasks due today and tomorrow (bulk, idempotente).
    """
    from apps.tasks.models import Task
    from apps.notifications.models import Notification
    
    now = timezone.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    
    notifications_to_create = []

    # Tasks due today
    tasks_due_today = Task.objects.select_related('owner').prefetch_related('assigned_to').filter(
        due_date__date=today,
        status__in=['pending', 'in_progress', 'on_hold']
    )[:2000]
    
    notifications_created = 0
    
    for task in tasks_due_today:
        # Check if reminder already sent today
        existing = Notification.objects.filter(
            task=task,
            notification_type='task_due_soon',
            created_at__date=today
        ).exists()
        
        if not existing:
            notifications_to_create.append(Notification(
                recipient=task.owner,
                notification_type='task_due_soon',
                title='Task Due Today',
                message=f'Your task "{task.title}" is due today!',
                task=task,
                priority='high'
            ))
            
            # Also notify assigned users
            for user in task.assigned_to.all():
                if user.id != task.owner_id:
                    notifications_to_create.append(Notification(
                        recipient=user,
                        notification_type='task_due_soon',
                        title='Assigned Task Due Today',
                        message=f'The task "{task.title}" is due today!',
                        task=task,
                        priority='high'
                    ))
    
    # Tasks due tomorrow
    tasks_due_tomorrow = Task.objects.select_related('owner').filter(
        due_date__date=tomorrow,
        status__in=['pending', 'in_progress', 'on_hold']
    )[:2000]
    
    for task in tasks_due_tomorrow:
        existing = Notification.objects.filter(
            task=task,
            notification_type='task_due_soon',
            created_at__date=today,
            message__icontains='tomorrow'
        ).exists()
        
        if not existing:
            notifications_to_create.append(Notification(
                recipient=task.owner,
                notification_type='task_due_soon',
                title='Task Due Tomorrow',
                message=f'Your task "{task.title}" is due tomorrow.',
                task=task,
                priority='medium'
            ))
    
    if notifications_to_create:
        Notification.objects.bulk_create(notifications_to_create, batch_size=500, ignore_conflicts=True)
    return f'Sent {len(notifications_to_create)} due date reminders'


@shared_task
def clean_old_notifications():
    """
    Delete old read notifications (older than 30 days).
    """
    from apps.notifications.models import Notification
    
    cutoff_date = timezone.now() - timedelta(days=30)
    
    deleted_count, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff_date
    ).delete()
    
    return f'Deleted {deleted_count} old notifications'


@shared_task
def send_email_notification(notification_id):
    """
    Send email for a notification.
    """
    from apps.notifications.models import Notification
    from django.core.mail import send_mail
    from django.conf import settings
    
    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return 'Notification not found'
    
    # Check user preferences
    if not notification.recipient.email_notifications:
        return 'User has email notifications disabled'
    
    try:
        send_mail(
            subject=notification.title,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            fail_silently=False,
        )
        
        notification.is_email_sent = True
        notification.save(update_fields=['is_email_sent'])
        
        return f'Email sent to {notification.recipient.email}'
    except Exception as e:
        return f'Failed to send email: {str(e)}'


@shared_task
def send_mention_notification(comment_id, mentioned_user_ids):
    """
    Send notifications for @mentions in comments.
    """
    from apps.tasks.models import Comment
    from apps.users.models import User
    from apps.notifications.models import Notification
    
    try:
        comment = Comment.objects.select_related('task', 'author').get(id=comment_id)
    except Comment.DoesNotExist:
        return 'Comment not found'
    
    users = User.objects.filter(id__in=mentioned_user_ids)
    
    for user in users:
        Notification.objects.create(
            recipient=user,
            sender=comment.author,
            notification_type='mention',
            title='You were mentioned',
            message=f'{comment.author.full_name} mentioned you in a comment on "{comment.task.title}"',
            task=comment.task,
            comment=comment,
            priority='medium'
        )
    
    return f'Sent {users.count()} mention notifications'
