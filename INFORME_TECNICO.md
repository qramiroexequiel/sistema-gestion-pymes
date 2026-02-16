# Informe Técnico — Sistema de Gestión de Pymes

**Proyecto:** Sistema de gestión interna multi-empresa (Suite Business)  
**Fecha del análisis:** 16 de febrero de 2026

---

## 1. Arquitectura y Stack Tecnológico

### Backend
- **Lenguaje:** Python 3.12+
- **Framework:** Django 5.x (patrón MVT: Model-View-Template)
- **Configuración:** Settings divididos por entorno en `config/settings/`:
  - `base.py`: configuración común (apps, middleware, i18n, crispy, login, sesión)
  - `development.py`: DEBUG, SQLite, `ALLOWED_HOSTS`, logging a consola
  - `production.py`: PostgreSQL vía `dj-database-url`, SSL, HSTS, WhiteNoise, logging a archivo
- **Librerías clave:** `python-decouple` (variables de entorno), `dj-database-url` (solo en producción), `django-crispy-forms`, `crispy-bootstrap5`, `Pillow` (imágenes), `gunicorn` y `whitenoise` (referidos en documentación para producción).

### Frontend
- **Templates:** Motor de plantillas Django, con herencia desde `templates/base.html` y `templates/base_auth.html`.
- **UI:** Bootstrap 5, diseño “Premium SaaS” con variables CSS (paleta, sidebar, tipografía Inter).
- **Interactividad:** HTMX (vía CDN) para actualizaciones parciales (p. ej. listados de operaciones).
- **Formularios:** django-crispy-forms con pack Bootstrap 5 en módulos `customers`, `suppliers`, `products`, `operations`.
- **Iconos:** Font Awesome 6 (CDN).

### Base de datos
- **Desarrollo:** SQLite (`db.sqlite3` en `BASE_DIR`).
- **Producción:** PostgreSQL; conexión mediante `DATABASE_URL` y `dj_database_url` (con `conn_max_age` y `conn_health_checks`).

---

## 2. Estructura de Archivos

