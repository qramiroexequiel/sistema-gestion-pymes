# Arquitectura del Sistema de Gestión Interna para PyMES

## 1. Propuesta de Arquitectura General

### 1.1 Arquitectura Multi-Tenant (Multi-Empresa)

**Modelo de Separación:** Separación lógica mediante `company_id` en todas las tablas relacionadas con datos de negocio. Todas las consultas incluyen filtrado automático por empresa.

**Ventajas:**
- Implementación rápida (sin múltiples bases de datos)
- Mantenimiento simplificado
- Escalable para decenas de clientes sin refactorizar
- Costos de infraestructura reducidos

**Estrategia de Aislamiento:**
- Middleware que identifica automáticamente la empresa del usuario autenticado
- QuerySets personalizados que filtran por empresa automáticamente
- Decoradores y mixins para views que validan acceso por empresa
- Validaciones a nivel de modelo que previenen fugas de datos entre empresas

### 1.2 Patrón de Diseño

**MVC (Model-View-Template)** - Estándar Django con separación por módulos de negocio.

**Módulos Principales:**
- `core`: Funcionalidades base (usuarios, empresas, autenticación)
- `customers`: Gestión de clientes
- `suppliers`: Gestión de proveedores
- `products`: Gestión de productos/servicios
- `operations`: Registro de ventas y compras
- `reports`: Generación de reportes
- `config`: Configuración por empresa

### 1.3 Capas de la Aplicación

```
┌─────────────────────────────────────┐
│   Templates (Interfaz de Usuario)   │
├─────────────────────────────────────┤
│   Views (Lógica de Presentación)    │
├─────────────────────────────────────┤
│   Services (Lógica de Negocio)      │
├─────────────────────────────────────┤
│   Models (Capa de Datos)            │
├─────────────────────────────────────┤
│   Database (PostgreSQL)             │
└─────────────────────────────────────┘
```

**Services Layer:** Separación de lógica de negocio de las views para:
- Reutilización
- Testabilidad
- Preparación para API REST futura

## 2. Stack Tecnológico Definitivo

### 2.1 Backend

- **Python 3.12+**: Última versión estable con mejor rendimiento y características modernas
- **Django 5.x**: Framework maduro, seguro, última versión estable
- **psycopg2-binary**: Driver para PostgreSQL
- **Pillow**: Manejo de imágenes (avatares, logos de empresa)
- **django-crispy-forms**: Formularios HTML profesionales (opcional, para mejorar UX)
- **crispy-bootstrap5**: Estilos Bootstrap 5 para formularios (opcional)

### 2.2 Base de Datos

- **PostgreSQL 14+**: Base de datos relacional robusta, preparada para producción

### 2.3 Frontend

- **Bootstrap 5**: Framework CSS para UI consistente y profesional
- **Django Templates**: Sistema de templates nativo de Django
- **HTMX (opcional)**: Para interacciones simples sin JavaScript complejo
- **Font Awesome 6**: Iconografía profesional

### 2.4 Seguridad y Autenticación

- **Django Auth**: Sistema de autenticación nativo
- **django-ratelimit**: Protección contra ataques de fuerza bruta
- **django-cors-headers**: Para futura API REST

### 2.5 Utilidades

- **python-decouple**: Gestión de variables de entorno
- **dj-database-url**: Configuración de base de datos mediante URL

### 2.6 Herramientas de Desarrollo

- **django-extensions**: Herramientas de desarrollo (shell_plus, runserver_plus)

### 2.7 Producción

- **gunicorn**: Servidor WSGI para producción
- **whitenoise**: Servir archivos estáticos en producción

## 3. Estructura de Carpetas del Proyecto

