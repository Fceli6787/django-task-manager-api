"""
Views for the Tasks app.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.permissions import CanManageTasks, IsOwner
from core.pagination import StandardResultsSetPagination
from .models import Task, Category, Tag, Comment, TaskAttachment, TaskHistory
from .serializers import (
    TaskListSerializer, TaskDetailSerializer, TaskCreateSerializer,
    TaskUpdateSerializer, CategorySerializer, TagSerializer,
    CommentSerializer, TaskAttachmentSerializer, TaskHistorySerializer,
    BulkTaskActionSerializer
)
from .filters import TaskFilter


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing task categories.
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)

    @swagger_auto_schema(
        operation_description="List all categories for current user"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new category"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing task tags.
    """
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Tag.objects.filter(owner=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tasks with full CRUD and soft-delete support.
    """
    permission_classes = [IsAuthenticated, CanManageTasks]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority', 'status', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        
        # Base queryset (non-deleted tasks)
        queryset = Task.objects.all()
        
        # Role-based filtering
        if user.role == 'admin':
            pass  # Admin sees all
        elif user.role == 'manager':
            # Manager sees own tasks and team tasks
            team_users = user.team_members.values_list('id', flat=True)
            queryset = queryset.filter(
                Q(owner=user) | 
                Q(assigned_to=user) | 
                Q(owner__in=team_users)
            )
        else:
            # Regular user sees own and assigned tasks
            queryset = queryset.filter(
                Q(owner=user) | Q(assigned_to=user)
            )
        
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        elif self.action == 'create':
            return TaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        return TaskDetailSerializer

    def perform_create(self, serializer):
        task = serializer.save()
        # Create history entry
        TaskHistory.objects.create(
            task=task,
            user=self.request.user,
            field_name='task',
            action='created',
            new_value=task.title
        )

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        task = serializer.save()
        
        # Log status change
        if old_status != task.status:
            TaskHistory.objects.create(
                task=task,
                user=self.request.user,
                field_name='status',
                old_value=old_status,
                new_value=task.status,
                action='updated'
            )

    def perform_destroy(self, instance):
        # Soft delete
        instance.delete()
        TaskHistory.objects.create(
            task=instance,
            user=self.request.user,
            field_name='task',
            action='deleted'
        )

    @swagger_auto_schema(
        operation_description="Get tasks assigned to current user"
    )
    @action(detail=False, methods=['get'])
    def assigned_to_me(self, request):
        """Get tasks assigned to current user."""
        tasks = Task.objects.filter(assigned_to=request.user)
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get tasks created by current user"
    )
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Get tasks created by current user."""
        tasks = Task.objects.filter(owner=request.user)
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get overdue tasks"
    )
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue tasks for current user."""
        now = timezone.now()
        tasks = self.get_queryset().filter(
            due_date__lt=now,
            status__in=['pending', 'in_progress', 'on_hold']
        )
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get tasks due today"
    )
    @action(detail=False, methods=['get'])
    def due_today(self, request):
        """Get tasks due today."""
        today = timezone.now().date()
        tasks = self.get_queryset().filter(
            due_date__date=today,
            status__in=['pending', 'in_progress', 'on_hold']
        )
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get tasks due this week"
    )
    @action(detail=False, methods=['get'])
    def due_this_week(self, request):
        """Get tasks due this week."""
        from datetime import timedelta
        today = timezone.now().date()
        week_end = today + timedelta(days=7)
        tasks = self.get_queryset().filter(
            due_date__date__gte=today,
            due_date__date__lte=week_end,
            status__in=['pending', 'in_progress', 'on_hold']
        )
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Mark task as completed"
    )
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as completed."""
        task = self.get_object()
        task.complete()
        TaskHistory.objects.create(
            task=task,
            user=request.user,
            field_name='status',
            old_value='in_progress',
            new_value='completed',
            action='updated'
        )
        return Response(TaskDetailSerializer(task).data)

    @swagger_auto_schema(
        operation_description="Restore a soft-deleted task"
    )
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore a soft-deleted task."""
        try:
            task = Task.all_objects.get(pk=pk, is_deleted=True)
            if task.owner != request.user and request.user.role != 'admin':
                return Response(
                    {'error': 'You can only restore your own tasks'},
                    status=status.HTTP_403_FORBIDDEN
                )
            task.restore()
            TaskHistory.objects.create(
                task=task,
                user=request.user,
                field_name='task',
                action='restored'
            )
            return Response(TaskDetailSerializer(task).data)
        except Task.DoesNotExist:
            return Response(
                {'error': 'Deleted task not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Get deleted tasks (trash)"
    )
    @action(detail=False, methods=['get'])
    def trash(self, request):
        """Get soft-deleted tasks."""
        tasks = Task.all_objects.filter(
            owner=request.user,
            is_deleted=True
        )
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Perform bulk actions on multiple tasks",
        request_body=BulkTaskActionSerializer
    )
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on multiple tasks."""
        serializer = BulkTaskActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        task_ids = serializer.validated_data['task_ids']
        action_type = serializer.validated_data['action']
        value = serializer.validated_data.get('value', '')
        
        tasks = Task.objects.filter(
            id__in=task_ids,
            owner=request.user
        )
        
        count = 0
        if action_type == 'complete':
            for task in tasks:
                task.complete()
                count += 1
        elif action_type == 'delete':
            count = tasks.count()
            for task in tasks:
                task.delete()
        elif action_type == 'change_status':
            count = tasks.update(status=value)
        elif action_type == 'change_priority':
            count = tasks.update(priority=value)
        
        return Response({
            'message': f'Action {action_type} performed on {count} tasks'
        })

    @swagger_auto_schema(
        operation_description="Get task history/audit log"
    )
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get task history."""
        task = self.get_object()
        history = TaskHistory.objects.filter(task=task)
        serializer = TaskHistorySerializer(history, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing task comments.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        if task_id:
            return Comment.objects.filter(task_id=task_id)
        return Comment.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        comment = serializer.save()
        # Create notification for task owner and mentioned users
        from apps.notifications.models import Notification
        task = comment.task
        
        # Notify task owner
        if task.owner != self.request.user:
            Notification.objects.create(
                recipient=task.owner,
                sender=self.request.user,
                notification_type='comment_added',
                title='New comment on your task',
                message=f'{self.request.user.full_name} commented on "{task.title}"',
                task=task,
                comment=comment
            )


class TaskAttachmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing task attachments.
    """
    serializer_class = TaskAttachmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        if task_id:
            return TaskAttachment.objects.filter(task_id=task_id)
        return TaskAttachment.objects.filter(uploaded_by=self.request.user)

    def perform_create(self, serializer):
        attachment = serializer.save()
        # Update attachment count
        attachment.task.attachments_count = attachment.task.attachments.count()
        attachment.task.save(update_fields=['attachments_count'])
