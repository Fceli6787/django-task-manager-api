# Setup Guide

## Prerequisites

1. **Python 3.11+** - Download from [python.org](https://www.python.org/)
2. **MySQL 8.0+** - Download from [mysql.com](https://dev.mysql.com/downloads/)
3. **Redis 7.2+** - Download from [redis.io](https://redis.io/download/) or use Docker

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd django-task-manager-api

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements/dev.txt
```

### 2. Database Setup

```sql
-- Connect to MySQL
mysql -u root -p

-- Create database
CREATE DATABASE task_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (optional)
CREATE USER 'taskmanager'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON task_manager_db.* TO 'taskmanager'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Important settings:
# - SECRET_KEY (generate a new one for production)
# - DB_PASSWORD (your MySQL password)
# - REDIS_URL (if using Redis)
```

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 5. Start Development Server

```bash
python manage.py runserver
```

Visit:
- API: http://localhost:8000/api/v1/
- Swagger: http://localhost:8000/swagger/
- Admin: http://localhost:8000/admin/

## Running Celery (Optional)

For background tasks like notifications and scheduled jobs:

```bash
# Terminal 1 - Celery Worker
celery -A config worker -l info

# Terminal 2 - Celery Beat (Scheduler)
celery -A config beat -l info
```

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=apps --cov=core --cov-report=html

# Specific test file
pytest tests/test_tasks.py -v
```

## Docker Setup (Alternative)

```bash
# Build and run
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## Troubleshooting

### MySQL Connection Issues
- Verify MySQL is running: `sudo systemctl status mysql`
- Check credentials in `.env`
- Ensure database exists: `mysql -u root -p -e "SHOW DATABASES;"`

### Redis Connection Issues
- Verify Redis is running: `redis-cli ping`
- Should return: `PONG`

### Migration Issues
- Delete all migrations (except `__init__.py`) and recreate
- Check for circular imports in models