```
/home/qramiroexequiel/Escritorio/1- Sistema de gestión de Pymes/
│
├── config/                          # Configuración principal de Django
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                 # Configuración base
│   │   ├── development.py          # Configuración desarrollo
│   │   └── production.py           # Configuración producción
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── core/                            # Módulo base
│   ├── __init__.py
│   ├── models.py                   # Membership, Company, AuditLog
│   ├── views.py
│   ├── admin.py
│   ├── forms.py
│   ├── services.py                 # Lógica de negocio core
│   ├── middleware.py               # Multi-tenant middleware
│   ├── managers.py                 # QuerySets personalizados
│   ├── mixins.py                   # Mixins para views y models
│   ├── decorators.py               # Decoradores de permisos
│   ├── utils.py                    # Utilidades generales
│   ├── migrations/
│   └── templates/core/
│
├── customers/                       # Módulo de clientes
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── admin.py
│   ├── forms.py
│   ├── services.py
│   ├── migrations/
│   └── templates/customers/
│
├── suppliers/                       # Módulo de proveedores
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── admin.py
│   ├── forms.py
│   ├── services.py
│   ├── migrations/
│   └── templates/suppliers/
│
├── products/                        # Módulo de productos/servicios
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── admin.py
│   ├── forms.py
│   ├── services.py
│   ├── migrations/
│   └── templates/products/
│
├── operations/                      # Módulo de operaciones (ventas/compras)
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── admin.py
│   ├── forms.py
│   ├── services.py
│   ├── migrations/
│   └── templates/operations/
│
├── reports/                         # Módulo de reportes
│   ├── __init__.py
│   ├── models.py                   # Configuraciones de reporte
│   ├── views.py
│   ├── services.py                 # Generación de reportes
│   ├── templates/reports/
│   └── utils.py                    # Utilidades de reportes
│
├── config_app/                     # Módulo de configuración por empresa
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── admin.py
│   ├── forms.py
│   ├── migrations/
│   └── templates/config_app/
│
├── templates/                       # Templates base y compartidos
│   ├── base.html
│   ├── registration/
│   └── includes/
│
├── static/                          # Archivos estáticos
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/                           # Archivos subidos por usuarios
│
├── locale/                          # Traducciones (opcional para v1)
│
├── scripts/                         # Scripts de utilidad
│   ├── setup_initial_data.py
│   └── create_superuser.py
│
├── requirements/                    # Dependencias por entorno
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── docs/                            # Documentación técnica
│   ├── API.md                       # (Para versión futura)
│   └── DEPLOYMENT.md
│
├── .env.example                     # Ejemplo de variables de entorno
├── .gitignore
├── manage.py
├── README.md                        # Documentación técnica
├── PRODUCT_OVERVIEW.md              # Documentación comercial
├── ARCHITECTURE.md                  # Este documento
└── LICENSE                          # Licencia del producto
```

## 4. Lista Exacta de Entidades Principales

### 4.1 Módulo Core

**Company (Empresa)**
- id, name, tax_id (CUIT/RUT/NIT), email, phone, address
- logo, active, created_at, updated_at

**Membership (Membresía Usuario-Empresa)**
- id, user (FK a User estándar de Django), company (FK), role
- active, created_at, updated_at
- Relación: Un usuario puede pertenecer a múltiples empresas con roles distintos

**AuditLog (Auditoría Operativa Básica)**
- id, company (FK), user (FK), action, model_name, object_id, changes (JSON)
- timestamp, ip_address
- **Nota:** Se usa User estándar de Django, NO User personalizado
- **Nota:** Auditoría operativa básica, no sistema de compliance legal

### 4.2 Módulo Customers

**Customer (Cliente)**
- id, company (FK), code, name, tax_id, email, phone, address
- notes, active, created_at, updated_at, created_by

### 4.3 Módulo Suppliers

**Supplier (Proveedor)**
- id, company (FK), code, name, tax_id, email, phone, address
- notes, active, created_at, updated_at, created_by

### 4.4 Módulo Products

**Product (Producto/Servicio)**
- id, company (FK), code, name, description
- type (product/service), price, unit_of_measure, stock (opcional)
- active, created_at, updated_at

**Nota:** Category excluida del MVP v1. Se puede agregar en versiones futuras.

### 4.5 Módulo Operations

**Operation (Operación Unificada: Venta/Compra)**
- id, company (FK), type (sale/purchase), number, date
- customer (FK, nullable), supplier (FK, nullable)
- subtotal, tax, total, status (draft/confirmed/cancelled)
- notes, created_at, updated_at, created_by
- Validación: Si type='sale' entonces customer no nulo. Si type='purchase' entonces supplier no nulo.
- **Lógica de negocio:** Toda la lógica de cálculo y validación en `operations/services.py`

**OperationItem (Item de Operación)**
- id, operation (FK), product (FK), quantity, unit_price, subtotal
- Cálculo de subtotal automático en save()

### 4.6 Módulo Config

**CompanySettings (Configuración por Empresa)**
- id, company (FK one-to-one), currency, tax_rate_default, timezone
- date_format, fiscal_year_start, custom_fields (JSON)

