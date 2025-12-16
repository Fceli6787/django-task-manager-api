# API Reference

## Authentication

All endpoints (except auth endpoints) require JWT authentication.

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## Auth Endpoints

### POST /api/v1/auth/register/
Register a new user.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Response (201):**
```json
{
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
}
```

### POST /api/v1/auth/login/
Obtain JWT tokens.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe",
        "role": "user"
    }
}
```

### POST /api/v1/auth/refresh/
Refresh access token.

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## Task Endpoints

### GET /api/v1/tasks/
List all tasks (paginated).

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status (pending, in_progress, completed) |
| priority | string | Filter by priority (low, medium, high, urgent) |
| category | integer | Filter by category ID |
| search | string | Search in title/description |
| ordering | string | Order by field (-created_at, due_date, priority) |
| page | integer | Page number |
| page_size | integer | Items per page (max 100) |

**Response (200):**
```json
{
    "count": 50,
    "next": "http://localhost:8000/api/v1/tasks/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Complete project",
            "status": "in_progress",
            "priority": "high",
            "due_date": "2024-01-15T10:00:00Z",
            "is_overdue": false
        }
    ]
}
```

### POST /api/v1/tasks/
Create a new task.

**Request Body:**
```json
{
    "title": "New Task",
    "description": "Task description",
    "priority": "high",
    "status": "pending",
    "due_date": "2024-01-20T10:00:00Z",
    "category": 1,
    "tag_ids": [1, 2],
    "assigned_to_ids": [2, 3]
}
```

### GET /api/v1/tasks/{id}/
Get task details.

### PATCH /api/v1/tasks/{id}/
Update a task.

### DELETE /api/v1/tasks/{id}/
Soft delete a task.

### POST /api/v1/tasks/{id}/complete/
Mark task as completed.

### POST /api/v1/tasks/{id}/restore/
Restore a soft-deleted task.

### GET /api/v1/tasks/overdue/
Get overdue tasks.

### GET /api/v1/tasks/due_today/
Get tasks due today.

### GET /api/v1/tasks/trash/
Get deleted tasks.

---

## Category Endpoints

### GET /api/v1/categories/
List categories.

### POST /api/v1/categories/
Create category.

**Request Body:**
```json
{
    "name": "Work",
    "description": "Work related tasks",
    "color": "#3498db"
}
```

### PATCH /api/v1/categories/{id}/
Update category.

### DELETE /api/v1/categories/{id}/
Delete category.

---

## Tag Endpoints

### GET /api/v1/tags/
List tags.

### POST /api/v1/tags/
Create tag.

**Request Body:**
```json
{
    "name": "urgent",
    "color": "#e74c3c"
}
```

---

## Comment Endpoints

### GET /api/v1/tasks/{task_id}/comments/
List comments for a task.

### POST /api/v1/tasks/{task_id}/comments/
Add comment to task.

**Request Body:**
```json
{
    "content": "This is a comment @john",
    "task": 1
}
```

---

## Notification Endpoints

### GET /api/v1/notifications/
List notifications.

### GET /api/v1/notifications/unread_count/
Get unread count.

### POST /api/v1/notifications/{id}/mark_read/
Mark as read.

### POST /api/v1/notifications/mark_all_read/
Mark all as read.

---

## Analytics Endpoints

### GET /api/v1/analytics/dashboard/
Get dashboard statistics.

**Response (200):**
```json
{
    "total_tasks": 100,
    "completed_tasks": 45,
    "pending_tasks": 30,
    "overdue_tasks": 5,
    "in_progress_tasks": 20,
    "completion_rate": 45.0,
    "tasks_due_today": 3,
    "tasks_due_this_week": 12,
    "urgent_tasks": 2,
    "high_priority_tasks": 8
}
```

### GET /api/v1/analytics/trends/
Get task trends.

**Query Parameters:**
- `days` (integer): Number of days (default: 30)

### GET /api/v1/analytics/by-status/
Get tasks grouped by status.

### GET /api/v1/analytics/by-priority/
Get tasks grouped by priority.

### GET /api/v1/analytics/team/
Get team analytics (managers only).

---

## Error Responses

### 400 Bad Request
```json
{
    "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```

### 429 Too Many Requests
```json
{
    "detail": "Request was throttled. Expected available in X seconds."
}
```
