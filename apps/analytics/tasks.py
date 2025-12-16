"""
Celery tasks for the Analytics app.
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta


@shared_task
def generate_daily_stats():
    """
    Generate daily statistics for all users.
    """
    from apps.users.models import User
    from apps.tasks.models import Task
    from apps.analytics.models import DailyTaskStats
    
    yesterday = timezone.now().date() - timedelta(days=1)
    
    stats_created = 0
    
    for user in User.objects.filter(is_active=True):
        # Get user's tasks
        user_tasks = Task.all_objects.filter(
            Q(owner=user) | Q(assigned_to=user)
        ).distinct()
        
        # Calculate daily stats
        stats, created = DailyTaskStats.objects.update_or_create(
            user=user,
            date=yesterday,
            defaults={
                'tasks_created': user_tasks.filter(created_at__date=yesterday).count(),
                'tasks_completed': user_tasks.filter(completed_at__date=yesterday).count(),
                'tasks_overdue': user_tasks.filter(
                    due_date__date__lt=yesterday,
                    status__in=['pending', 'in_progress', 'on_hold']
                ).count(),
                'tasks_pending': user_tasks.filter(status='pending').count(),
                'tasks_in_progress': user_tasks.filter(status='in_progress').count(),
                'comments_added': user.task_comments.filter(created_at__date=yesterday).count(),
            }
        )
        
        if created:
            stats_created += 1
    
    return f'Generated {stats_created} daily stats records'


@shared_task
def generate_team_stats():
    """
    Generate team statistics for managers.
    """
    from apps.users.models import User
    from apps.tasks.models import Task
    from apps.analytics.models import TeamStats
    
    yesterday = timezone.now().date() - timedelta(days=1)
    
    managers = User.objects.filter(role__in=['admin', 'manager'])
    
    stats_created = 0
    
    for manager in managers:
        team_members = manager.get_team_members()
        
        if not team_members.exists():
            continue
        
        team_task_ids = Task.objects.filter(
            Q(owner__in=team_members) | Q(assigned_to__in=team_members)
        ).values_list('id', flat=True).distinct()
        
        team_tasks = Task.objects.filter(id__in=team_task_ids)
        
        total_tasks = team_tasks.count()
        completed_tasks = team_tasks.filter(status='completed').count()
        overdue_tasks = team_tasks.filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress', 'on_hold']
        ).count()
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        on_time = completed_tasks - team_tasks.filter(
            status='completed',
            completed_at__gt=models.F('due_date')
        ).count()
        on_time_rate = (on_time / completed_tasks * 100) if completed_tasks > 0 else 0
        
        stats, created = TeamStats.objects.update_or_create(
            manager=manager,
            date=yesterday,
            defaults={
                'team_size': team_members.count(),
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'overdue_tasks': overdue_tasks,
                'completion_rate': round(completion_rate, 2),
                'on_time_rate': round(on_time_rate, 2),
            }
        )
        
        if created:
            stats_created += 1
    
    return f'Generated {stats_created} team stats records'


@shared_task
def generate_weekly_report(user_id):
    """
    Generate weekly productivity report for a user.
    """
    from apps.users.models import User
    from apps.tasks.models import Task
    from apps.analytics.models import ProductivityReport
    from django.db.models.functions import TruncDate
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return 'User not found'
    
    now = timezone.now()
    end_date = now.date()
    start_date = end_date - timedelta(days=7)
    
    user_tasks = Task.all_objects.filter(
        Q(owner=user) | Q(assigned_to=user),
        created_at__date__gte=start_date
    ).distinct()
    
    # Calculate completion trend
    completion_trend = list(
        user_tasks.filter(
            completed_at__isnull=False
        ).annotate(
            date=TruncDate('completed_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date').values('date', 'count')
    )
    
    # Tasks by priority
    tasks_by_priority = dict(
        user_tasks.values('priority').annotate(
            count=Count('id')
        ).values_list('priority', 'count')
    )
    
    # Tasks by category
    tasks_by_category = dict(
        user_tasks.filter(category__isnull=False).values(
            'category__name'
        ).annotate(
            count=Count('id')
        ).values_list('category__name', 'count')
    )
    
    completed_count = user_tasks.filter(status='completed').count()
    total_count = user_tasks.count()
    
    report = ProductivityReport.objects.create(
        user=user,
        report_type='weekly',
        start_date=start_date,
        end_date=end_date,
        total_tasks_completed=completed_count,
        productivity_score=round((completed_count / total_count * 100) if total_count > 0 else 0, 2),
        summary={
            'period': f'{start_date} to {end_date}',
            'total_tasks': total_count,
            'completed_tasks': completed_count,
        },
        tasks_by_priority=tasks_by_priority,
        tasks_by_category=tasks_by_category,
        completion_trend=[
            {'date': str(item['date']), 'count': item['count']}
            for item in completion_trend
        ]
    )
    
    return f'Generated weekly report for {user.email}'
