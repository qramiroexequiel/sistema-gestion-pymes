# Sistema de Gestión Interna para PyMES

Sistema de gestión multi-empresa diseñado para pequeñas y medianas empresas. Permite gestionar clientes, proveedores, productos y operaciones comerciales (ventas y compras) de forma centralizada.

## Stack Tecnológico

- **Python 3.12+**
- **Django 5.x**
- **PostgreSQL** (producción) / SQLite (desarrollo)
- **Bootstrap 5** (UI)
- **HTMX** (opcional, para interacciones simples)

## Requisitos

- Python 3.12 o superior
- pip
- PostgreSQL 14+ (para producción)
- virtualenv (recomendado)

## Instalación

1. Clonar el repositorio:
```bash
cd "/home/qramiroexequiel/Escritorio/1- Sistema de gestión de Pymes"
```

2. Crear y activar entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements/development.txt
```

4. Copiar archivo de variables de entorno:
```bash
cp .env.example .env
```

5. Editar `.env` con tus configuraciones (al menos `SECRET_KEY`).

6. Aplicar migraciones:
```bash
python manage.py migrate
```

7. Crear superusuario:
```bash
python manage.py createsuperuser
```

8. Ejecutar servidor de desarrollo:
```bash
python manage.py runserver
```

## Estructura del Proyecto

```
.
├── config/              # Configuración principal de Django
│   └── settings/        # Settings por entorno (base, development, production)
├── core/                # Módulo base (Company, Membership, AuditLog)
├── customers/           # Gestión de clientes
├── suppliers/           # Gestión de proveedores
├── products/            # Gestión de productos/servicios
├── operations/          # Registro de operaciones (ventas/compras)
├── reports/             # Reportes operativos
├── config_app/          # Configuración por empresa
├── templates/           # Templates base
├── static/              # Archivos estáticos
└── media/               # Archivos subidos por usuarios
```

## Arquitectura Multi-Tenant

El sistema utiliza un modelo multi-tenant con separación lógica por `company_id`. Cada usuario puede pertenecer a múltiples empresas mediante el modelo `Membership`, con roles específicos por empresa.

### Roles Disponibles

- **Administrador**: Acceso completo a todos los módulos
- **Gestor**: Acceso a módulos de operaciones y reportes
- **Operador**: Acceso limitado a registro de operaciones

## Desarrollo

### Aplicar migraciones después de cambios en modelos:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Ejecutar servidor de desarrollo:
```bash
python manage.py runserver
```

### Acceder al admin:
```
http://localhost:8000/admin/
```

## Producción

1. Configurar variables de entorno en `.env`:
   - `SECRET_KEY`
   - `DEBUG=False`
   - `ALLOWED_HOSTS`
   - `DATABASE_URL`
   - `DJANGO_ENV=production`

2. Recolectar archivos estáticos:
```bash
python manage.py collectstatic
```

3. Ejecutar con gunicorn:
```bash
gunicorn config.wsgi:application
```

## Documentación

- `ARCHITECTURE.md`: Documentación técnica de la arquitectura
- `PRODUCT_OVERVIEW.md`: Documentación comercial del producto

## Licencia

Proyecto comercial privado.

