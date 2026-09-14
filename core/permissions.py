"""
Custom permissions for the Task Manager API.
"""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Permission to only allow owners of an object to access it.
    """
    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, 'owner', None)
        if owner is None:
            # Soporta Comment(author) sin 500.
            owner = getattr(obj, 'author', None)
        if owner is None:
            return False
        return owner == request.user


class IsOwnerOrAssigned(permissions.BasePermission):
    """
    Permission to allow owners or assigned users to access a task.
    """
    def has_object_permission(self, request, view, obj):
        if getattr(obj, 'owner', None) == request.user:
            return True
        assigned = getattr(obj, 'assigned_to', None)
        if assigned is not None and request.user.is_authenticated:
            # FIX: exists() en vez de `user in all()` que cargaba todo el M2M.
            return assigned.filter(id=request.user.id).exists()
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
        owner = getattr(obj, 'owner', None) or getattr(obj, 'author', None)
        return owner == request.user


class CanManageTasks(permissions.BasePermission):
    """
    Permission for managing tasks based on user role.
    - Admins can manage all tasks
    - Managers can manage tasks in their teams
    - Users can only manage their own tasks
    - Assigned users: solo lectura (usar acción dedicada para status)
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        
        # Admins can do anything
        if getattr(user, 'role', None) == 'admin':
            return True
        
        # Owner can always access their tasks
        if getattr(obj, 'owner', None) == user:
            return True
        
        # Assigned users: FIX solo lectura. Antes PATCH/PUT total (escalada).
        assigned = getattr(obj, 'assigned_to', None)
        if assigned is not None and assigned.filter(id=user.id).exists():
            return request.method in permissions.SAFE_METHODS
        
        # Managers can access tasks of their team members
        if getattr(user, 'role', None) == 'manager':
            owner = getattr(obj, 'owner', None)
            if owner is not None and getattr(owner, 'manager_id', None) == user.id:
                return True
        
        return False
