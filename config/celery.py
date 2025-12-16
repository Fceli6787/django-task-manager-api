"""
Celery configuration for Task Manager API.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('task_manager')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


# Celery Beat Schedule for recurring tasks
app.conf.beat_schedule = {
    # Check for overdue tasks every hour
    'check-overdue-tasks': {
        'task': 'apps.tasks.tasks.check_overdue_tasks',
        'schedule': crontab(minute=0),  # Every hour
    },
    # Send task due reminders every day at 8 AM
    'send-due-reminders': {
        'task': 'apps.notifications.tasks.send_due_date_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    # Generate daily stats at midnight
    'generate-daily-stats': {
        'task': 'apps.analytics.tasks.generate_daily_stats',
        'schedule': crontab(hour=0, minute=5),
    },
    # Process recurring tasks daily
    'process-recurring-tasks': {
        'task': 'apps.tasks.tasks.process_recurring_tasks',
        'schedule': crontab(hour=0, minute=30),
    },
    # Clean old notifications weekly
    'clean-old-notifications': {
        'task': 'apps.notifications.tasks.clean_old_notifications',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday at 3 AM
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery connection."""
    print(f'Request: {self.request!r}')
