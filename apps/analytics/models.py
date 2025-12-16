"""
Analytics models for dashboard and reporting.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models import TimeStampedModel


class DailyTaskStats(TimeStampedModel):
    """
    Daily statistics for tasks per user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_stats'
    )
    date = models.DateField()
    
    # Task counts
    tasks_created = models.PositiveIntegerField(default=0)
    tasks_completed = models.PositiveIntegerField(default=0)
    tasks_overdue = models.PositiveIntegerField(default=0)
    tasks_pending = models.PositiveIntegerField(default=0)
    tasks_in_progress = models.PositiveIntegerField(default=0)
    
    # Time tracking
    total_hours_logged = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    # Comments and collaboration
    comments_added = models.PositiveIntegerField(default=0)
    tasks_assigned_to_others = models.PositiveIntegerField(default=0)
    tasks_received = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _('daily task statistics')
        verbose_name_plural = _('daily task statistics')
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"Stats for {self.user.email} on {self.date}"


class TeamStats(TimeStampedModel):
    """
    Team-level statistics (for managers).
    """
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_stats'
    )
    date = models.DateField()
    
    # Team metrics
    team_size = models.PositiveIntegerField(default=0)
    total_tasks = models.PositiveIntegerField(default=0)
    completed_tasks = models.PositiveIntegerField(default=0)
    overdue_tasks = models.PositiveIntegerField(default=0)
    
    # Performance
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    on_time_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    average_completion_time = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # Hours

    class Meta:
        verbose_name = _('team statistics')
        verbose_name_plural = _('team statistics')
        ordering = ['-date']
        unique_together = ['manager', 'date']

    def __str__(self):
        return f"Team stats for {self.manager.email} on {self.date}"


class ProductivityReport(TimeStampedModel):
    """
    Weekly/Monthly productivity reports.
    """
    REPORT_TYPES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='productivity_reports'
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Summary data
    summary = models.JSONField(default=dict)
    
    # Calculated metrics
    total_tasks_completed = models.PositiveIntegerField(default=0)
    total_hours_worked = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    productivity_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    
    # Trends
    tasks_by_category = models.JSONField(default=dict)
    tasks_by_priority = models.JSONField(default=dict)
    completion_trend = models.JSONField(default=list)  # Daily completion counts

    class Meta:
        verbose_name = _('productivity report')
        verbose_name_plural = _('productivity reports')
        ordering = ['-end_date']

    def __str__(self):
        return f"{self.report_type} report for {self.user.email}: {self.start_date} to {self.end_date}"


class CategoryStats(TimeStampedModel):
    """
    Statistics per category.
    """
    category = models.ForeignKey(
        'tasks.Category',
        on_delete=models.CASCADE,
        related_name='stats'
    )
    date = models.DateField()
    
    total_tasks = models.PositiveIntegerField(default=0)
    completed_tasks = models.PositiveIntegerField(default=0)
    pending_tasks = models.PositiveIntegerField(default=0)
    overdue_tasks = models.PositiveIntegerField(default=0)
    average_completion_time = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = _('category statistics')
        verbose_name_plural = _('category statistics')
        ordering = ['-date']
        unique_together = ['category', 'date']

    def __str__(self):
        return f"Stats for {self.category.name} on {self.date}"
