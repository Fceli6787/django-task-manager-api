"""
Notification models for the Task Manager API.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models import TimeStampedModel


class Notification(TimeStampedModel):
    """
    User notifications for task events.
    """
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_completed', 'Task Completed'),
        ('task_overdue', 'Task Overdue'),
        ('task_due_soon', 'Task Due Soon'),
        ('comment_added', 'Comment Added'),
        ('mention', 'Mentioned in Comment'),
        ('task_updated', 'Task Updated'),
        ('team_update', 'Team Update'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications'
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Related objects
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    comment = models.ForeignKey(
        'tasks.Comment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_email_sent = models.BooleanField(default=False)
    is_push_sent = models.BooleanField(default=False)
    
    # Extra data
    metadata = models.JSONField(default=dict, blank=True)
    action_url = models.URLField(blank=True)

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return f"{self.notification_type} for {self.recipient.email}"

    def mark_as_read(self):
        """Mark notification as read."""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])


class NotificationPreference(TimeStampedModel):
    """
    User preferences for notifications.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Email notifications
    email_task_assigned = models.BooleanField(default=True)
    email_task_completed = models.BooleanField(default=True)
    email_task_overdue = models.BooleanField(default=True)
    email_task_due_soon = models.BooleanField(default=True)
    email_comment_added = models.BooleanField(default=True)
    email_mention = models.BooleanField(default=True)
    email_digest = models.BooleanField(default=True)
    email_digest_frequency = models.CharField(
        max_length=20,
        choices=[('daily', 'Daily'), ('weekly', 'Weekly')],
        default='daily'
    )
    
    # Push notifications
    push_task_assigned = models.BooleanField(default=True)
    push_task_completed = models.BooleanField(default=True)
    push_task_overdue = models.BooleanField(default=True)
    push_task_due_soon = models.BooleanField(default=True)
    push_comment_added = models.BooleanField(default=True)
    push_mention = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('notification preference')
        verbose_name_plural = _('notification preferences')

    def __str__(self):
        return f"Preferences for {self.user.email}"
