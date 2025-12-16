"""
URL patterns for the Analytics app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DashboardView, TaskTrendsView, TasksByStatusView,
    TasksByPriorityView, TasksByCategoryView,
    TeamAnalyticsView, ProductivityReportViewSet
)

router = DefaultRouter()
router.register(r'reports', ProductivityReportViewSet, basename='report')

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('trends/', TaskTrendsView.as_view(), name='task-trends'),
    path('by-status/', TasksByStatusView.as_view(), name='tasks-by-status'),
    path('by-priority/', TasksByPriorityView.as_view(), name='tasks-by-priority'),
    path('by-category/', TasksByCategoryView.as_view(), name='tasks-by-category'),
    path('team/', TeamAnalyticsView.as_view(), name='team-analytics'),
    path('', include(router.urls)),
]
