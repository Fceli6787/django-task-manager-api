"""
URL configuration for Task Manager API project.

Includes all API endpoints and Swagger documentation.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from apps.users.views_web import register_view
from apps.tasks.views_web import (
    task_list, task_detail, task_create, task_edit, task_delete,
    task_complete, task_comment, task_attach, categories_view,
    category_create, category_delete, tag_create, tag_delete,
)
from apps.tasks.models import Category, Tag
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from apps.analytics.views_web import dashboard_view, generate_report
from apps.notifications.views_web import notif_list, notif_read, notif_read_all, team_view


# Swagger/OpenAPI Schema
schema_view = get_schema_view(
    openapi.Info(
        title="Task Manager API",
        default_version='v1',
        description="""
# Task Manager API Documentation

A comprehensive RESTful API for managing tasks with the following features:

## Features
- **Authentication**: JWT-based authentication with refresh tokens
- **Tasks**: Full CRUD operations with soft-delete support
- **Categories & Tags**: Organize tasks with categories and tags
- **Comments**: Add comments to tasks with @mention support
- **Attachments**: Upload files to tasks
- **Notifications**: Real-time notifications for task updates
- **Analytics**: Dashboard with statistics and reports
- **Team Management**: Role-based access with Admin, Manager, User roles

## Authentication
All endpoints (except auth endpoints) require JWT authentication.
Include the token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

## Rate Limiting
- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="andres.celi@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Fullstack web Opción A (sesiones). API JWT intacta abajo.
    path('', dashboard_view, name='web-dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register_view, name='web-register'),
    path('tasks/', task_list, name='web-task-list'),
    path('tasks/new/', task_create, name='web-task-create'),
    path('tasks/<int:pk>/', task_detail, name='web-task-detail'),
    path('tasks/<int:pk>/edit/', task_edit, name='web-task-edit'),
    path('tasks/<int:pk>/delete/', task_delete, name='web-task-delete'),
    path('tasks/<int:pk>/complete/', task_complete, name='web-task-complete'),
    path('tasks/<int:pk>/comment/', task_comment, name='web-task-comment'),
    path('tasks/<int:pk>/attach/', task_attach, name='web-task-attach'),
    path('categories/', categories_view, name='web-categories'),
    path('categories/new/', category_create, name='web-cat-create'),
    path('categories/<int:pk>/delete/', category_delete, name='web-cat-delete'),
    path('tags/new/', tag_create, name='web-tag-create'),
    path('tags/<int:pk>/delete/', tag_delete, name='web-tag-delete'),
    path('notifications/', notif_list, name='web-notifs'),
    path('notifications/<int:pk>/read/', notif_read, name='web-notif-read'),
    path('notifications/read-all/', notif_read_all, name='web-notif-read-all'),
    path('team/', team_view, name='web-team'),
    path('reports/generate/', generate_report, name='web-report-generate'),
    
    # API Documentation (Swagger)
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API v1 endpoints
    path('api/v1/', include([
        path('', include('apps.users.urls')),
        path('', include('apps.tasks.urls')),
        path('', include('apps.notifications.urls')),
        path('analytics/', include('apps.analytics.urls')),
    ])),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
