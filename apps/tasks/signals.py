"""
Django signals for the Tasks app.
"""
from django.db import transaction
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Task, Comment
from apps.notifications.models import Notification


@receiver(m2m_changed, sender=Task.assigned_to.through, dispatch_uid='notify_task_assignment_v1')
def notify_task_assignment(sender, instance, action, pk_set, **kwargs):
    """
    Send notifications when users are assigned to a task (async si hay Redis, sync si no).
    """
    if action == 'post_add' and pk_set:
        ids = list(pk_set)
        def _enqueue():
            try:
                from .tasks import send_task_assignment_notification
                send_task_assignment_notification.delay(instance.id, ids)
            except Exception:
                # Sin Redis/Celery (XAMPP local): crea directo, sin tumbar request.
                from django.contrib.auth import get_user_model
                User = get_user_model()
                to_create = []
                for user_id in ids:
                    try:
                        user = User.objects.get(pk=user_id)
                        if user.id != instance.owner_id:
                            to_create.append(Notification(
                                recipient=user, sender=instance.owner,
                                notification_type='task_assigned', title='New Task Assignment',
                                message=f'You have been assigned to "{instance.title}"',
                                task=instance, priority='medium'))
                    except User.DoesNotExist:
                        continue
                if to_create:
                    Notification.objects.bulk_create(to_create, batch_size=200, ignore_conflicts=True)
        try:
            transaction.on_commit(_enqueue)
        except Exception:
            _enqueue()


@receiver(post_save, sender=Task, dispatch_uid='notify_task_completion_v1')
def notify_task_completion(sender, instance, created, update_fields=None, **kwargs):
    """
    Send notifications when a task transitions to completed (solo transición).
    """
    if created or instance.status != 'completed':
        return
    # FIX: solo si status cambió. Si update_fields no incluye status, ignora
    # para no spamear en cada edición de tarea completada.
    if update_fields is not None and 'status' not in update_fields:
        return
    # Notify assigned users
    for user in instance.assigned_to.exclude(id=instance.owner_id).only('id', 'email')[:100]:
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
