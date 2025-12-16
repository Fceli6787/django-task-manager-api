"""
Admin configuration for the Notifications app.
"""
from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for Notification model."""
    
    list_display = (
        'title', 'recipient', 'notification_type', 'priority',
        'is_read', 'is_email_sent', 'created_at'
    )
    list_filter = ('notification_type', 'priority', 'is_read', 'is_email_sent', 'created_at')
    search_fields = ('title', 'message', 'recipient__email')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    readonly_fields = ('recipient', 'sender', 'task', 'comment', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'message', 'notification_type', 'priority')
        }),
        ('Recipients', {
            'fields': ('recipient', 'sender')
        }),
        ('Related Objects', {
            'fields': ('task', 'comment', 'action_url', 'metadata')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'is_email_sent', 'is_push_sent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin configuration for NotificationPreference model."""
    
    list_display = ('user', 'email_digest', 'email_digest_frequency', 'quiet_hours_enabled')
    list_filter = ('email_digest', 'email_digest_frequency', 'quiet_hours_enabled')
    search_fields = ('user__email',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Email Notifications', {
            'fields': (
                'email_task_assigned', 'email_task_completed',
                'email_task_overdue', 'email_task_due_soon',
                'email_comment_added', 'email_mention',
                'email_digest', 'email_digest_frequency'
            )
        }),
        ('Push Notifications', {
            'fields': (
                'push_task_assigned', 'push_task_completed',
                'push_task_overdue', 'push_task_due_soon',
                'push_comment_added', 'push_mention'
            )
        }),
        ('Quiet Hours', {
            'fields': ('quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end')
        }),
    )
