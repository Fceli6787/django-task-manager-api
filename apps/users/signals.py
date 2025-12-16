"""
Django signals for the Users app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.notifications.models import NotificationPreference

User = get_user_model()


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """
    Create notification preferences when a new user is created.
    """
    if created:
        NotificationPreference.objects.get_or_create(user=instance)
