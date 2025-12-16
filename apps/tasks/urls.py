"""
URL patterns for the Tasks app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from .views import (
    TaskViewSet, CategoryViewSet, TagViewSet,
    CommentViewSet, TaskAttachmentViewSet
)

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')

# Nested routers for task-related resources
tasks_router = nested_routers.NestedDefaultRouter(router, r'tasks', lookup='task')
tasks_router.register(r'comments', CommentViewSet, basename='task-comments')
tasks_router.register(r'attachments', TaskAttachmentViewSet, basename='task-attachments')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(tasks_router.urls)),
]