| Carpeta / Módulo | Propósito |
|------------------|-----------|
| **config/** | Configuración global: `urls.py`, `wsgi.py`, `settings/` (base, development, production). |
| **core/** | Núcleo multi-tenant: modelos `Company`, `Membership`, `AuditLog`; mixins de vistas (`CompanyRequiredMixin`, `RoleRequiredMixin`, `CompanyFilterMixin`, `CompanyObjectMixin`, `HTMXResponseMixin`); `CompanyManager`/`CompanyQuerySet`; middleware de empresa; context processor; vistas dashboard, perfil, selección de empresa; handlers 404/500. |
| **customers/** | CRUD de clientes: modelo `Customer` (por empresa), vistas list/create/update/delete, formularios Crispy, auditoría. |
| **suppliers/** | CRUD de proveedores: modelo `Supplier`, misma estructura que clientes. |
| **products/** | CRUD de productos/servicios: modelo `Product` (tipo producto/servicio, código, precio, stock, unidad), vistas y forms. |
| **operations/** | Operaciones comerciales unificadas: modelos `Operation` (venta/compra) y `OperationItem`; capa de servicios (`services.py`: crear operación, ítems, confirmar/cancelar, recalcular totales); vistas list/create/detail con formset de ítems; soporte HTMX en listado. |
| **reports/** | Reportes: lista de reportes; ventas por período; compras por período; resumen por cliente; resumen por proveedor; exportación CSV. |
| **config_app/** | Configuración por empresa: modelo `CompanySettings` (moneda, tasa de impuesto, timezone, formato de fecha, año fiscal, `custom_fields` JSON). Vistas/URLs mínimas. |
| **templates/** | Base HTML, login, partials; cada app aporta sus propios templates bajo `app/templates/app/`. |
| **static/** | Archivos estáticos (referenciados en `STATICFILES_DIRS`). |
| **media/** | Archivos subidos (logos de empresa, etc.). |

La documentación interna (`ARCHITECTURE.md`) describe además una carpeta `requirements/` (p. ej. `development.txt`, `production.txt`), que **no está presente** en la raíz del proyecto.

---

## 3. Flujo de Datos

1. **Request HTTP** → `config/urls.py` enruta a la app correspondiente (`core`, `customers`, `suppliers`, `products`, `operations`, `reports`, `config_app`).

2. **Middleware:**  
   `SecurityMiddleware` → `SessionMiddleware` → `CommonMiddleware` → `CsrfViewMiddleware` → `AuthenticationMiddleware` → **`CompanyMiddleware`** → `MessageMiddleware` → `XFrameOptionsMiddleware`.  
   `CompanyMiddleware` establece `request.current_company` y `request.current_membership` a partir de la sesión (`current_company_id`) y valida membresía activa; si no hay empresa y la ruta es protegida, deja `current_company = None` (las vistas mixins se encargan de redirigir o denegar).

3. **Vistas:**  
   - Rutas públicas: login, logout, selección de empresa (sin empresa obligatoria).  
   - Rutas protegidas: usan `LoginRequiredMixin` y `CompanyRequiredMixin` (redirección a selección de empresa o a login si no hay membresías).  
   - Listados/objetos: `CompanyFilterMixin` fuerza `get_queryset().for_company(company)`; Detail/Update/Delete usan `CompanyObjectMixin` para obtener el objeto solo si pertenece a la empresa.  
   - Reportes y operaciones de escritura usan además `RoleRequiredMixin` (roles admin, manager, operator).

4. **Lógica de negocio:**  
   En **operations** la lógica no está en las vistas sino en `operations/services.py`: creación de operación, alta/baja/actualización de ítems, confirmación/cancelación, recálculo de totales. Las vistas llaman a estos servicios y, en creación/edición, registran auditoría con `core.utils.log_audit` y `get_client_ip`.

5. **Persistencia:**  
   Acceso a datos vía ORM Django; modelos de negocio heredan `CompanyModelMixin` y usan `CompanyManager`, de modo que todas las consultas deben usar explícitamente `.for_company(company)` (las vistas lo garantizan mediante los mixins).

6. **Respuesta:**  
   HTML completo o fragmentos HTMX según el header `HX-Request`; en reportes, también respuestas CSV según parámetro `format=csv`.

---

## 4. Funcionalidades Core

- **Autenticación y multi-tenant:** Login/logout, selección de empresa activa, perfil de usuario. Varias empresas por usuario mediante `Membership` y roles (Administrador, Gestor, Operador, Visualizador).
- **Dashboard:** KPIs (ventas/compras del mes, operaciones pendientes, clientes activos, productos activos, totales históricos).
- **Clientes:** Alta, edición, listado, baja lógica (activo/inactivo); códigos únicos por empresa.
- **Proveedores:** Misma funcionalidad que clientes.
- **Productos/Servicios:** CRUD; tipo producto/servicio; código, precio, stock, unidad de medida; activo/inactivo.
- **Operaciones (ventas y compras):** Crear operación (venta con cliente, compra con proveedor), ítems con producto, cantidad y precio; estados borrador → confirmado / cancelado; totales calculados en capa de servicios; listado con filtros (tipo, estado, búsqueda) y paginación; soporte HTMX en tabla.
- **Reportes:** Ventas por período; compras por período; resumen por cliente; resumen por proveedor; filtro por fechas; exportación CSV.
- **Configuración por empresa:** Moneda, tasa de impuesto por defecto, zona horaria, formato de fecha, inicio de año fiscal, campos personalizados (JSON) — modelo y admin; flujo de uso en app aún limitado.
- **Auditoría:** Registro de acciones (create, update, delete, view, login, logout) en `AuditLog` (empresa, usuario, modelo, cambios, IP, timestamp).
- **Manejo de errores:** Páginas 404 y 500 propias con branding.

---

## 5. Seguridad y Modelos

### Modelos de datos
- **core:** `Company` (nombre, CUIT, contacto, logo, activo, is_demo), `Membership` (user, company, role, activo), `AuditLog` (company, user, action, model_name, object_id, changes JSON, IP).  
- **Abstracto:** `CompanyModelMixin`: `company` FK obligatoria, `created_at`, `updated_at`, `created_by`; índice en `company`.  
- **Negocio:** `Customer`, `Supplier`, `Product` heredan `CompanyModelMixin` y usan `CompanyManager`; `Operation` también (con FK a Customer/Supplier, totales, estado); `OperationItem` enlaza operación y producto con cantidad, precio unitario y subtotal.  
- **config_app:** `CompanySettings` (OneToOne con Company, moneda, impuesto, timezone, etc.).  
- Unicidades y filtros por empresa están asegurados con `unique_together`/índices y uso de `for_company(company)` en todas las consultas desde vistas.

### Patrones de diseño
- **MVT (Django):** Modelos, vistas (clases y funciones), templates separados por app.
- **Capa de servicios:** En `operations`, la lógica de negocio (crear operación, ítems, confirmar, cancelar, totales) está en `services.py`, no en las vistas; las vistas delegan y solo orquestan formularios, redirecciones y auditoría.
- **Repository-like:** `CompanyManager` + `CompanyQuerySet` ofrecen `for_company(company)` y `get_or_404_for_company(company, **kwargs)`; no hay una capa Repository explícita, pero el acceso a datos queda centralizado y siempre filtrado por empresa.
- **Mixins:** Reutilización de requisitos (empresa, rol, objeto por empresa, contexto de empresa, respuestas HTMX) en vistas sin duplicar lógica.

### Seguridad
- CSRF, validadores de contraseña por defecto de Django, sesiones con duración y renovación configuradas.
- Producción: `SECURE_SSL_REDIRECT`, cookies seguras, HSTS, XSS/Content-Type nosniff, `SESSION_COOKIE_HTTPONLY`/`SAMESITE`.
- Aislamiento por tenant: middleware + mixins aseguran que no se liste ni acceda a datos de otra empresa; intentos incorrectos se registran en logger `security`.
- Auditoría de acciones y IP en operaciones sensibles.

---

## 6. Estado del Proyecto

- **Tipo:** MVP funcional orientado a producción. La documentación (`PRODUCCION_READY.md`) lo marca como “Listo para producción” (settings, seguridad básica, 404/500, separación demo/real, documentación de deploy y onboarding).
- **Dependencias y configuración:**
  - **Faltantes en el repositorio:**  
    - No existe `requirements.txt` ni carpeta `requirements/` con `development.txt` o `production.txt`, a pesar de que el README y `DEPLOY_CHECKLIST.md` referencian `pip install -r requirements/development.txt` y `requirements/production.txt`.  
    - No hay archivo `.env` ni `.env.example` en la raíz; el checklist de deploy indica copiar `.env.example` y completar variables.  
  - **Implicación:** Quien clone el proyecto debe deducir dependencias (por ejemplo con `pip freeze` desde un venv ya configurado) y crear `.env` según la documentación. Tener `requirements/` y `.env.example` mejoraría la reproducibilidad y el onboarding.

- **Configuración de Django:** `config/settings/__init__.py` no define `DJANGO_SETTINGS_MODULE`; `manage.py` usa por defecto `config.settings`. Para elegir entorno se suele usar la variable de entorno `DJANGO_SETTINGS_MODULE` (p. ej. `config.settings.development` o `config.settings.production`) o un `DJANGO_ENV` que el `__init__.py` de settings cargue el módulo correspondiente; conviene documentarlo si ya se usa en algún despliegue.

---

## 7. Conclusión sobre escalabilidad para una PyME real

- **Fortalezas:** Multi-tenant por empresa bien integrado (modelo, middleware, managers, mixins), roles por empresa, auditoría, capa de servicios en operaciones, reportes con exportación CSV, configuración por empresa (moneda, impuestos, timezone) y documentación de deploy y seguridad. La base es sólida para un uso real en una PyME (una o pocas empresas, varios usuarios por empresa).
- **Escalabilidad:** La arquitectura aguanta bien crecimiento moderado (más usuarios, más operaciones, más empresas en el mismo esquema). Para crecer más (muchas empresas o alto volumen), habría que valorar: optimización de consultas (select_related/prefetch ya usados en varios sitios), índices adicionales si aparecen cuellos de botella, y si en el futuro se expone API REST (la separación en servicios facilita reutilizar la lógica).
- **Recomendaciones inmediatas:** Añadir en el repositorio `requirements/base.txt` (o `development.txt`) y `requirements/production.txt` a partir de las dependencias reales del proyecto, y un `.env.example` con las variables documentadas en `DEPLOY_CHECKLIST.md`, para que el proyecto sea reproducible y desplegable sin depender de un venv preexistente.

---

*Informe generado a partir del análisis del código y la documentación del proyecto.*
