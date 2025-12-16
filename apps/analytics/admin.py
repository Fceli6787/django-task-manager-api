"""
Admin configuration for the Analytics app.
"""
from django.contrib import admin
from .models import DailyTaskStats, TeamStats, ProductivityReport, CategoryStats


@admin.register(DailyTaskStats)
class DailyTaskStatsAdmin(admin.ModelAdmin):
    """Admin configuration for DailyTaskStats model."""
    
    list_display = (
        'user', 'date', 'tasks_created', 'tasks_completed',
        'tasks_overdue', 'total_hours_logged'
    )
    list_filter = ('date',)
    search_fields = ('user__email',)
    ordering = ('-date',)
    date_hierarchy = 'date'
    
    readonly_fields = (
        'user', 'date', 'tasks_created', 'tasks_completed',
        'tasks_overdue', 'tasks_pending', 'tasks_in_progress',
        'total_hours_logged', 'comments_added',
        'tasks_assigned_to_others', 'tasks_received'
    )


@admin.register(TeamStats)
class TeamStatsAdmin(admin.ModelAdmin):
    """Admin configuration for TeamStats model."""
    
    list_display = (
        'manager', 'date', 'team_size', 'total_tasks',
        'completed_tasks', 'completion_rate'
    )
    list_filter = ('date',)
    search_fields = ('manager__email',)
    ordering = ('-date',)
    date_hierarchy = 'date'


@admin.register(ProductivityReport)
class ProductivityReportAdmin(admin.ModelAdmin):
    """Admin configuration for ProductivityReport model."""
    
    list_display = (
        'user', 'report_type', 'start_date', 'end_date',
        'total_tasks_completed', 'productivity_score'
    )
    list_filter = ('report_type', 'start_date')
    search_fields = ('user__email',)
    ordering = ('-end_date',)
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CategoryStats)
class CategoryStatsAdmin(admin.ModelAdmin):
    """Admin configuration for CategoryStats model."""
    
    list_display = (
        'category', 'date', 'total_tasks', 'completed_tasks',
        'overdue_tasks', 'average_completion_time'
    )
    list_filter = ('date', 'category')
    search_fields = ('category__name',)
    ordering = ('-date',)
    date_hierarchy = 'date'
