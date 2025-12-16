"""
Views for the Analytics app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Count, Q, Avg
from django.db.models.functions import TruncDate
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.permissions import IsManagerOrAdmin
from core.pagination import StandardResultsSetPagination
from apps.tasks.models import Task
from .models import DailyTaskStats, TeamStats, ProductivityReport, CategoryStats
from .serializers import (
    DailyTaskStatsSerializer, TeamStatsSerializer,
    ProductivityReportSerializer, CategoryStatsSerializer,
    DashboardSummarySerializer, TaskTrendSerializer, AnalyticsFilterSerializer
)


class DashboardView(APIView):
    """
    Dashboard API with summary statistics.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get dashboard summary statistics",
        responses={200: DashboardSummarySerializer}
    )
    def get(self, request):
        """Get dashboard summary for current user."""
        user = request.user
        now = timezone.now()
        today = now.date()
        week_from_now = today + timedelta(days=7)
        
        # Get user's tasks
        if user.role == 'admin':
            tasks = Task.objects.all()
        elif user.role == 'manager':
            team_ids = user.team_members.values_list('id', flat=True)
            tasks = Task.objects.filter(
                Q(owner=user) | Q(assigned_to=user) | Q(owner__in=team_ids)
            )
        else:
            tasks = Task.objects.filter(Q(owner=user) | Q(assigned_to=user))
        
        tasks = tasks.distinct()
        
        # Calculate stats
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='completed').count()
        pending_tasks = tasks.filter(status='pending').count()
        in_progress_tasks = tasks.filter(status='in_progress').count()
        overdue_tasks = tasks.filter(
            due_date__lt=now,
            status__in=['pending', 'in_progress', 'on_hold']
        ).count()
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        tasks_due_today = tasks.filter(
            due_date__date=today,
            status__in=['pending', 'in_progress', 'on_hold']
        ).count()
        
        tasks_due_this_week = tasks.filter(
            due_date__date__gte=today,
            due_date__date__lte=week_from_now,
            status__in=['pending', 'in_progress', 'on_hold']
        ).count()
        
        # Today's activity
        tasks_completed_today = tasks.filter(
            completed_at__date=today
        ).count()
        tasks_created_today = tasks.filter(
            created_at__date=today
        ).count()
        
        # Priority breakdown
        urgent_tasks = tasks.filter(priority='urgent', status__in=['pending', 'in_progress']).count()
        high_priority_tasks = tasks.filter(priority='high', status__in=['pending', 'in_progress']).count()
        medium_priority_tasks = tasks.filter(priority='medium', status__in=['pending', 'in_progress']).count()
        low_priority_tasks = tasks.filter(priority='low', status__in=['pending', 'in_progress']).count()
        
        data = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'overdue_tasks': overdue_tasks,
            'in_progress_tasks': in_progress_tasks,
            'completion_rate': round(completion_rate, 2),
            'tasks_due_today': tasks_due_today,
            'tasks_due_this_week': tasks_due_this_week,
            'tasks_completed_today': tasks_completed_today,
            'tasks_created_today': tasks_created_today,
            'urgent_tasks': urgent_tasks,
            'high_priority_tasks': high_priority_tasks,
            'medium_priority_tasks': medium_priority_tasks,
            'low_priority_tasks': low_priority_tasks,
        }
        
        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)


class TaskTrendsView(APIView):
    """
    Task trends and charts data.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get task creation and completion trends",
        manual_parameters=[
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                            description='Number of days to look back (default: 30)')
        ]
    )
    def get(self, request):
        """Get task trends for charts."""
        user = request.user
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        # Get user's tasks
        if user.role == 'admin':
            tasks = Task.all_objects.all()
        else:
            tasks = Task.all_objects.filter(Q(owner=user) | Q(assigned_to=user))
        
        # Daily creation counts
        created_by_day = tasks.filter(
            created_at__date__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Daily completion counts
        completed_by_day = tasks.filter(
            completed_at__date__gte=start_date
        ).annotate(
            date=TruncDate('completed_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Build response data
        created_dict = {item['date']: item['count'] for item in created_by_day}
        completed_dict = {item['date']: item['count'] for item in completed_by_day}
        
        trends = []
        current_date = start_date
        while current_date <= timezone.now().date():
            trends.append({
                'date': current_date,
                'created': created_dict.get(current_date, 0),
                'completed': completed_dict.get(current_date, 0)
            })
            current_date += timedelta(days=1)
        
        return Response(trends)


class TasksByStatusView(APIView):
    """
    Tasks grouped by status for pie charts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get tasks grouped by status."""
        user = request.user
        
        if user.role == 'admin':
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(Q(owner=user) | Q(assigned_to=user))
        
        status_counts = tasks.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        return Response(list(status_counts))


class TasksByPriorityView(APIView):
    """
    Tasks grouped by priority.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get tasks grouped by priority."""
        user = request.user
        
        if user.role == 'admin':
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(Q(owner=user) | Q(assigned_to=user))
        
        priority_counts = tasks.values('priority').annotate(
            count=Count('id')
        ).order_by('priority')
        
        return Response(list(priority_counts))


class TasksByCategoryView(APIView):
    """
    Tasks grouped by category.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get tasks grouped by category."""
        user = request.user
        
        if user.role == 'admin':
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(Q(owner=user) | Q(assigned_to=user))
        
        category_counts = tasks.values(
            'category__id', 'category__name', 'category__color'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response(list(category_counts))


class TeamAnalyticsView(APIView):
    """
    Team analytics for managers.
    """
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    @swagger_auto_schema(
        operation_description="Get team analytics (managers only)"
    )
    def get(self, request):
        """Get team analytics for managers."""
        user = request.user
        team_members = user.get_team_members()
        
        if not team_members.exists():
            return Response({
                'error': 'No team members found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        team_stats = []
        for member in team_members:
            member_tasks = Task.objects.filter(Q(owner=member) | Q(assigned_to=member)).distinct()
            total = member_tasks.count()
            completed = member_tasks.filter(status='completed').count()
            overdue = member_tasks.filter(
                due_date__lt=timezone.now(),
                status__in=['pending', 'in_progress']
            ).count()
            
            team_stats.append({
                'user_id': member.id,
                'name': member.full_name,
                'email': member.email,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': round((completed / total * 100) if total > 0 else 0, 2),
                'overdue_tasks': overdue
            })
        
        # Sort by completion rate
        team_stats.sort(key=lambda x: x['completion_rate'], reverse=True)
        
        return Response({
            'team_size': team_members.count(),
            'members': team_stats
        })


class ProductivityReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing productivity reports.
    """
    serializer_class = ProductivityReportSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ProductivityReport.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Generate a new productivity report"
    )
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new productivity report."""
        report_type = request.data.get('report_type', 'weekly')
        user = request.user
        
        if report_type == 'weekly':
            days = 7
        else:
            days = 30
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        tasks = Task.objects.filter(
            Q(owner=user) | Q(assigned_to=user),
            created_at__date__gte=start_date
        ).distinct()
        
        completed_tasks = tasks.filter(status='completed').count()
        
        # Create report
        report = ProductivityReport.objects.create(
            user=user,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            total_tasks_completed=completed_tasks,
            summary={
                'period': f'{start_date} to {end_date}',
                'total_tasks': tasks.count(),
                'completed': completed_tasks
            }
        )
        
        serializer = ProductivityReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
