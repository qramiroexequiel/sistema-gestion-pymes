# 🚀 Suite Business - SaaS de Gestión para PyMEs

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.x-green.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)
![License](https://img.shields.io/badge/License-Comercial-red.svg)

> **Solución multi-tenant diseñada para el aislamiento seguro de datos entre empresas. Organiza ventas, compras, clientes y productos en un solo lugar, para que sepas exactamente cómo va tu negocio sin perder tiempo buscando información.**

---

## 📋 Descripción

**Suite Business** es una plataforma SaaS completa de gestión empresarial diseñada específicamente para pequeñas y medianas empresas. El sistema utiliza una arquitectura **multi-tenant** robusta que garantiza el aislamiento total de datos entre empresas, permitiendo que múltiples organizaciones operen de forma segura en la misma infraestructura.

### 🎯 ¿Para quién es este producto?

- PyMEs con facturación mensual entre $500K y $5M ARS
- Negocios que venden productos o servicios
- Empresas que compran a proveedores regularmente
- Negocios con 1-20 empleados
- Dueños que manejan todo o tienen 1-2 personas de administración

**Problema que resuelve:** Elimina el desorden de Excel, reduce errores humanos, proporciona control total sobre ventas y compras, y centraliza toda la información del negocio en un solo lugar accesible desde cualquier dispositivo.

---

## ✨ Funcionalidades Core

### 📊 Dashboard de KPIs
- Vista general con métricas clave del negocio
- Ventas y compras del mes actual
- Operaciones pendientes
- Clientes y productos activos
- Totales históricos

### 👥 Gestión de Clientes y Proveedores
- CRUD completo con códigos únicos por empresa
- Información de contacto, CUIT/RUT/NIT, direcciones
- Historial de operaciones asociadas
- Estados activo/inactivo

### 📦 Gestión de Productos y Servicios
- Catálogo unificado de productos y servicios
- Control de precios y stock
- Unidades de medida personalizables
- Códigos únicos por empresa

### 💼 Módulo de Operaciones (Ventas/Compras)
- Sistema unificado para ventas y compras
- Creación de operaciones con múltiples ítems
- Estados: Borrador → Confirmado / Cancelado
- Cálculo automático de subtotales, impuestos y totales
- Numeración automática secuencial
- Validaciones de negocio en capa de servicios

### 📈 Reportes con Exportación CSV
- **Ventas por período:** Filtrado por rango de fechas con exportación CSV
- **Compras por período:** Análisis de compras con exportación CSV
- **Resumen por cliente:** Agrupación de ventas por cliente
- **Resumen por proveedor:** Agrupación de compras por proveedor
- Todos los reportes incluyen totales y exportación a CSV

### 🔐 Auditoría de Acciones
- Registro completo de todas las acciones del sistema
- Trazabilidad de cambios (create, update, delete, view)
- Registro de IP y timestamp
- Logs de seguridad para detección de accesos no autorizados

### ⚙️ Configuración por Empresa
- Moneda personalizada
- Tasa de impuesto por defecto
- Zona horaria y formato de fecha
- Inicio del año fiscal
- Campos personalizados (JSON)

---

## 🏗️ Arquitectura Técnica

### Stack Tecnológico

**Backend:**
- **Python 3.12+** - Lenguaje de programación
- **Django 5.x** - Framework web con patrón MVT
- **PostgreSQL** (producción) / SQLite (desarrollo) - Base de datos

**Frontend:**
- **Bootstrap 5** - Framework CSS con diseño Premium SaaS
- **HTMX** - Interacciones dinámicas sin JavaScript complejo
- **Font Awesome 6** - Iconografía profesional
- **Crispy Forms** - Formularios HTML profesionales

**Infraestructura:**
- **Gunicorn** - Servidor WSGI para producción
- **WhiteNoise** - Servicio de archivos estáticos
- **python-decouple** - Gestión de variables de entorno

### Patrones de Diseño Implementados

#### 🔒 Multi-Tenancy con Aislamiento Total
- **Middleware personalizado** (`CompanyMiddleware`) que identifica automáticamente la empresa del usuario
- **Mixins de seguridad** (`CompanyRequiredMixin`, `CompanyFilterMixin`, `CompanyObjectMixin`) que garantizan filtrado por empresa en todas las consultas
- **Managers personalizados** (`CompanyManager`) con métodos `for_company()` obligatorios
- **Validaciones a nivel de modelo** que previenen fugas de datos entre empresas

#### 🎯 Capa de Servicios
- Lógica de negocio separada de las vistas en `operations/services.py`
- Funciones reutilizables para crear operaciones, gestionar ítems, confirmar/cancelar
- Preparado para futura API REST sin refactorizar

#### 🛡️ Seguridad por Capas
- Autenticación con Django Auth
- Roles por empresa (Administrador, Gestor, Operador, Visualizador)
- CSRF protection habilitado
- Headers de seguridad en producción (HSTS, XSS protection, etc.)
- Logging de seguridad para detección de accesos cross-tenant

---

## 💼 Estrategia Comercial

Este proyecto incluye **documentación estratégica completa** para ventas, pricing y onboarding de clientes:

### 📚 Documentos de Estrategia Comercial
- **`ESTRATEGIA_COMERCIAL.md`** - Guía completa de ventas, cliente ideal, propuesta de valor y scripts de venta
- **`ESTRATEGIA_PRICING.md`** - Estrategia de precios, modelos de facturación y análisis de competencia
- **`COPYS_DE_VENTA_PRICING.md`** - Copys listos para usar en ventas y comunicación comercial
- **`PRICING_FINAL.md`** - Precios finales y paquetes del producto

### 📋 Documentos Operativos
- **`ONBOARDING_CLIENTE.md`** - Proceso completo de incorporación de nuevos clientes
- **`DEMO_COMERCIAL_CHECKLIST.md`** - Checklist para realizar demos comerciales exitosas
- **`GUIA_RAPIDA_VENTAS.md`** - Guía rápida para el equipo de ventas
- **`GUIA_RAPIDA_PRICING.md`** - Guía rápida de pricing para ventas

### 📧 Templates Comerciales
- **`OFERTA_WHATSAPP.md`** - Template de oferta para WhatsApp
- **`UPWORK_TEMPLATES.md`** - Templates para propuestas en Upwork

### 📖 Documentación Técnica
- **`ARCHITECTURE.md`** - Documentación técnica detallada de la arquitectura
- **`INFORME_TECNICO.md`** - Análisis técnico completo del sistema
- **`PRODUCCION_READY.md`** - Checklist de producción y estado del proyecto

---

## 🚀 Instalación Rápida

### Prerrequisitos
- Python 3.12 o superior
- pip
- PostgreSQL 14+ (para producción) o SQLite (para desarrollo)
- virtualenv (recomendado)

### Pasos de Instalación

1. **Clonar el repositorio:**
```bash
git clone <url-del-repositorio>
cd "1- Sistema de gestión de Pymes"
```

2. **Crear y activar entorno virtual:**
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias:**
```bash
pip install -r requirements/development.txt
```

4. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus configuraciones (al menos SECRET_KEY)
```

5. **Aplicar migraciones:**
```bash
python manage.py migrate
```

6. **Crear superusuario:**
```bash
python manage.py createsuperuser
```

7. **Ejecutar servidor de desarrollo:**
```bash
python manage.py runserver
```

8. **Acceder a la aplicación:**
```
http://localhost:8000/
```

### 🏭 Despliegue en Producción

Para desplegar en producción, consulta el archivo **`DEPLOY_CHECKLIST.md`** que incluye:
- Configuración de variables de entorno
- Setup de PostgreSQL
- Configuración de servidor web (Nginx/Apache)
- Configuración SSL
- Optimizaciones de seguridad

---

## 🔒 Seguridad (Ciberdefensa)

### Principios de Seguridad Aplicados

#### 🛡️ Aislamiento Multi-Tenant
- **Separación lógica de datos** mediante `company_id` en todas las tablas
- **Middleware obligatorio** que valida membresía activa antes de cada request
- **QuerySets filtrados automáticamente** por empresa en todas las vistas
- **Validaciones a nivel de modelo** que previenen acceso cross-tenant
- **Logging de seguridad** para detectar intentos de acceso no autorizado

#### 🔐 Autenticación y Autorización
- Autenticación robusta con Django Auth
- Roles granulares por empresa (no globales)
- Validación de membresía activa en cada request
- Sesiones seguras con renovación automática

#### 🚨 Protección de Datos
- Variables de entorno para secretos (`.env` excluido del repositorio)
- CSRF protection habilitado en todos los formularios
- Headers de seguridad en producción (HSTS, XSS, Content-Type nosniff)
- Cookies seguras (HttpOnly, Secure, SameSite)
- Validación de entrada en todos los formularios

#### 📊 Auditoría y Monitoreo
- Registro completo de acciones en `AuditLog`
- Logging de seguridad para eventos sospechosos
- Trazabilidad de cambios con IP y timestamp
- Detección de intentos de acceso cross-tenant

---

## 📁 Estructura del Proyecto

```
.
├── config/              # Configuración principal de Django
│   └── settings/        # Settings por entorno (base, development, production)
├── core/                # Módulo base (Company, Membership, AuditLog, middleware)
├── customers/           # Gestión de clientes
├── suppliers/           # Gestión de proveedores
├── products/            # Gestión de productos/servicios
├── operations/          # Registro de operaciones (ventas/compras) + services
├── reports/             # Reportes operativos con exportación CSV
├── config_app/          # Configuración por empresa
├── templates/           # Templates base y por módulo
├── static/              # Archivos estáticos
└── media/               # Archivos subidos por usuarios
```

---

## 🧑‍💻 Desarrollo

### Comandos Útiles

```bash
# Crear migraciones después de cambios en modelos
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recolectar archivos estáticos
python manage.py collectstatic

# Verificar configuración de producción
python manage.py check --deploy
```

### Acceso al Admin de Django
```
http://localhost:8000/admin/
```

---

## 📄 Licencia

Proyecto comercial privado. Todos los derechos reservados.

---

## 🤝 Contribuciones

Este es un proyecto comercial privado. Para consultas o colaboraciones, contactar con los mantenedores del proyecto.

---

## 📞 Soporte

Para soporte técnico o consultas comerciales, consultar la documentación estratégica incluida en el repositorio o contactar al equipo del proyecto.

---

<div align="center">

**Desarrollado con ❤️ para PyMEs que buscan crecer de forma organizada**

[⭐ Si este proyecto te resulta útil, considera darle una estrella ⭐](#)

</div>
