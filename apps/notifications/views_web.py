"""Notificaciones + equipo en HTML. Email/push: flags + Celery ya existentes."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Notification


@login_required
def notif_list(request):
    notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:100]
    return render(request, 'web/notifications.html', {'notifs': notifs})


@login_required
def notif_read(request, pk):
    if request.method != 'POST': return redirect('web-notifs')
    n = get_object_or_404(Notification, pk=pk, recipient=request.user)
    n.mark_as_read(); return redirect('web-notifs')


@login_required
def notif_read_all(request):
    if request.method != 'POST': return redirect('web-notifs')
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
    return redirect('web-notifs')


@login_required
def team_view(request):
    if request.user.role not in ('admin', 'manager'): return redirect('/')
    members = request.user.get_team_members()
    rows = []
    for m in members:
        from apps.tasks.views import get_visible_tasks
        qs = get_visible_tasks(m)
        t, c = qs.count(), qs.filter(status='completed').count()
        rows.append({'name': m.full_name, 'email': m.email, 'total_tasks': t, 'completed_tasks': c,
                     'completion_rate': round(c / t * 100, 2) if t else 0,
                     'overdue_tasks': qs.filter(due_date__lt=timezone.now(), status__in=['pending', 'in_progress', 'on_hold']).count()})
    rows.sort(key=lambda x: x['completion_rate'], reverse=True)
    return render(request, 'web/team.html', {'members': rows, 'team_size': members.count()})


def unread_count_processor(request):
    if not request.user.is_authenticated: return {}
    return {'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()}
