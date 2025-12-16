# Django Task Manager API

Sistema de gestión de tareas con autenticación JWT, MySQL y documentación Swagger

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.0-green.svg)
![DRF](https://img.shields.io/badge/DRF-3.14-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🚀 Características Principales

- ✅ **CRUD completo de tareas** con soft-delete
- 🔐 **Autenticación JWT** con refresh tokens
- 👥 **Sistema de roles y permisos** (Admin, Manager, User)
- 📝 **Colaboración**: asignación de tareas, comentarios y @menciones
- 🏷️ **Organización**: categorías, tags, prioridades y fechas límite
- 📊 **Dashboard** con analytics y reportes
- 📚 **Documentación interactiva** con Swagger/OpenAPI
- ⚡ **Optimización de queries** y caché con Redis
- 🔄 **Tareas recurrentes** con Celery
- 📧 **Notificaciones** por email y push

## 🛠️ Stack Tecnológico

| Categoría | Tecnología |
|-----------|------------|
| Backend | Django 5.0, Django REST Framework 3.14 |
| Base de Datos | MySQL 8.0 |
| Autenticación | djangorestframework-simplejwt |
| Documentación | drf-yasg (Swagger/OpenAPI) |
| Caché | Redis 7.2 |
| Task Queue | Celery + Redis |
| Testing | pytest, pytest-django |

## 📁 Estructura del Proyecto

```
django-task-manager-api/
├── config/                 # Configuración del proyecto
│   ├── settings.py         # Configuración principal
│   ├── urls.py             # URLs raíz
│   ├── celery.py           # Configuración de Celery
│   └── wsgi.py             # WSGI application
├── apps/
│   ├── tasks/              # App principal de tareas
│   │   ├── models.py       # Task, Category, Tag, Comment
│   │   ├── views.py        # ViewSets y APIs
│   │   ├── serializers.py  # Serializers
│   │   ├── filters.py      # Filtros de búsqueda
│   │   └── tasks.py        # Celery tasks
│   ├── users/              # Gestión de usuarios
│   │   ├── models.py       # User, UserActivity
│   │   ├── views.py        # Auth y profile APIs
│   │   └── serializers.py  # User serializers
│   ├── notifications/      # Sistema de notificaciones
│   │   ├── models.py       # Notification, Preferences
│   │   └── tasks.py        # Email/push tasks
│   └── analytics/          # Reportes y estadísticas
│       ├── models.py       # Stats models
│       └── views.py        # Dashboard APIs
├── core/                   # Utilidades compartidas
│   ├── models.py           # Base models (SoftDelete)
│   ├── permissions.py      # Custom permissions
│   ├── pagination.py       # Pagination classes
│   └── exceptions.py       # Custom exceptions
├── tests/                  # Tests organizados por app
├── docs/                   # Documentación adicional
└── requirements/           # Dependencias por entorno
```

## 🚀 Instalación

### Requisitos Previos

- Python 3.11+
- MySQL 8.0+
- Redis 7.2+ (para caché y Celery)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/yourusername/django-task-manager-api.git
cd django-task-manager-api
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements/dev.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

5. **Crear base de datos MySQL**
```sql
CREATE DATABASE task_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

6. **Ejecutar migraciones**
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Crear superusuario**
```bash
python manage.py createsuperuser
```

8. **Iniciar el servidor**
```bash
python manage.py runserver
```

### Iniciar Celery (para tareas en segundo plano)

```bash
# Worker
celery -A config worker -l info

# Beat (tareas programadas)
celery -A config beat -l info
```

## 📚 Documentación API

Una vez iniciado el servidor, accede a la documentación interactiva:

- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/
- **Admin**: http://localhost:8000/admin/

## 🔑 Autenticación

### Registro de Usuario
```bash
POST /api/v1/auth/register/
{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
}
```

### Login (Obtener Token)
```bash
POST /api/v1/auth/login/
{
    "email": "user@example.com",
    "password": "SecurePass123!"
}

# Response:
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

### Usar Token
```bash
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/v1/tasks/
```

## 📋 Endpoints Principales

### Tareas
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/tasks/` | Listar tareas |
| POST | `/api/v1/tasks/` | Crear tarea |
| GET | `/api/v1/tasks/{id}/` | Detalle de tarea |
| PATCH | `/api/v1/tasks/{id}/` | Actualizar tarea |
| DELETE | `/api/v1/tasks/{id}/` | Eliminar (soft delete) |
| POST | `/api/v1/tasks/{id}/complete/` | Completar tarea |
| POST | `/api/v1/tasks/{id}/restore/` | Restaurar tarea |
| GET | `/api/v1/tasks/my_tasks/` | Mis tareas |
| GET | `/api/v1/tasks/overdue/` | Tareas vencidas |
| GET | `/api/v1/tasks/trash/` | Tareas eliminadas |

### Usuarios
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/users/me/` | Perfil actual |
| PATCH | `/api/v1/users/update_profile/` | Actualizar perfil |
| POST | `/api/v1/users/change_password/` | Cambiar contraseña |
| GET | `/api/v1/users/team/` | Ver equipo (managers) |

### Analytics
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/analytics/dashboard/` | Dashboard stats |
| GET | `/api/v1/analytics/trends/` | Tendencias |
| GET | `/api/v1/analytics/by-status/` | Por estado |
| GET | `/api/v1/analytics/team/` | Stats de equipo |

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=apps --cov=core

# Tests específicos
pytest tests/test_tasks.py -v
```

## 🚦 Estado del Proyecto

✅ **Completado** – Todas las características implementadas

### Checklist

- [x] Setup inicial del proyecto
- [x] Modelos y migraciones
- [x] API CRUD básica
- [x] Autenticación JWT
- [x] Sistema de permisos (roles)
- [x] Documentación Swagger
- [x] Tests unitarios
- [x] Optimizaciones y caché
- [x] Features avanzadas (Celery, notificaciones)

## 👨‍💻 Autor

**Andres Felipe Celi Jimenez** – Proyecto Portfolio

## 📄 Licencia

Este proyecto está bajo la Licencia MIT – ver el archivo [LICENSE](LICENSE) para más detalles.
