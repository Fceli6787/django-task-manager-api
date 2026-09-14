"""
Serializers for the Tasks app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Task, Category, Tag, Comment, TaskAttachment, TaskHistory

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for tags.
    """
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for categories.
    """
    tasks_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'color', 'icon',
            'is_default', 'tasks_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_tasks_count(self, obj):
        return obj.tasks.filter(is_deleted=False).count()

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments.
    """
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    author_avatar = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'task', 'author', 'author_name', 'author_avatar',
            'content', 'parent', 'is_edited', 'replies_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author', 'is_edited', 'created_at', 'updated_at']

    def get_author_avatar(self, obj):
        if obj.author.avatar:
            return obj.author.avatar.url
        return None

    def get_replies_count(self, obj):
        return obj.replies.count()

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class TaskAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for task attachments.
    """
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)

    class Meta:
        model = TaskAttachment
        fields = [
            'id', 'task', 'file', 'filename', 'file_size',
            'mime_type', 'uploaded_by', 'uploaded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'file_size', 'mime_type', 'created_at']

    def validate_file(self, value):
        # FIX: alinear con FILE_UPLOAD_MAX (5MB) y bloquear ejecutables.
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(f'File too large. Max {max_size} bytes.')
        blocked = ('.exe', '.bat', '.sh', '.msi', '.dll', '.ps1')
        if value.name.lower().endswith(blocked):
            raise serializers.ValidationError('File type not allowed.')
        return value

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        file = validated_data['file']
        validated_data['filename'] = file.name
        validated_data['file_size'] = file.size
        validated_data['mime_type'] = file.content_type
        return super().create(validated_data)


class TaskHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for task history.
    """
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = TaskHistory
        fields = [
            'id', 'task', 'user', 'user_name', 'field_name',
            'old_value', 'new_value', 'action', 'created_at'
        ]


class TaskListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for task lists.
    Usa anotaciones assigned_count/comments_count si vienen del queryset,
    si no hace fallback a count() (subtareas, trash sin annotar).
    """
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    assigned_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'priority', 'due_date',
            'owner', 'owner_name', 'category', 'category_name',
            'assigned_count', 'comments_count', 'tags', 'progress',
            'is_overdue', 'subtask_count', 'created_at'
        ]

    def get_assigned_count(self, obj):
        if hasattr(obj, 'assigned_count') and isinstance(obj.assigned_count, int):
            return obj.assigned_count
        return obj.assigned_to.count()

    def get_comments_count(self, obj):
        if hasattr(obj, 'comments_count') and isinstance(obj.comments_count, int):
            return obj.comments_count
        return obj.comments.count()


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for task details.
    NOTA: comments/attachments se exponen paginados vía nested routes,
    aquí solo conteos para evitar OOM con 10k comentarios.
    """
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='tags',
        write_only=True,
        many=True,
        required=False
    )
    assigned_to_details = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    attachments_count_display = serializers.IntegerField(source='attachments_count', read_only=True)
    subtasks = serializers.SerializerMethodField()
    parent_title = serializers.CharField(source='parent.title', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'due_date', 'start_date', 'completed_at', 'progress',
            'estimated_hours', 'actual_hours',
            'owner', 'owner_name', 'assigned_to', 'assigned_to_details',
            'category', 'category_id', 'tags', 'tag_ids',
            'parent', 'parent_title', 'subtasks',
            'is_recurring', 'recurrence_pattern', 'recurrence_end_date',
            'attachments_count', 'attachments_count_display', 'comments_count',
            'is_overdue', 'subtask_count', 'completed_subtasks_count',
            'created_at', 'updated_at', 'is_deleted', 'deleted_at'
        ]
        read_only_fields = [
            'id', 'owner', 'completed_at', 'attachments_count',
            'created_at', 'updated_at', 'is_deleted', 'deleted_at'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FIX IDOR: solo categorías/tags propios.
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['category_id'].queryset = Category.objects.filter(owner=request.user)
            self.fields['tag_ids'].child_relation.queryset = Tag.objects.filter(owner=request.user)

    def get_assigned_to_details(self, obj):
        from apps.users.serializers import UserListSerializer
        return UserListSerializer(obj.assigned_to.all(), many=True).data

    def get_comments_count(self, obj):
        if hasattr(obj, 'comments_count') and isinstance(obj.comments_count, int):
            return obj.comments_count
        return obj.comments.count()

    def get_subtasks(self, obj):
        subtasks = obj.subtasks.filter(is_deleted=False)[:20]
        return TaskListSerializer(subtasks, many=True).data


class TaskCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating tasks.
    """
    id = serializers.IntegerField(read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='tags',
        write_only=True,
        many=True,
        required=False
    )
    assigned_to_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        write_only=True,
        many=True,
        required=False
    )

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'due_date', 'start_date', 'category',
            'tag_ids', 'assigned_to_ids', 'parent',
            'estimated_hours', 'is_recurring', 'recurrence_pattern',
            'recurrence_end_date'
        ]
        read_only_fields = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['category'].queryset = Category.objects.filter(owner=request.user)
            self.fields['tag_ids'].child_relation.queryset = Tag.objects.filter(owner=request.user)
            if 'parent' in self.fields:
                self.fields['parent'].queryset = Task.objects.filter(owner=request.user)

    def validate(self, attrs):
        if attrs.get('start_date') and attrs.get('due_date'):
            if attrs['due_date'] < attrs['start_date']:
                raise serializers.ValidationError({'due_date': 'due_date must be >= start_date.'})
        parent = attrs.get('parent')
        if parent and parent.is_deleted:
            raise serializers.ValidationError({'parent': 'Parent is deleted.'})
        return attrs

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        assigned_to = validated_data.pop('assigned_to', [])
        validated_data['owner'] = self.context['request'].user
        
        task = Task.objects.create(**validated_data)
        task.tags.set(tags)
        task.assigned_to.set(assigned_to)
        
        return task


class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating tasks.
    """
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='tags',
        write_only=True,
        many=True,
        required=False
    )
    assigned_to_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        write_only=True,
        many=True,
        required=False
    )

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority',
            'due_date', 'start_date', 'progress', 'category',
            'tag_ids', 'assigned_to_ids', 'parent',
            'estimated_hours', 'actual_hours', 'is_recurring',
            'recurrence_pattern', 'recurrence_end_date'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['category'].queryset = Category.objects.filter(owner=request.user)
            self.fields['tag_ids'].child_relation.queryset = Tag.objects.filter(owner=request.user)

    def validate_progress(self, value):
        if value is not None and not 0 <= value <= 100:
            raise serializers.ValidationError('Progress must be 0-100.')
        return value

    def validate(self, attrs):
        # Asignados no pueden editar campos salvo status (defensa en profundidad).
        request = self.context.get('request')
        instance = getattr(self, 'instance', None)
        if request and instance and instance.owner != request.user and getattr(request.user, 'role', None) not in ('admin', 'manager'):
            allowed = {'status'}
            extra = set(attrs.keys()) - allowed
            if extra:
                raise serializers.ValidationError('Assigned users can only update status. Use dedicated endpoint.')
        return attrs

    def update(self, instance, validated_data):
        # FIX: capturar old_status ANTES de mutar (antes siempre False).
        old_status = instance.status
        tags = validated_data.pop('tags', None)
        assigned_to = validated_data.pop('assigned_to', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Handle completion
        if validated_data.get('status') == 'completed' and old_status != 'completed':
            from django.utils import timezone
            instance.completed_at = timezone.now()
            instance.progress = 100
        
        instance.full_clean(exclude=['owner', 'created_at', 'updated_at'])
        instance.save()
        
        if tags is not None:
            instance.tags.set(tags)
        if assigned_to is not None:
            instance.assigned_to.set(assigned_to)
        
        return instance


class BulkTaskActionSerializer(serializers.Serializer):
    """
    Serializer for bulk task operations.
    """
    task_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    action = serializers.ChoiceField(choices=[
        'complete', 'delete', 'restore', 'archive',
        'change_priority', 'change_status', 'assign'
    ])
    value = serializers.CharField(required=False, allow_blank=True)
