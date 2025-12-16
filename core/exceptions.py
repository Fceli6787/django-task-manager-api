"""
Custom exceptions for the Task Manager API.
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class TaskManagerException(APIException):
    """Base exception for Task Manager API."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An error occurred.'
    default_code = 'error'


class TaskNotFoundError(TaskManagerException):
    """Exception raised when a task is not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Task not found.'
    default_code = 'task_not_found'


class TaskAlreadyCompletedError(TaskManagerException):
    """Exception raised when trying to modify a completed task."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Cannot modify a completed task.'
    default_code = 'task_already_completed'


class InvalidAssignmentError(TaskManagerException):
    """Exception raised for invalid task assignments."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid task assignment.'
    default_code = 'invalid_assignment'


class PermissionDeniedError(TaskManagerException):
    """Exception raised when user lacks permission."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'permission_denied'


class DuplicateEntryError(TaskManagerException):
    """Exception raised for duplicate entries."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'This entry already exists.'
    default_code = 'duplicate_entry'
