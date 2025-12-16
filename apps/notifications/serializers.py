"""
Serializers for the Notifications app.
"""
from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notifications.
    """
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'sender', 'sender_name',
            'notification_type', 'title', 'message', 'priority',
            'task', 'task_title', 'comment',
            'is_read', 'read_at', 'action_url', 'metadata',
            'created_at'
        ]
        read_only_fields = [
            'id', 'recipient', 'sender', 'notification_type',
            'title', 'message', 'task', 'comment', 'created_at'
        ]


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for notification lists.
    """
    sender_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message',
            'priority', 'is_read', 'sender_avatar', 'created_at'
        ]

    def get_sender_avatar(self, obj):
        if obj.sender and obj.sender.avatar:
            return obj.sender.avatar.url
        return None


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for notification preferences.
    """
    class Meta:
        model = NotificationPreference
        fields = [
            'email_task_assigned', 'email_task_completed',
            'email_task_overdue', 'email_task_due_soon',
            'email_comment_added', 'email_mention',
            'email_digest', 'email_digest_frequency',
            'push_task_assigned', 'push_task_completed',
            'push_task_overdue', 'push_task_due_soon',
            'push_comment_added', 'push_mention',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end'
        ]


class MarkReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read.
    """
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    mark_all = serializers.BooleanField(default=False)
