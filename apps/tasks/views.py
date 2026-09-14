"""
Views for the Tasks app.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count
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


def get_visible_tasks(user, base_qs=None):
    """Fuente única RBAC + performance. Evita 4 variantes divergentes."""
    qs = base_qs if base_qs is not None else Task.objects.all()
    qs = qs.select_related('owner', 'category', 'parent').prefetch_related(
        'assigned_to', 'tags'
    ).annotate(
        assigned_count=Count('assigned_to', distinct=True),
        comments_count=Count('comments', distinct=True),
    )
    if getattr(user, 'role', None) == 'admin':
        return qs
    if getattr(user, 'role', None) == 'manager':
        team_ids = user.team_members.values_list('id', flat=True)
        return qs.filter(
            Q(owner=user) | Q(assigned_to=user) | Q(owner__in=team_ids)
        ).distinct()
    return qs.filter(Q(owner=user) | Q(assigned_to=user)).distinct()


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
        return get_visible_tasks(self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        elif self.action == 'create':
            return TaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        return TaskDetailSerializer

    def perform_create(self, serializer):
        task = serializer.save(owner=self.request.user)
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
        tasks = self.filter_queryset(self.get_queryset().filter(assigned_to=request.user))
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
        tasks = self.filter_queryset(self.get_queryset().filter(owner=request.user))
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
        """Get overdue tasks for current user (paginado)."""
        now = timezone.now()
        tasks = self.filter_queryset(self.get_queryset().filter(
            due_date__lt=now,
            status__in=['pending', 'in_progress', 'on_hold']
        ))
        page = self.paginate_queryset(tasks)
        if page is not None:
            return self.get_paginated_response(TaskListSerializer(page, many=True).data)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get tasks due today"
    )
    @action(detail=False, methods=['get'])
    def due_today(self, request):
        """Get tasks due today (paginado)."""
        today = timezone.now().date()
        tasks = self.filter_queryset(self.get_queryset().filter(
            due_date__date=today,
            status__in=['pending', 'in_progress', 'on_hold']
        ))
        page = self.paginate_queryset(tasks)
        if page is not None:
            return self.get_paginated_response(TaskListSerializer(page, many=True).data)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get tasks due this week"
    )
    @action(detail=False, methods=['get'])
    def due_this_week(self, request):
        """Get tasks due this week (paginado)."""
        from datetime import timedelta
        today = timezone.now().date()
        week_end = today + timedelta(days=7)
        tasks = self.filter_queryset(self.get_queryset().filter(
            due_date__date__gte=today,
            due_date__date__lte=week_end,
            status__in=['pending', 'in_progress', 'on_hold']
        ))
        page = self.paginate_queryset(tasks)
        if page is not None:
            return self.get_paginated_response(TaskListSerializer(page, many=True).data)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Mark task as completed"
    )
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as completed (idempotente, audita old real)."""
        task = self.get_object()
        old_status = task.status
        if old_status == 'completed':
            return Response(TaskDetailSerializer(task, context={'request': request}).data)
        task.complete()
        TaskHistory.objects.create(
            task=task,
            user=request.user,
            field_name='status',
            old_value=old_status,
            new_value='completed',
            action='updated'
        )
        return Response(TaskDetailSerializer(task, context={'request': request}).data)

    @swagger_auto_schema(
        operation_description="Restore a soft-deleted task"
    )
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore a soft-deleted task. No enumera existencia ajena."""
        # FIX: scope primero a visibles + trash propio/equipo para no filtrar por 403/404.
        visible_ids = set(self.get_queryset().values_list('id', flat=True))
        try:
            task = Task.all_objects.select_related('owner').get(pk=pk, is_deleted=True)
        except Task.DoesNotExist:
            return Response(
                {'error': 'Deleted task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        allowed = (
            task.id in visible_ids
            or task.owner_id == request.user.id
            or getattr(request.user, 'role', None) == 'admin'
        )
        if not allowed:
            # Mismo 404 para no revelar existencia (anti-enumeración).
            return Response(
                {'error': 'Deleted task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        task.restore()
        TaskHistory.objects.create(
            task=task,
            user=request.user,
            field_name='task',
            action='restored'
        )
        return Response(TaskDetailSerializer(task, context={'request': request}).data)

    @swagger_auto_schema(
        operation_description="Get deleted tasks (trash)"
    )
    @action(detail=False, methods=['get'])
    def trash(self, request):
        """Get soft-deleted tasks (paginado, respeta rol)."""
        base = Task.all_objects.select_related('owner', 'category').prefetch_related('assigned_to', 'tags').filter(is_deleted=True)
        if getattr(request.user, 'role', None) == 'admin':
            tasks = base
        elif getattr(request.user, 'role', None) == 'manager':
            team_ids = request.user.team_members.values_list('id', flat=True)
            tasks = base.filter(Q(owner=request.user) | Q(owner__in=team_ids))
        else:
            tasks = base.filter(owner=request.user)
        tasks = self.filter_queryset(tasks.order_by('-deleted_at'))
        page = self.paginate_queryset(tasks)
        if page is not None:
            return self.get_paginated_response(TaskListSerializer(page, many=True).data)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Perform bulk actions on multiple tasks",
        request_body=BulkTaskActionSerializer
    )
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on multiple tasks (atómico, validado)."""
        serializer = BulkTaskActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        task_ids = serializer.validated_data['task_ids']
        action_type = serializer.validated_data['action']
        value = serializer.validated_data.get('value', '')

        if action_type not in ('complete', 'delete', 'change_status', 'change_priority'):
            return Response(
                {'error': f'Action {action_type} not implemented. Use complete/delete/change_status/change_priority.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if action_type == 'change_status' and value not in dict(Task.STATUS_CHOICES):
            return Response({'error': 'Invalid status value.'}, status=status.HTTP_400_BAD_REQUEST)
        if action_type == 'change_priority' and value not in dict(Task.PRIORITY_CHOICES):
            return Response({'error': 'Invalid priority value.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(task_ids) > 500:
            return Response({'error': 'Max 500 task_ids per request.'}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            tasks = self.get_queryset().filter(id__in=task_ids).select_for_update()
            ids = list(tasks.values_list('id', flat=True))
            if not ids:
                return Response({'message': 'No tasks matched.', 'count': 0})
            count = 0
            now = timezone.now()
            if action_type == 'complete':
                count = tasks.exclude(status='completed').update(status='completed', progress=100, completed_at=now)
                TaskHistory.objects.bulk_create([
                    TaskHistory(task_id=tid, user=request.user, field_name='status', new_value='completed', action='updated')
                    for tid in ids
                ], ignore_conflicts=True)
            elif action_type == 'delete':
                count = tasks.update(is_deleted=True, deleted_at=now)
            elif action_type == 'change_status':
                # Si pasan a completed, fijar completed_at/progress también.
                if value == 'completed':
                    count = tasks.update(status=value, progress=100, completed_at=now)
                else:
                    count = tasks.update(status=value)
            elif action_type == 'change_priority':
                count = tasks.update(priority=value)
        
        return Response({
            'message': f'Action {action_type} performed on {count} tasks',
            'count': count
        })

    @swagger_auto_schema(
        operation_description="Get task history/audit log"
    )
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get task history (paginado)."""
        task = self.get_object()
        history = TaskHistory.objects.filter(task=task).order_by('-created_at')
        page = self.paginate_queryset(history)
        if page is not None:
            return self.get_paginated_response(TaskHistorySerializer(page, many=True).data)
        serializer = TaskHistorySerializer(history, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing task comments.
    Permiso: IsAuthenticated + visibilidad de tarea (no CanManageTasks directo,
    porque Comment no tiene owner sino author).
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        qs = Comment.objects.select_related('author', 'task').prefetch_related('replies')
        if task_id:
            # FIX: solo si la tarea es visible para el usuario.
            visible = get_visible_tasks(self.request.user).filter(id=task_id).exists()
            if not visible and getattr(self.request.user, 'role', None) != 'admin':
                return Comment.objects.none()
            return qs.filter(task_id=task_id)
        # Sin task_pk: solo propios para no exponer todos.
        return qs.filter(author=self.request.user)

    def _get_accessible_task(self, task_id):
        task = get_visible_tasks(self.request.user).filter(id=task_id).first()
        return task

    def perform_create(self, serializer):
        # FIX: verifica acceso a la tarea antes de comentar.
        task = serializer.validated_data.get('task')
        if task is None or self._get_accessible_task(task.id) is None:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You cannot comment on this task.')
        comment = serializer.save(author=self.request.user)
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
    Permiso: IsAuthenticated + visibilidad de tarea (igual que comments).
    """
    serializer_class = TaskAttachmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        qs = TaskAttachment.objects.select_related('task', 'uploaded_by')
        if task_id:
            visible = get_visible_tasks(self.request.user).filter(id=task_id).exists()
            if not visible and getattr(self.request.user, 'role', None) != 'admin':
                return TaskAttachment.objects.none()
            return qs.filter(task_id=task_id)
        return qs.filter(uploaded_by=self.request.user)

    def perform_create(self, serializer):
        from rest_framework.exceptions import PermissionDenied
        from django.db.models import F
        task = serializer.validated_data.get('task')
        if task is None or get_visible_tasks(self.request.user).filter(id=task.id).first() is None:
            raise PermissionDenied('You cannot attach files to this task.')
        attachment = serializer.save(uploaded_by=self.request.user)
        # FIX atómico: evita race en conteo concurrente.
        Task.objects.filter(id=attachment.task_id).update(attachments_count=F('attachments_count') + 1)
