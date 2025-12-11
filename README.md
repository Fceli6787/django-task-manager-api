# Django Task Manager API

> Sistema de gestión de tareas con autenticación JWT, MySQL y documentación Swagger

## 🚀 Características Principales

- ✅ CRUD completo de tareas con soft-delete
- 🔐 Autenticación JWT con refresh tokens
- 👥 Sistema de roles y permisos (Admin, Manager, User)
- 📝 Colaboración: asignación de tareas, comentarios y menciones
- 🏷️ Organización: categorías, tags, prioridades y fechas límite
- 📊 Dashboard con analytics y reportes
- 📚 Documentación interactiva con Swagger/OpenAPI
- ⚡ Optimización de queries y caché con Redis
- 🔄 Tareas recurrentes con Celery

## 🛠️ Stack Tecnológico

- **Backend**: Django 5.0, Django REST Framework 3.14
- **Base de Datos**: MySQL 8.0
- **Autenticación**: djangorestframework-simplejwt
- **Documentación**: drf-yasg (Swagger)
- **Caché**: Redis 7.2
- **Task Queue**: Celery + Redis
- **Testing**: pytest, pytest-django

## 📁 Estructura del Proyecto

django-task-manager-api/
├── config/ # Configuración del proyecto
├── apps/
│ ├── tasks/ # App principal de tareas
│ ├── users/ # Gestión de usuarios
│ ├── notifications/ # Sistema de notificaciones
│ └── analytics/ # Reportes y estadísticas
├── core/ # Utilidades compartidas
├── tests/ # Tests organizados por app
├── docs/ # Documentación adicional
└── requirements/ # Dependencias por entorno

text

## 🚦 Estado del Proyecto

🔧 En desarrollo - Fase inicial

text

## 📝 Roadmap

- [ ] Setup inicial del proyecto
- [ ] Modelos y migraciones
- [ ] API CRUD básica
- [ ] Autenticación JWT
- [ ] Sistema de permisos
- [ ] Documentación Swagger
- [ ] Tests unitarios
- [ ] Optimizaciones y caché
- [ ] Features avanzadas

## 👨‍💻 Autor

[Tu Nombre] - Proyecto Portfolio

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE)