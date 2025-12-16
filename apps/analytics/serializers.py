"""
Serializers for the Analytics app.
"""
from rest_framework import serializers
from .models import DailyTaskStats, TeamStats, ProductivityReport, CategoryStats


class DailyTaskStatsSerializer(serializers.ModelSerializer):
    """
    Serializer for daily task statistics.
    """
    class Meta:
        model = DailyTaskStats
        fields = [
            'id', 'date', 'tasks_created', 'tasks_completed',
            'tasks_overdue', 'tasks_pending', 'tasks_in_progress',
            'total_hours_logged', 'comments_added',
            'tasks_assigned_to_others', 'tasks_received'
        ]


class TeamStatsSerializer(serializers.ModelSerializer):
    """
    Serializer for team statistics.
    """
    class Meta:
        model = TeamStats
        fields = [
            'id', 'date', 'team_size', 'total_tasks',
            'completed_tasks', 'overdue_tasks',
            'completion_rate', 'on_time_rate', 'average_completion_time'
        ]


class ProductivityReportSerializer(serializers.ModelSerializer):
    """
    Serializer for productivity reports.
    """
    class Meta:
        model = ProductivityReport
        fields = [
            'id', 'report_type', 'start_date', 'end_date',
            'summary', 'total_tasks_completed', 'total_hours_worked',
            'productivity_score', 'tasks_by_category',
            'tasks_by_priority', 'completion_trend', 'created_at'
        ]


class CategoryStatsSerializer(serializers.ModelSerializer):
    """
    Serializer for category statistics.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = CategoryStats
        fields = [
            'id', 'category', 'category_name', 'date',
            'total_tasks', 'completed_tasks', 'pending_tasks',
            'overdue_tasks', 'average_completion_time'
        ]


class DashboardSummarySerializer(serializers.Serializer):
    """
    Serializer for dashboard summary data.
    """
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    pending_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    in_progress_tasks = serializers.IntegerField()
    
    completion_rate = serializers.FloatField()
    tasks_due_today = serializers.IntegerField()
    tasks_due_this_week = serializers.IntegerField()
    
    # Recent activity
    tasks_completed_today = serializers.IntegerField()
    tasks_created_today = serializers.IntegerField()
    
    # Priority breakdown
    urgent_tasks = serializers.IntegerField()
    high_priority_tasks = serializers.IntegerField()
    medium_priority_tasks = serializers.IntegerField()
    low_priority_tasks = serializers.IntegerField()


class TaskTrendSerializer(serializers.Serializer):
    """
    Serializer for task trend data.
    """
    date = serializers.DateField()
    created = serializers.IntegerField()
    completed = serializers.IntegerField()


class AnalyticsFilterSerializer(serializers.Serializer):
    """
    Serializer for analytics filter parameters.
    """
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    period = serializers.ChoiceField(
        choices=['today', 'week', 'month', 'quarter', 'year'],
        required=False,
        default='month'
    )
    category_id = serializers.IntegerField(required=False)
    user_id = serializers.IntegerField(required=False)
