"""Dashboard HTML: mismos datos que /api/v1/analytics/dashboard/ + caché."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db import connection
from django.conf import settings
from django.db.models import Count, Q
from datetime import timedelta
from django.core.cache import cache
from apps.tasks.views import get_visible_tasks
from .models import ProductivityReport


def get_db_status():
    """Indica host:puerto MySQL y si conecta. No rompe si DB caída."""
    cfg = settings.DATABASES['default']
    host, port = cfg.get('HOST') or 'localhost', str(cfg.get('PORT') or '3306')
    try:
        with connection.cursor() as cur:
            cur.execute('SELECT 1')
            cur.fetchone()
        ok = True
    except Exception:
        ok = False
    return {'engine': cfg.get('ENGINE'), 'host': host, 'port': port, 'name': cfg.get('NAME'), 'ok': ok}


@login_required
def dashboard_view(request):
    key = f'dashboard:{request.user.id}:{request.user.role}'
    s = cache.get(key)
    if s is None:
        now = timezone.now(); today = now.date(); week = today + timedelta(days=7)
        tasks = get_visible_tasks(request.user)
        total = tasks.count()
        comp = tasks.filter(status='completed').count()
        s = {
            'total_tasks': total, 'completed_tasks': comp,
            'pending_tasks': tasks.filter(status='pending').count(),
            'in_progress_tasks': tasks.filter(status='in_progress').count(),
            'overdue_tasks': tasks.filter(due_date__lt=now, status__in=['pending', 'in_progress', 'on_hold']).count(),
            'completion_rate': round(comp / total * 100, 2) if total else 0,
            'tasks_due_today': tasks.filter(due_date__date=today, status__in=['pending', 'in_progress', 'on_hold']).count(),
            'tasks_due_this_week': tasks.filter(due_date__date__gte=today, due_date__date__lte=week, status__in=['pending', 'in_progress', 'on_hold']).count(),
            'urgent_tasks': tasks.filter(priority='urgent', status__in=['pending', 'in_progress']).count(),
            'high_priority_tasks': tasks.filter(priority='high', status__in=['pending', 'in_progress']).count(),
            'medium_priority_tasks': tasks.filter(priority='medium', status__in=['pending', 'in_progress']).count(),
            'low_priority_tasks': tasks.filter(priority='low', status__in=['pending', 'in_progress']).count(),
        }
        cache.set(key, s, 120)
    tasks = get_visible_tasks(request.user)
    by_status = list(tasks.values('status').annotate(count=Count('id')))
    by_priority = list(tasks.values('priority').annotate(count=Count('id')))
    return render(request, 'web/dashboard.html', {'s': s, 'by_status': by_status, 'by_priority': by_priority, 'db': get_db_status()})


@login_required
def generate_report(request):
    if request.method != 'POST': return redirect('/')
    end = timezone.now().date(); start = end - timedelta(days=7)
    tasks = get_visible_tasks(request.user).filter(created_at__date__gte=start)
    done = tasks.filter(status='completed').count()
    ProductivityReport.objects.create(user=request.user, report_type='weekly', start_date=start, end_date=end,
                                      total_tasks_completed=done, summary={'total_tasks': tasks.count(), 'completed': done})
    return redirect('/')
