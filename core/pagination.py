"""
Custom pagination classes for the API.
"""
from rest_framework.pagination import PageNumberPagination, CursorPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination with customizable page size.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination for large result sets.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class TaskCursorPagination(CursorPagination):
    """
    Cursor pagination for tasks (more efficient for large datasets).
    """
    page_size = 20
    ordering = '-created_at'
    cursor_query_param = 'cursor'
