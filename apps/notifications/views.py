"""
Views for the Notifications app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema

from core.pagination import StandardResultsSetPagination
from .models import Notification, NotificationPreference
from .serializers import (
    NotificationSerializer, NotificationListSerializer,
    NotificationPreferenceSerializer, MarkReadSerializer
)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing and managing notifications.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer

    @swagger_auto_schema(
        operation_description="Get unread notifications count"
    )
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})

    @swagger_auto_schema(
        operation_description="Get only unread notifications"
    )
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications."""
        notifications = self.get_queryset().filter(is_read=False)
        page = self.paginate_queryset(notifications)
        if page is not None:
            serializer = NotificationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = NotificationListSerializer(notifications, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Mark notification as read"
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response(NotificationSerializer(notification).data)

    @swagger_auto_schema(
        operation_description="Mark multiple or all notifications as read",
        request_body=MarkReadSerializer
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark multiple notifications as read."""
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        queryset = self.get_queryset().filter(is_read=False)
        
        if serializer.validated_data.get('mark_all'):
            count = queryset.update(is_read=True, read_at=timezone.now())
        elif serializer.validated_data.get('notification_ids'):
            count = queryset.filter(
                id__in=serializer.validated_data['notification_ids']
            ).update(is_read=True, read_at=timezone.now())
        else:
            count = 0
        
        return Response({'marked_read': count})

    @swagger_auto_schema(
        operation_description="Delete a notification"
    )
    @action(detail=True, methods=['delete'])
    def dismiss(self, request, pk=None):
        """Delete a notification."""
        notification = self.get_object()
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_description="Clear all notifications"
    )
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Delete all notifications for current user."""
        count = self.get_queryset().delete()[0]
        return Response({'deleted': count})


class NotificationPreferenceViewSet(viewsets.ViewSet):
    """
    ViewSet for managing notification preferences.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get notification preferences"
    )
    def list(self, request):
        """Get current user's notification preferences."""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(preferences)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update notification preferences",
        request_body=NotificationPreferenceSerializer
    )
    def create(self, request):
        """Update notification preferences."""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(
            preferences, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
