"""
Django Filter classes for the Tasks app.
"""
import django_filters
from .models import Task


class TaskFilter(django_filters.FilterSet):
    """
    Filter class for Task model.
    """
    title = django_filters.CharFilter(lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=Task.STATUS_CHOICES)
    priority = django_filters.ChoiceFilter(choices=Task.PRIORITY_CHOICES)
    
    category = django_filters.NumberFilter(field_name='category__id')
    category_name = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    
    tags = django_filters.NumberFilter(field_name='tags__id')
    tag_name = django_filters.CharFilter(field_name='tags__name', lookup_expr='icontains')
    
    owner = django_filters.NumberFilter()
    assigned_to = django_filters.NumberFilter(field_name='assigned_to__id')
    
    # Date filters
    due_date = django_filters.DateFilter()
    due_date_gte = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='gte')
    due_date_lte = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='lte')
    
    created_at_gte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_lte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Progress filters
    progress_gte = django_filters.NumberFilter(field_name='progress', lookup_expr='gte')
    progress_lte = django_filters.NumberFilter(field_name='progress', lookup_expr='lte')
    
    # Boolean filters
    is_recurring = django_filters.BooleanFilter()
    is_overdue = django_filters.BooleanFilter(method='filter_overdue')
    has_subtasks = django_filters.BooleanFilter(method='filter_has_subtasks')
    
    # Parent task filter
    parent = django_filters.NumberFilter()
    is_subtask = django_filters.BooleanFilter(method='filter_is_subtask')

    class Meta:
        model = Task
        fields = [
            'title', 'status', 'priority', 'category', 'category_name',
            'tags', 'tag_name', 'owner', 'assigned_to', 'due_date',
            'due_date_gte', 'due_date_lte', 'created_at_gte', 'created_at_lte',
            'progress_gte', 'progress_lte', 'is_recurring', 'is_overdue',
            'has_subtasks', 'parent', 'is_subtask'
        ]

    def filter_overdue(self, queryset, name, value):
        from django.utils import timezone
        now = timezone.now()
        if value:
            return queryset.filter(
                due_date__lt=now,
                status__in=['pending', 'in_progress', 'on_hold']
            )
        return queryset.filter(due_date__gte=now)

    def filter_has_subtasks(self, queryset, name, value):
        if value:
            return queryset.filter(subtasks__isnull=False).distinct()
        return queryset.filter(subtasks__isnull=True)

    def filter_is_subtask(self, queryset, name, value):
        if value:
            return queryset.filter(parent__isnull=False)
        return queryset.filter(parent__isnull=True)
