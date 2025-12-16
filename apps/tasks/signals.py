"""
Django signals for the Tasks app.
"""
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Task, Comment
from apps.notifications.models import Notification


@receiver(m2m_changed, sender=Task.assigned_to.through)
def notify_task_assignment(sender, instance, action, pk_set, **kwargs):
    """
    Send notifications when users are assigned to a task.
    """
    if action == 'post_add' and pk_set:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        for user_id in pk_set:
            try:
                user = User.objects.get(pk=user_id)
                if user != instance.owner:
                    Notification.objects.create(
                        recipient=user,
                        sender=instance.owner,
                        notification_type='task_assigned',
                        title='New Task Assignment',
                        message=f'You have been assigned to "{instance.title}"',
                        task=instance,
                        priority='medium'
                    )
            except User.DoesNotExist:
                pass


@receiver(post_save, sender=Task)
def notify_task_completion(sender, instance, created, **kwargs):
    """
    Send notifications when a task is completed.
    """
    if not created and instance.status == 'completed':
        # Notify assigned users
        for user in instance.assigned_to.exclude(id=instance.owner.id):
            Notification.objects.get_or_create(
                recipient=user,
                task=instance,
                notification_type='task_completed',
                defaults={
                    'sender': instance.owner,
                    'title': 'Task Completed',
                    'message': f'The task "{instance.title}" has been marked as completed',
                    'priority': 'low'
                }
            )
