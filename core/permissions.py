"""
Custom permissions for the Task Manager API.
"""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Permission to only allow owners of an object to access it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsOwnerOrAssigned(permissions.BasePermission):
    """
    Permission to allow owners or assigned users to access a task.
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        if hasattr(obj, 'assigned_to') and request.user in obj.assigned_to.all():
            return True
        return False


class IsAdminUser(permissions.BasePermission):
    """
    Permission to only allow admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Permission to allow managers and admins.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'manager']


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission to allow owners to edit, others can only read.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class CanManageTasks(permissions.BasePermission):
    """
    Permission for managing tasks based on user role.
    - Admins can manage all tasks
    - Managers can manage tasks in their teams
    - Users can only manage their own tasks
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admins can do anything
        if user.role == 'admin':
            return True
        
        # Owner can always access their tasks
        if obj.owner == user:
            return True
        
        # Assigned users have read access
        if hasattr(obj, 'assigned_to') and user in obj.assigned_to.all():
            if request.method in permissions.SAFE_METHODS:
                return True
            # Assigned users can update task status
            if request.method in ['PATCH', 'PUT']:
                return True
        
        # Managers can access tasks of their team members
        if user.role == 'manager':
            if hasattr(obj.owner, 'manager') and obj.owner.manager == user:
                return True
        
        return False
