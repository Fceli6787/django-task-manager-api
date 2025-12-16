"""
URL configuration for Task Manager API project.

Includes all API endpoints and Swagger documentation.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


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
