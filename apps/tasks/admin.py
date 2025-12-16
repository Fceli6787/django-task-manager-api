"""
Admin configuration for the Tasks app.
"""
from django.contrib import admin
from .models import Task, Category, Tag, Comment, TaskAttachment, TaskHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model."""
    
    list_display = ('name', 'owner', 'color', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('name', 'owner__email')
    ordering = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin configuration for Tag model."""
    
    list_display = ('name', 'owner', 'color', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'owner__email')
    ordering = ('name',)


class CommentInline(admin.TabularInline):
    """Inline for comments in Task admin."""
    model = Comment
    extra = 0
    readonly_fields = ('author', 'created_at')


class AttachmentInline(admin.TabularInline):
    """Inline for attachments in Task admin."""
    model = TaskAttachment
    extra = 0
    readonly_fields = ('uploaded_by', 'file_size', 'mime_type', 'created_at')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin configuration for Task model."""
    
    list_display = ('title', 'owner', 'status', 'priority', 'due_date', 'is_deleted', 'created_at')
    list_filter = ('status', 'priority', 'is_deleted', 'is_recurring', 'category', 'created_at')
    search_fields = ('title', 'description', 'owner__email')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    filter_horizontal = ('assigned_to', 'tags')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'owner')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'progress')
        }),
        ('Dates', {
            'fields': ('start_date', 'due_date', 'completed_at')
        }),
        ('Organization', {
            'fields': ('category', 'tags', 'parent')
        }),
        ('Assignment', {
            'fields': ('assigned_to',)
        }),
        ('Time Tracking', {
            'fields': ('estimated_hours', 'actual_hours'),
            'classes': ('collapse',)
        }),
        ('Recurrence', {
            'fields': ('is_recurring', 'recurrence_pattern', 'recurrence_end_date'),
            'classes': ('collapse',)
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('completed_at', 'deleted_at', 'created_at', 'updated_at', 'attachments_count')
    
    inlines = [CommentInline, AttachmentInline]
    
    def get_queryset(self, request):
        """Include soft-deleted tasks in admin."""
        return Task.all_objects.all()


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin configuration for Comment model."""
    
    list_display = ('task', 'author', 'content_preview', 'is_edited', 'created_at')
    list_filter = ('is_edited', 'created_at')
    search_fields = ('content', 'task__title', 'author__email')
    ordering = ('-created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    """Admin configuration for TaskAttachment model."""
    
    list_display = ('filename', 'task', 'uploaded_by', 'file_size', 'created_at')
    list_filter = ('mime_type', 'created_at')
    search_fields = ('filename', 'task__title')
    ordering = ('-created_at',)


@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for TaskHistory model."""
    
    list_display = ('task', 'user', 'field_name', 'action', 'created_at')
    list_filter = ('action', 'field_name', 'created_at')
    search_fields = ('task__title', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('task', 'user', 'field_name', 'old_value', 'new_value', 'action', 'created_at')
