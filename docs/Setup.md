# Guía de Instalación

## Prerrequisitos
- Python 3.11+
- MySQL 8.0+
- Git

## Instalación Local

1. Clonar repositorio
2. Crear entorno virtual: `python -m venv venv`
3. Activar: `source venv/bin/activate` (Linux/Mac)
4. Instalar dependencias: `pip install -r requirements/dev.txt`
5. Crear base de datos MySQL
6. Copiar .env.example a .env y configurar
7. Ejecutar migraciones
8. Crear superusuario
