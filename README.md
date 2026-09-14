# 🗂️ Django Task Manager

> Sistema fullstack de gestión de tareas con API REST (JWT), interfaz web con Django Templates + HTMX, MySQL, Redis y Celery. Diseñado como proyecto portfolio con foco en buenas prácticas.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14-A30000?logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Redis](https://img.shields.io/badge/Redis-7.2-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Tests](https://img.shields.io/badge/tests-pytest-blueviolet)](tests/)

<!-- 📸 REEMPLAZA ESTO CON TUS CAPTURAS REALES -->
<p align="center">
  <img src="docs/screenshots/dashboard.png" alt="Dashboard web" width="800">
</p>

<p align="center">
  <a href="#-quickstart">Quickstart</a> ·
  <a href="#-documentación">Documentación</a> ·
  <a href="#-api-rest">API</a> ·
  <a href="#-testing">Testing</a> ·
  <a href="#-roadmap">Roadmap</a>
</p>

---

## ✨ Características

- ✅ **CRUD completo de tareas** con soft-delete y papelera
- 🔐 **Doble autenticación**: JWT (API) + sesiones Django (web)
- 👥 **Roles y permisos**: Admin, Manager, User
- 📝 **Colaboración**: asignación, comentarios y @menciones
- 🏷️ **Organización**: categorías, tags, prioridades y deadlines
- 📊 **Dashboard analítico** con métricas en tiempo real
- 📚 **Swagger / ReDoc** autogenerados con drf-yasg
- 🎨 **Frontend** con Django Templates + HTMX + Atlas Design System
- ⚡ **Caché Redis** (con fallback LocMem para desarrollo local)
- 🔄 **Tareas recurrentes** con Celery Beat
- 📧 **Notificaciones** por email y push

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Django 5.0 · Django REST Framework 3.14 |
| Frontend | Django Templates · HTMX · Atlas CSS |
| Base de datos | MySQL 8.0 (`localhost:3306`) |
| Autenticación | SimpleJWT (API) · Sesiones Django (web) |
| Documentación | drf-yasg (Swagger / OpenAPI) |
| Caché | Redis 7.2 (prod) · LocMem (dev) |
| Task Queue | Celery + Redis |
| Testing | pytest · pytest-django |
| Entorno | Python 3.11+ |

---

## ⚡ Quickstart

> Para tener el proyecto corriendo en local en menos de 2 minutos (sin Redis, sin Celery).

```bash
# 1. Clonar
git clone https://github.com/yourusername/django-task-manager-api.git
cd django-task-manager-api

# 2. Entorno virtual
python -m venv venv
source venv/bin/activate          # Linux / macOS
# venv\Scripts\activate           # Windows

# 3. Dependencias
pip install setuptools==68.0.0
pip install -r requirements/dev.txt

# 4. Variables de entorno
cp .env.example .env              # Linux / macOS
# Copy-Item .env.example .env     # Windows

# 5. Base de datos (MySQL)
mysql -u root -e "CREATE DATABASE task_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 6. Migraciones y superusuario
python manage.py migrate
python manage.py createsuperuser

# 7. Arrancar
python manage.py runserver
```

Abre 👉 http://localhost:8000/login/

<details>
<summary><b>⚙️ Configuración detallada (.env, MySQL, Redis, Celery)</b></summary>

### Variables de entorno (`.env`)

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `SECRET_KEY` | — | Genera con `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `True` | Modo debug |
| `DB_NAME` | `task_manager_db` | Nombre de la base de datos |
| `DB_USER` | `root` | Usuario MySQL |
| `DB_PASSWORD` | _(vacío)_ | Contraseña MySQL |
| `DB_HOST` | `localhost` | Host MySQL |
| `DB_PORT` | `3306` | Puerto MySQL |
| `USE_REDIS` | `False` | `True` para usar Redis real |
| `REDIS_URL` | `redis://localhost:6379/0` | URL de Redis |
| `EMAIL_HOST` | `smtp.gmail.com` | Servidor SMTP |

### MySQL

Compatible con **XAMPP**, **WAMP**, **Workbench** o **MySQL puro**:
- XAMPP/WAMP: `root` sin contraseña por defecto.
- MySQL puro / Workbench: usa tus credenciales.

### Redis + Celery (opcional en local)

```bash
# Worker
celery -A config worker -l info

# Beat (tareas programadas)
celery -A config beat -l info
```

Si no quieres instalar Redis en local, deja `USE_REDIS=False` y usa Celery en modo eager.

### Nota sobre dependencias

`django-celery-beat==2.6.0` es **obligatorio** en Django 5.0 (la 2.5.0 exige Django<5.0 y rompe pip).

</details>

---

## 📁 Estructura del Proyecto

```
django-task-manager-api/
├── config/                     # Configuración del proyecto
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── apps/
│   ├── tasks/                  # App principal
│   │   ├── models.py           # Task, Category, Tag, Comment
│   │   ├── views.py            # ViewSets (JWT)
│   │   ├── views_web.py        # Vistas HTML (sesión)
│   │   ├── serializers.py
│   │   ├── filters.py
│   │   └── tasks.py            # Celery tasks
│   ├── users/                  # User, UserActivity
│   ├── notifications/          # Notification, Preferences
│   └── analytics/              # Stats + Dashboard
├── templates/                  # base.html + registration/ + web/
├── static/css/app.css          # Atlas Design System
├── core/                       # SoftDelete, permisos, paginación
├── tests/                      # Tests por app
├── docs/                       # Documentación y screenshots
└── requirements/               # dev.txt / prod.txt
```

---

## 📚 Documentación

| Recurso | URL | Auth |
|---------|-----|------|
| 🖥️ Dashboard web | [`/`](http://localhost:8000/) | Sesión |
| 📝 Tareas | [`/tasks/`](http://localhost:8000/tasks/) | Sesión |
| 🏷️ Categorías | [`/categories/`](http://localhost:8000/categories/) | Sesión |
| 🔔 Notificaciones | [`/notifications/`](http://localhost:8000/notifications/) | Sesión |
| 👥 Equipo | [`/team/`](http://localhost:8000/team/) | Manager+ |
| 📖 Swagger UI | [`/swagger/`](http://localhost:8000/swagger/) | Público |
| 📕 ReDoc | [`/redoc/`](http://localhost:8000/redoc/) | Público |
| ⚙️ Admin Django | [`/admin/`](http://localhost:8000/admin/) | Staff |

---

## 🌐 Web (sesión)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Dashboard + estado MySQL |
| `GET/POST` | `/login/` · `/register/` · `/logout/` | Autenticación web |
| `GET` | `/tasks/?filter=trash` | Lista con filtros y papelera |
| `GET/POST` | `/tasks/new/` · `/tasks/<id>/edit/` | Crear / editar |
| `POST` | `/tasks/<id>/complete/` | Marcar como completada |
| `POST` | `/tasks/<id>/comment/` | Añadir comentario |
| `POST` | `/tasks/<id>/attach/` | Adjuntar archivo |
| `GET/POST` | `/categories/` · `/tags/` | Organización |
| `GET/POST` | `/notifications/` | Preferencias email/push |

---

## 🔌 API REST

Base URL: `http://localhost:8000/api/v1/`

### 🔐 Autenticación

<details>
<summary><b>Registro</b></summary>

```http
POST /api/v1/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```
</details>

<details>
<summary><b>Login</b></summary>

```http
POST /api/v1/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
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
</details>

<details>
<summary><b>Usar el token</b></summary>

```bash
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/v1/tasks/
```
</details>

### 📋 Tareas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/tasks/` | Listar tareas |
| `POST` | `/tasks/` | Crear tarea |
| `GET` | `/tasks/{id}/` | Detalle |
| `PATCH` | `/tasks/{id}/` | Actualizar |
| `DELETE` | `/tasks/{id}/` | Soft delete |
| `POST` | `/tasks/{id}/complete/` | Completar |
| `POST` | `/tasks/{id}/restore/` | Restaurar |
| `GET` | `/tasks/my_tasks/` | Mis tareas |
| `GET` | `/tasks/overdue/` | Vencidas |
| `GET` | `/tasks/trash/` | Papelera |

### 👤 Usuarios

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/users/me/` | Perfil actual |
| `PATCH` | `/users/update_profile/` | Actualizar perfil |
| `POST` | `/users/change_password/` | Cambiar contraseña |
| `GET` | `/users/team/` | Ver equipo (manager+) |

### 📊 Analytics

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/analytics/dashboard/` | Estadísticas generales |
| `GET` | `/analytics/trends/` | Tendencias |
| `GET` | `/analytics/by-status/` | Por estado |
| `GET` | `/analytics/team/` | Stats del equipo |

---

## 🎨 Frontend

`static/css/app.css` implementa el **Atlas Design System**: tokens de color, layout responsive (`.container`, `.grid-2/3/4`), componentes (cards, `.task`, badges de estado/prioridad), formularios, comentarios y timeline. Complementado con **HTMX** para interactividad sin recargar y **Tailwind CDN** para utilidades puntuales.

> Detalles técnicos del design system en [`docs/frontend.md`](docs/frontend.md).

---

## 🧪 Testing

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=apps --cov=core

# Un archivo específico
pytest tests/test_tasks.py -v

# Solo tests marcados
pytest -m "not slow"
```

---

## 🚦 Roadmap

### ✅ Completado
- [x] Setup inicial y modelos (`users`, `tasks`, `notifications`, `analytics`)
- [x] API CRUD completa con soft-delete
- [x] Autenticación JWT + sesiones web
- [x] Sistema de permisos por roles
- [x] Swagger / ReDoc
- [x] Web fullstack (`/`, `/tasks/`, `/categories/`, `/notifications/`, `/team/`)
- [x] Dashboard con badge MySQL `localhost:3306`
- [x] Tests unitarios con pytest
- [x] Caché Redis con fallback LocMem
- [x] Celery + notificaciones

### 🔜 Próximamente
- [ ] Dockerización (`Dockerfile` + `docker-compose.yml`)
- [ ] CI/CD con GitHub Actions
- [ ] Cobertura de tests ≥ 85%
- [ ] WebSockets para notificaciones en vivo
- [ ] i18n (ES / EN)

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del repo
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit con [Conventional Commits](https://www.conventionalcommits.org/)
4. Push y abre un Pull Request

Lee [`CONTRIBUTING.md`](CONTRIBUTING.md) para más detalles.

---

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT** — ver [`LICENSE`](LICENSE) para más detalles.

---

## 👨‍💻 Autor

**Andrés Felipe Celi Jiménez**
🔗 [GitHub](https://github.com/fceli6787) · 💼 [LinkedIn](https://www.linkedin.com/in/andres-felipe-celi-jimenez-a12a191a7/)

Si este proyecto te resultó útil, dale una ⭐ — ¡motiva a seguir mejorando!