## 5. Alcance Cerrado de la Versión 1 (MVP Vendible)

### 5.1 INCLUYE (Funcionalidades Core)

✅ **Autenticación y Autorización**
- Login/Logout
- Gestión de sesiones
- Recuperación de contraseña (email básico)

✅ **Gestión de Usuarios y Roles**
- CRUD de usuarios por empresa
- Roles: Administrador, Gestor, Operador
- Permisos básicos por módulo

✅ **Gestión de Empresas (Multi-tenant)**
- Registro de empresa
- Configuración inicial
- Logo y datos básicos

✅ **Gestión de Clientes**
- CRUD completo
- Búsqueda y filtros básicos
- Listado paginado

✅ **Gestión de Proveedores**
- CRUD completo
- Búsqueda y filtros básicos
- Listado paginado

✅ **Gestión de Productos/Servicios**
- CRUD completo
- Búsqueda y filtros
- **Nota:** Categorías excluidas del MVP v1

✅ **Registro de Operaciones**
- Modelo unificado Operation para ventas y compras
- Crear operación de tipo venta o compra (con múltiples items)
- Estados: borrador, confirmado, cancelado
- Numeración automática por tipo

✅ **Reportes Básicos**
- Reporte de ventas por período
- Reporte de compras por período
- Resumen de ventas/compras por cliente/proveedor
- Exportación a CSV

✅ **Configuración por Empresa**
- Configuración de moneda
- Tasa de impuesto por defecto
- Datos fiscales

✅ **Auditoría Operativa Básica**
- Registro de creaciones, modificaciones y eliminaciones en entidades principales
- Registro de acciones críticas (confirmar/cancelar operaciones)
- Vista de log por empresa (últimos 30 días)
- **Nota:** Sistema de auditoría operativa básica, no compliance legal

✅ **UI/UX Mínimo Profesional**
- Interfaz responsive (Bootstrap 5)
- Django Templates nativos (sin jQuery)
- HTMX opcional para interacciones simples
- Navegación intuitiva
- Formularios validados
- Mensajes de éxito/error

### 5.2 NO INCLUYE (Versiones Futuras)

❌ Sistema de turnos o agendas
❌ Notificaciones en tiempo real
❌ Dashboard con gráficos complejos
❌ Facturación electrónica
❌ Integraciones con bancos o procesadores de pago
❌ App móvil
❌ API REST pública
❌ Sistema de permisos granular avanzado
❌ Multi-idioma completo
❌ Importación masiva de datos
❌ Exportación a Excel avanzada (solo CSV básico)
❌ Reportes con gráficos
❌ Inventario avanzado con control de stock en tiempo real
❌ Puntos de venta (POS)
❌ Compras con cotizaciones múltiples
❌ Ventas con presupuestos

## 6. Propuesta de Nombre y Estructura del Archivo de Documentación Comercial

**Nombre del archivo:** `PRODUCT_OVERVIEW.md`

**Estructura propuesta:**

```markdown
# Overview del Producto

## 1. Descripción del Sistema
[Descripción clara y orientada a beneficios]

## 2. Problemas que Resuelve
[Lista de problemas concretos y dolorosos que soluciona]

## 3. Cliente Ideal
[Perfil de empresa que necesita este sistema]

## 4. Funcionalidades Principales
[Alcance funcional detallado por módulo]

## 5. Inversión y Modelo de Precios

### Setup Inicial
[Precio y qué incluye]

### Mantenimiento Mensual
[Precio y servicios incluidos]

## 6. Condiciones de Servicio
[Términos y condiciones profesionales]

## 7. Proceso de Implementación
[Pasos y tiempo estimado]

## 8. Soporte y Garantías
[Qué incluye el soporte]
```

## 7. Consideraciones de Seguridad

- Middleware de autenticación obligatorio
- Validación de pertenencia a empresa en todas las vistas
- Protección CSRF nativa de Django
- Sanitización de inputs
- Passwords hasheados (bcrypt via Django)
- Rate limiting en login
- Logs de seguridad

## 8. Preparación para Escalabilidad Futura

- Arquitectura modular permite agregar módulos sin afectar existentes
- Services layer preparado para exponer como API REST
- Modelos diseñados para extensión
- Separación clara de responsabilidades
- Código documentado y estructurado

---

**Versión del Documento:** 2.0
**Fecha:** Enero 2026
**Autor:** Arquitecto de Software

