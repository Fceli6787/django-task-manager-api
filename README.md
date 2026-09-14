# Django Task Manager — API + Web Fullstack

Sistema de gestión de tareas con autenticación JWT, MySQL y documentación Swagger,
más interfaz web Django (sesiones) con design system Atlas en `static/css/app.css`.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.0-green.svg)
![DRF](https://img.shields.io/badge/DRF-3.14-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🚀 Características Principales

- ✅ **CRUD completo de tareas** con soft-delete (API + web `/tasks/`)
- 🔐 **Autenticación JWT** con refresh tokens (API) + sesiones Django (web `/login/`)
- 👥 **Sistema de roles y permisos** (Admin, Manager, User)
- 📝 **Colaboración**: asignación de tareas, comentarios y @menciones
- 🏷️ **Organización**: categorías, tags, prioridades y fechas límite
- 📊 **Dashboard web `/`** con analytics y reportes (mismos datos que `/api/v1/analytics/dashboard/`)
- 📚 **Documentación interactiva** con Swagger/OpenAPI
- 🎨 **Frontend Django Templates + HTMX + Atlas CSS** (`templates/`, `static/css/app.css`)
- ⚡ **Optimización de queries** y caché con Redis (opcional local con `USE_REDIS=False`)
- 🔄 **Tareas recurrentes** con Celery
- 📧 **Notificaciones** por email y push (flags + web `/notifications/`)

## 🛠️ Stack Tecnológico

| Categoría | Tecnología |
|-----------|------------|
| Backend | Django 5.0, Django REST Framework 3.14 |
| Frontend web | Django Templates + HTMX + `static/css/app.css` (Atlas Design System) |
| Base de Datos | MySQL 8.0 (`localhost:3306` — XAMPP / WAMP / Workbench / MySQL puro) |
| Autenticación | djangorestframework-simplejwt (API) + sesiones Django (web) |
| Documentación | drf-yasg (Swagger/OpenAPI) |
| Caché | Redis 7.2 (prod) / LocMem + `USE_REDIS=False` (local sin Redis) |
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
│   │   ├── views.py        # ViewSets y APIs (JWT)
│   │   ├── views_web.py    # Vistas HTML (sesión): lista/detalle/CRUD
│   │   ├── serializers.py  # Serializers
│   │   ├── filters.py      # Filtros de búsqueda
│   │   └── tasks.py        # Celery tasks
│   ├── users/              # Gestión de usuarios
│   │   ├── models.py       # User, UserActivity
│   │   ├── views.py        # Auth y profile APIs
│   │   ├── views_web.py    # Registro web
│   │   └── serializers.py  # User serializers
│   ├── notifications/      # Sistema de notificaciones
│   │   ├── models.py       # Notification, Preferences
│   │   ├── views_web.py    # Lista equipo + badge MySQL
│   │   └── tasks.py        # Email/push tasks
│   └── analytics/          # Reportes y estadísticas
│       ├── models.py       # Stats models
│       ├── views.py        # Dashboard APIs
│       └── views_web.py    # Dashboard HTML + `get_db_status()` 3306
├── templates/              # Frontend Opción A
│   ├── base.html
│   ├── registration/login.html, register.html
│   └── web/dashboard.html, task_list.html, task_detail.html, categories.html, notifications.html, team.html
├── static/css/app.css      # Atlas Design System (tokens, layout, cards, tasks, auth)
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

- Python 3.11+ (probado 3.12)
- MySQL 8.0+ en `localhost:3306` (vale XAMPP, WAMP, Workbench o MySQL puro)
- Redis 7.2+ solo prod/Celery (local: `USE_REDIS=False`, sin instalar Redis)

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
pip install setuptools==68.0.0
pip install -r requirements/dev.txt
# Nota: django-celery-beat==2.6.0 (2.5.0 exige Django<5.0 y rompe pip)
```

4. **Configurar variables de entorno**
```bash
Copy-Item .env.example .env  # Windows / cp .env.example .env
# MySQL local: DB_USER=root DB_PASSWORD= DB_HOST=localhost DB_PORT=3306
# (XAMPP/WAMP: root sin clave por defecto / Workbench/MySQL puro: tu clave)
# Local sin Redis: USE_REDIS=False
# Generar: python -c "from django.core.management.utils import get_random_secret_key; print(...)"
```

5. **Crear base de datos MySQL**
```sql
CREATE DATABASE task_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

6. **Ejecutar migraciones**
```bash
python manage.py makemigrations users tasks notifications analytics
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

## 📚 Documentación y Web

- **Web (sesión)**: http://localhost:8000/login/ → `/` dashboard (badge `MySQL localhost:3306 OK`), `/tasks/`, `/categories/`, `/notifications/`, `/team/`
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

### Web fullstack (sesión)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Dashboard + badge MySQL 3306 |
| GET/POST | `/login/`, `/register/`, `/logout/` | Auth web |
| GET | `/tasks/` | Lista + filtros + papelera `?filter=trash` |
| GET/POST | `/tasks/new/`, `/tasks/<id>/edit/` | CRUD |
| POST | `/tasks/<id>/complete/`, `/comment/`, `/attach/` | Colaboración |
| GET/POST | `/categories/`, `/tags/` | Organización |
| GET/POST | `/notifications/` | Email/push flags |
| GET | `/team/` | Equipo (manager/admin) |

### API (JWT)
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

## 🎨 Frontend CSS

`static/css/app.css` — Atlas Design System (~1300 líneas): tokens (`--paper/--ink/--accent`), reset accesible, layout `.container/.grid-2/3/4`, header/nav, cards/stats, `.task` + badges estado/prioridad, formularios, comentarios, adjuntos, timeline historial, auth, notificaciones y equipo, responsive + `prefers-reduced-motion`. Se carga en `templates/base.html` (Tailwind CDN + HTMX como complemento).

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

✅ **Fullstack Opción A** – API JWT intacta + web Django con Atlas CSS

### Checklist

- [x] Setup inicial del proyecto
- [x] Modelos y migraciones (`makemigrations users tasks notifications analytics`)
- [x] API CRUD básica
- [x] Autenticación JWT + sesiones web
- [x] Sistema de permisos (roles)
- [x] Documentación Swagger
- [x] Web `/`, `/tasks/`, `/categories/`, `/notifications/`, `/team/` + `static/css/app.css`
- [x] Badge MySQL `localhost:3306` en dashboard
- [x] Tests unitarios
- [x] Optimizaciones y caché (`USE_REDIS=False` local / Redis prod)
- [x] Features avanzadas (Celery, notificaciones)

## 👨‍💻 Autor

**Andres Felipe Celi Jimenez** – Proyecto Portfolio

## 📄 Licencia

Este proyecto está bajo la Licencia MIT – ver el archivo [LICENSE](LICENSE) para más detalles.
