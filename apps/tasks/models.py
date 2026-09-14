"""
Task models with categories, tags, comments, and collaboration features.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from core.models import SoftDeleteModel, TimeStampedModel


class Category(TimeStampedModel):
    """
    Category for organizing tasks.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3498db')  # Hex color
    icon = models.CharField(max_length=50, blank=True)  # Icon name/class
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['name', 'owner'], name='unique_category_owner')
        ]

    def __str__(self):
        return self.name


class Tag(TimeStampedModel):
    """
    Tags for labeling and filtering tasks.
    """
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#9b59b6')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tags'
    )

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['name', 'owner'], name='unique_tag_owner')
        ]

    def __str__(self):
        return self.name


class Task(SoftDeleteModel):
    """
    Main Task model with full CRUD and soft-delete support.
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    RECURRENCE_CHOICES = [
        ('none', 'None'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    # Basic info
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Dates
    due_date = models.DateTimeField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Progress
    progress = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )  # 0-100
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Relationships
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_tasks'
    )
    assigned_to = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_tasks',
        blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    tags = models.ManyToManyField(Tag, related_name='tasks', blank=True)
    
    # Parent task for subtasks
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtasks'
    )
    
    # Recurrence
    is_recurring = models.BooleanField(default=False, db_index=True)
    recurrence_pattern = models.CharField(
        max_length=20,
        choices=RECURRENCE_CHOICES,
        default='none'
    )
    recurrence_end_date = models.DateTimeField(null=True, blank=True)
    # FIX: idempotencia recurrentes + overdue (evita duplicados si Beat corre 2x).
    last_recurrence_at = models.DateTimeField(null=True, blank=True)
    overdue_notified_at = models.DateTimeField(null=True, blank=True)
    
    # Attachments count (actual files stored in TaskAttachment)
    attachments_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _('task')
        verbose_name_plural = _('tasks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['due_date']),
            models.Index(fields=['owner']),
            # FIX: toda query filtra is_deleted; compuestos para dashboard/overdue.
            models.Index(fields=['is_deleted', 'status', 'due_date']),
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['is_recurring', 'status']),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        # FIX: evita parent circular / auto-referencia -> recursión infinita.
        if self.parent_id:
            if self.parent_id == getattr(self, 'id', None):
                raise ValidationError({'parent': 'A task cannot be its own parent.'})
            # Camina ancestros (máx 20 niveles para no escanear infinito).
            ancestor = self.parent
            for _ in range(20):
                if ancestor is None:
                    break
                if ancestor.id == getattr(self, 'id', None):
                    raise ValidationError({'parent': 'Circular parent detected.'})
                ancestor = ancestor.parent
        if self.start_date and self.due_date and self.due_date < self.start_date:
            raise ValidationError({'due_date': 'due_date must be >= start_date.'})
        if self.due_date and self.recurrence_end_date and self.recurrence_end_date < self.due_date:
            raise ValidationError({'recurrence_end_date': 'Must be >= due_date.'})

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.due_date
        return False

    @property
    def subtask_count(self):
        return self.subtasks.count()

    @property
    def completed_subtasks_count(self):
        return self.subtasks.filter(status='completed').count()

    def complete(self):
        """Mark task as completed (idempotente, atómico)."""
        from django.utils import timezone
        if self.status == 'completed':
            return
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress = 100
        self.save(update_fields=['status', 'completed_at', 'progress', 'updated_at'])


class TaskAttachment(TimeStampedModel):
    """
    File attachments for tasks.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)  # Size in bytes
    mime_type = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_attachments'
    )

    class Meta:
        verbose_name = _('task attachment')
        verbose_name_plural = _('task attachments')
        ordering = ['-created_at']

    def __str__(self):
        return self.filename


class Comment(TimeStampedModel):
    """
    Comments on tasks with mention support.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_comments'
    )
    content = models.TextField()
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='mentioned_in_comments',
        blank=True
    )
    is_edited = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.email} on {self.task.title}"

    def save(self, *args, **kwargs):
        """Extract and save mentions on save. FIX: matching real por email/handle."""
        super().save(*args, **kwargs)
        from core.utils import extract_mentions
        from apps.users.models import User
        from django.db.models import Q

        mentioned = extract_mentions(self.content)
        if not mentioned:
            if self.pk and self.mentions.exists():
                self.mentions.clear()
            return
        q = Q()
        for username in mentioned:
            # username puede ser handle, first_name o prefijo de email.
            q |= Q(email__iexact=username)
            q |= Q(email__istartswith=f"{username}@")
            q |= Q(first_name__iexact=username)
        self.mentions.set(User.objects.filter(q).distinct())


class TaskHistory(TimeStampedModel):
    """
    Audit log for task changes.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_changes'
    )
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    action = models.CharField(max_length=50)  # created, updated, deleted, restored

    class Meta:
        verbose_name = _('task history')
        verbose_name_plural = _('task histories')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task.title} - {self.action} by {self.user.email}"
