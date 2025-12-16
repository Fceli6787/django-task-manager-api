"""
Admin configuration for the Users app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserActivity


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model."""
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'avatar', 'bio', 'phone')}),
        (_('Role & Team'), {'fields': ('role', 'manager')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Notifications'), {'fields': ('email_notifications', 'push_notifications')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'last_login_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined', 'last_login_at', 'created_at', 'updated_at')


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Admin configuration for UserActivity model."""
    
    list_display = ('user', 'action', 'created_at', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('user__email', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'action', 'description', 'ip_address', 'user_agent', 'metadata', 'created_at')
