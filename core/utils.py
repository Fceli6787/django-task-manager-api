"""
Utility functions and helpers for the Task Manager API.
"""
import re
from django.utils import timezone
from datetime import timedelta


def extract_mentions(text):
    """
    Extract @mentions from text content.
    Returns a list of usernames mentioned.
    """
    if not text:
        return []
    pattern = r'@(\w+)'
    matches = re.findall(pattern, text)
    return list(set(matches))


def calculate_due_date(days_from_now=7):
    """
    Calculate a due date from the current time.
    """
    return timezone.now() + timedelta(days=days_from_now)


def get_priority_weight(priority):
    """
    Get numerical weight for priority sorting.
    """
    weights = {
        'urgent': 4,
        'high': 3,
        'medium': 2,
        'low': 1,
    }
    return weights.get(priority, 0)


def format_task_summary(task):
    """
    Format a task into a summary string.
    """
    return f"[{task.priority.upper()}] {task.title} - Due: {task.due_date}"


def is_task_overdue(task):
    """
    Check if a task is overdue.
    """
    if not task.due_date:
        return False
    if task.status == 'completed':
        return False
    return timezone.now() > task.due_date


def get_time_remaining(due_date):
    """
    Get the time remaining until a due date.
    Returns a human-readable string.
    """
    if not due_date:
        return "No due date"
    
    now = timezone.now()
    if now > due_date:
        diff = now - due_date
        return f"Overdue by {diff.days} days"
    
    diff = due_date - now
    if diff.days > 0:
        return f"{diff.days} days remaining"
    
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours} hours remaining"
    
    minutes = (diff.seconds % 3600) // 60
    return f"{minutes} minutes remaining"
