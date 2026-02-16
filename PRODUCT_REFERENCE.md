# Documento de Referencia Completo - Custom Internal Management System

**Versión:** 1.0  
**Fecha:** Enero 2026  
**Propósito:** Documento de referencia completo para ventas, propuestas y presentaciones

---

## 1. Descripción del Producto a Alto Nivel

### 1.1 ¿Qué es?

El **Custom Internal Management System** es un sistema web de gestión interna diseñado específicamente para pequeñas y medianas empresas (PyMES). Es una solución completa, lista para usar, que centraliza todas las operaciones comerciales diarias en una plataforma accesible desde cualquier navegador.

### 1.2 ¿Para qué sirve?

El sistema permite a las empresas:

- **Centralizar información comercial:** Clientes, proveedores, productos y operaciones en un solo lugar
- **Registrar operaciones comerciales:** Ventas y compras con trazabilidad completa
- **Generar reportes operativos:** Análisis de ventas, compras y resúmenes por cliente/proveedor
- **Gestionar múltiples usuarios:** Control de acceso con roles y permisos por empresa
- **Exportar datos:** Exportación completa en CSV para análisis externo

### 1.3 Diferencia Clave

**Implementación rápida:** El sistema está funcionando en 7-14 días calendario, no en meses. A diferencia de desarrollos custom que toman 3-6 meses, este sistema se entrega completamente configurado y listo para usar.

**Valor principal:** Ordena las operaciones diarias de una empresa sin la complejidad, el costo ni el tiempo de implementación de sistemas ERP tradicionales.

### 1.4 Propuesta de Valor

- **Rápido:** De Excel a sistema profesional en menos de 2 semanas
- **Seguro:** Multi-tenant probado, datos completamente aislados
- **Propiedad de datos:** Exportación completa, sin lock-in
- **Profesional:** Tecnología empresarial (Django + PostgreSQL)
- **Soporte incluido:** Mantenimiento mensual con actualizaciones y soporte técnico

---

## 2. Funcionalidades Completas por Módulo

### 2.1 Autenticación y Seguridad

**Login y Sesiones:**
- Sistema de login seguro con autenticación estándar de Django
- Gestión de sesiones con protección CSRF nativa
- Recuperación de contraseña vía email
- Rate limiting en intentos de login (protección contra fuerza bruta)

**Roles de Usuario:**
- **ADMIN:** Acceso completo, puede gestionar usuarios, confirmar/cancelar operaciones, eliminar registros
- **MANAGER:** Puede crear/editar operaciones, confirmar/cancelar, gestionar clientes/proveedores/productos
- **OPERATOR:** Puede crear/editar operaciones en borrador, gestionar clientes/proveedores/productos
- **VIEWER:** Solo lectura, puede ver reportes y listados

**Control de Acceso:**
- Todas las rutas protegidas requieren autenticación
- Validación de pertenencia a empresa activa
- Permisos por módulo según rol asignado

### 2.2 Gestión de Usuarios y Empresas

**Sistema Multi-Tenant:**
- Una instancia del sistema, múltiples empresas
- Cada empresa tiene sus datos completamente aislados
- Usuarios pueden pertenecer a múltiples empresas con roles distintos

**Gestión de Empresas:**
- Registro de empresa con datos completos (nombre, CUIT/RUT/NIT, email, teléfono, dirección)
- Logo personalizado por empresa
- Estado activo/inactivo
- Configuración inicial durante setup

**Selección de Empresa Activa:**
- Usuario selecciona empresa activa al iniciar sesión
- Sistema recuerda selección en sesión
- Cambio de empresa activa disponible en cualquier momento

**Gestión de Usuarios:**
- CRUD de usuarios por empresa
- Asignación de roles por empresa
- Membresías activas/inactivas
- Un usuario puede tener diferentes roles en diferentes empresas

### 2.3 Gestión de Clientes

**CRUD Completo:**
- Crear, leer, actualizar y eliminar clientes
- Campos: código (único por empresa), nombre, CUIT/RUT/NIT, email, teléfono, dirección, notas
- Estado activo/inactivo
- Timestamps: fecha de creación y última actualización
- Usuario que creó el registro

**Búsqueda y Filtros:**
- Búsqueda por: nombre, código, email, CUIT/RUT/NIT
- Filtro por estado: activos, inactivos, todos
- Búsqueda en tiempo real con debounce (500ms)
- Paginación: 25 registros por página

**Funcionalidades Adicionales:**
- Exportación CSV completa con todos los campos
- Historial de operaciones asociadas al cliente
- Validación: código único por empresa

**Protección Multi-Tenant:**
- Solo muestra clientes de la empresa activa
- Imposible acceder a clientes de otra empresa por ID (retorna 404)
- Todas las consultas filtran automáticamente por empresa

### 2.4 Gestión de Proveedores

**CRUD Completo:**
- Mismo patrón y funcionalidades que clientes
- Campos idénticos: código, nombre, CUIT/RUT/NIT, email, teléfono, dirección, notas
- Estado activo/inactivo
- Timestamps y usuario creador

**Búsqueda y Filtros:**
- Búsqueda por: nombre, código, email, CUIT/RUT/NIT
- Filtro por estado: activos, inactivos, todos
- Búsqueda en tiempo real
- Paginación: 25 registros por página

**Funcionalidades Adicionales:**
- Exportación CSV completa
- Historial de operaciones asociadas al proveedor
- Validación: código único por empresa

**Protección Multi-Tenant:**
- Aislamiento completo por empresa
- Mismas garantías de seguridad que clientes

### 2.5 Gestión de Productos/Servicios

**CRUD Completo:**
- Crear, leer, actualizar y eliminar productos/servicios
- Tipo: Producto o Servicio
- Campos: código (único por empresa), nombre, descripción, precio, unidad de medida, stock (opcional)
- Estado activo/inactivo
- Timestamps y usuario creador

**Búsqueda y Filtros:**
- Búsqueda por: nombre, código, descripción
- Filtro por tipo: productos, servicios, todos
- Filtro por estado: activos, inactivos, todos
- Búsqueda en tiempo real
- Paginación: 25 registros por página

**Funcionalidades Adicionales:**
- Exportación CSV completa con todos los campos
- Validación: código único por empresa
- Precio en formato decimal (12 dígitos, 2 decimales)

**Limitaciones del MVP:**
- **NO incluye:** Categorías de productos (excluidas del MVP v1)
- **NO incluye:** Variantes de productos (tallas, colores, etc.)
- **NO incluye:** Control de stock avanzado en tiempo real (campo stock es opcional)

**Protección Multi-Tenant:**
- Aislamiento completo por empresa
- Mismas garantías de seguridad que otros módulos

### 2.6 Operaciones Comerciales (Ventas y Compras)

**Modelo Unificado:**
- Un solo modelo `Operation` para ventas y compras
- Campo `type` distingue entre 'sale' (venta) y 'purchase' (compra)
- Misma lógica y funcionalidades para ambos tipos

**Creación de Operaciones:**
- Crear operación con múltiples items (productos/servicios)
- Formulario con inline formset para agregar items dinámicamente
- Cada item incluye: producto, cantidad, precio unitario, subtotal (calculado automáticamente)

**Estados de Operación:**
- **Borrador:** Operación en creación, puede editarse
- **Confirmado:** Operación finalizada, no puede editarse
- **Cancelado:** Operación anulada, no puede editarse

**Validaciones Automáticas:**
- Venta (`type='sale'`) requiere cliente obligatorio
- Compra (`type='purchase'`) requiere proveedor obligatorio
- Cliente/proveedor debe pertenecer a la empresa activa
- Items deben tener producto válido y cantidades > 0

**Cálculos Automáticos:**
- Subtotal de cada item: cantidad × precio unitario
- Subtotal de operación: suma de subtotales de items
- Impuesto: calculado según tasa configurada por empresa
- Total: subtotal + impuesto
- Todos los cálculos se realizan en backend (`operations/services.py`)

**Numeración Automática:**
- Numeración automática por tipo de operación
- Formato: V-0001, V-0002 (ventas), C-0001, C-0002 (compras)
- Sin duplicados garantizado

**Acciones Disponibles:**
- **Confirmar:** Cambia estado de borrador a confirmado (solo ADMIN, MANAGER)
- **Cancelar:** Cambia estado a cancelado (solo ADMIN, MANAGER)
- **Editar:** Solo si está en estado borrador (ADMIN, MANAGER, OPERATOR)
- **Ver detalle:** Todos los roles con acceso

**Exportación CSV:**
- Exportación con filtros: tipo, estado, búsqueda por número/cliente/proveedor
- Columnas: fecha, tipo, número, cliente/proveedor, subtotal, impuesto, total, estado
- Respeta filtros activos en pantalla

**Protección Multi-Tenant:**
- Solo muestra operaciones de la empresa activa
- Imposible acceder a operaciones de otra empresa por ID (retorna 404)
- Imposible confirmar/cancelar operaciones de otra empresa

### 2.7 Reportes Operativos

**Reporte de Ventas por Período:**
- Filtro por rango de fechas (fecha inicio, fecha fin)
- Muestra todas las ventas confirmadas en el período
- Columnas: número, fecha, cliente, subtotal, impuesto, total
- Totales: subtotales, impuestos y totales agregados
- Exportación CSV disponible

**Reporte de Compras por Período:**
- Filtro por rango de fechas
- Muestra todas las compras confirmadas en el período
- Columnas: número, fecha, proveedor, subtotal, impuesto, total
- Totales agregados
- Exportación CSV disponible

**Resumen por Cliente:**
- Agrupa ventas por cliente
- Muestra: cliente, cantidad de operaciones, total de ventas
- Ordenado por total descendente
- Exportación CSV disponible

**Resumen por Proveedor:**
- Agrupa compras por proveedor
- Muestra: proveedor, cantidad de operaciones, total de compras
- Ordenado por total descendente
- Exportación CSV disponible

**Características de Reportes:**
- Solo datos de la empresa activa
- Solo operaciones confirmadas (excluye borradores y canceladas)
- Filtros configurables por usuario
- Exportación CSV con mismos datos mostrados en pantalla

**Limitaciones del MVP:**
- **NO incluye:** Gráficos o visualizaciones
- **NO incluye:** Dashboards complejos
- **NO incluye:** Análisis BI avanzado
- **NO incluye:** Comparativas entre períodos automáticas

### 2.8 Exportación de Datos

**Módulos con Exportación CSV:**
- Operaciones (con filtros: tipo, estado, búsqueda)
- Clientes (con filtros: búsqueda, estado)
- Proveedores (con filtros: búsqueda, estado)
- Productos/Servicios (con filtros: tipo, búsqueda, estado)

**Características Técnicas:**
- Formato: CSV con encoding UTF-8 + BOM (compatible con Excel)
- Headers claros y estables
- Respeta filtros activos en pantalla
- Sin limitaciones de cantidad de registros
- Descarga directa (no pantalla intermedia)

**Política de Exportación:**
- Disponible en cualquier momento
- Sin restricciones ni costos adicionales
- Sin necesidad de solicitudes especiales
- Exportación completa de todos los datos operativos

**Compatibilidad:**
- Excel (Windows, Mac)
- Google Sheets
- Cualquier herramienta de análisis que lea CSV
- LibreOffice Calc

### 2.9 Auditoría Operativa

**Registro de Acciones:**
- **Creaciones:** Registro cuando se crea cliente, proveedor, producto, operación
- **Modificaciones:** Registro cuando se modifica cualquier entidad principal
- **Eliminaciones:** Registro cuando se elimina cliente, proveedor, producto
- **Acciones críticas:** Confirmar operación, cancelar operación

**Datos Registrados:**
- Usuario que realizó la acción
- Empresa (contexto multi-tenant)
- Tipo de acción (create, update, delete, confirm, cancel)
- Modelo afectado (Customer, Supplier, Product, Operation)
- ID del objeto afectado
- Cambios realizados (en formato JSON para updates)
- Dirección IP del usuario
- Timestamp preciso

**Vista de Auditoría:**
- Log por empresa (solo muestra acciones de la empresa activa)
- Últimos 30 días de actividad
- Filtrable por usuario, acción, modelo
- Información completa de trazabilidad

**Limitaciones:**
- **NO es:** Sistema de compliance legal (SOX, HIPAA, etc.)
- **NO registra:** Login/logout (opcional, no implementado en MVP)
- **NO incluye:** Retención a largo plazo (solo últimos 30 días visibles)
- **Es:** Auditoría operativa básica para rastrear quién hizo qué

### 2.10 Configuración por Empresa

**Datos de Empresa:**
- Nombre, CUIT/RUT/NIT, email, teléfono, dirección
- Logo personalizado (imagen)
- Estado activo/inactivo

**Configuración Operativa:**
- Moneda (USD, EUR, ARS, etc.)
- Tasa de impuesto por defecto (para cálculos automáticos)
- Formato de fecha preferido
- Zona horaria

**Personalización:**
- Logo visible en interfaz
- Datos fiscales para reportes
- Configuración de impuestos para cálculos automáticos

**Acceso:**
- Solo ADMIN puede modificar configuración
- Cambios afectan a toda la empresa
- Historial de cambios en auditoría

---

## 3. Arquitectura Técnica (Lenguaje Comprensible)

### 3.1 Stack Tecnológico

**Backend:**
- **Python 3.12+:** Lenguaje de programación moderno, eficiente y ampliamente utilizado
- **Django 5.x:** Framework web empresarial, seguro y probado en producción
- **PostgreSQL 14+:** Base de datos relacional robusta, estándar en aplicaciones empresariales

**Frontend:**
- **Bootstrap 5:** Framework CSS para interfaz responsive y profesional
- **Django Templates:** Sistema de templates nativo, sin dependencias JavaScript complejas
- **HTMX (opcional):** Biblioteca ligera para interacciones dinámicas sin recargar página completa
- **Font Awesome 6:** Iconografía profesional y consistente

**Seguridad:**
- **Django Auth:** Sistema de autenticación nativo, probado y seguro
- **Protección CSRF:** Nativa de Django, previene ataques cross-site
- **Rate Limiting:** Protección contra ataques de fuerza bruta en login
- **Password Hashing:** Bcrypt, estándar de la industria

### 3.2 Arquitectura Multi-Tenant

**Modelo de Separación:**
- Base de datos compartida con separación lógica mediante `company_id`
- Todas las entidades de negocio tienen un campo `company` (Foreign Key)
- Todas las consultas filtran automáticamente por empresa activa

**Ventajas Comerciales:**
- **Setup rápido:** No requiere crear bases de datos o schemas por cliente
- **Mantenimiento simple:** Un solo backup cubre todos los clientes
- **Migraciones unificadas:** Un comando actualiza todos los clientes
- **Costos predecibles:** Hosting fijo independiente del número de clientes
- **Monitoreo centralizado:** Una sola instancia a monitorear

**Escalabilidad:**
- Diseñado para 10-100 empresas sin refactorizar
- Optimizado con índices compuestos (company + campo_búsqueda)
- Consultas eficientes gracias a filtrado por empresa

**Aislamiento Garantizado:**
- Middleware valida pertenencia a empresa antes de establecer contexto
- Managers personalizados requieren `for_company()` explícito
- Mixins en vistas previenen acceso cross-tenant
- Doble verificación en servicios y modelos

### 3.3 Capas de la Aplicación

```
┌─────────────────────────────────────┐
│   Templates (Interfaz de Usuario)   │  ← Bootstrap 5, HTML, HTMX
├─────────────────────────────────────┤
│   Views (Lógica de Presentación)    │  ← Coordinación, validación básica
├─────────────────────────────────────┤
│   Services (Lógica de Negocio)      │  ← Cálculos, validaciones complejas
├─────────────────────────────────────┤
│   Models (Capa de Datos)            │  ← Estructura, validaciones de modelo
├─────────────────────────────────────┤
│   Database (PostgreSQL)             │  ← Almacenamiento persistente
└─────────────────────────────────────┘
```

**Services Layer:**
- Toda la lógica de negocio está separada de las vistas
- Permite reutilización de código
- Facilita testing unitario
- Preparado para exponer como API REST en el futuro sin refactorizar

**Views:**
- Solo se encargan de presentación y coordinación
- Validación básica de formularios
- Delegación de lógica compleja a services

**Models:**
- Estructura de datos con validaciones a nivel de base de datos
- Relaciones entre entidades
- Índices para optimización de consultas

### 3.4 Módulos Principales

**core:**
- Funcionalidades base del sistema
- Autenticación, usuarios, empresas
- Middleware multi-tenant
- Managers y mixins de seguridad
- Utilidades compartidas (auditoría, exportación CSV)

**customers:**
- Gestión completa de clientes
- CRUD, búsqueda, filtros, exportación

**suppliers:**
- Gestión completa de proveedores
- Mismo patrón que customers

**products:**
- Gestión de productos y servicios
- CRUD, búsqueda, filtros, exportación

**operations:**
- Registro de ventas y compras
- Lógica de negocio en services
- Cálculos automáticos, validaciones

**reports:**
- Generación de reportes operativos
- Filtros por fecha, agrupaciones
- Exportación CSV

**config_app:**
- Configuración por empresa
- Moneda, impuestos, datos fiscales

---

## 4. Seguridad y Aislamiento Multi-Tenant

### 4.1 Protecciones Implementadas

**Middleware (`core/middleware.py`):**
- Valida que el usuario tenga `Membership` activa en la empresa seleccionada
- Verifica que la empresa esté activa (`company.active=True`)
- Establece `request.current_company` solo si validación pasa
- Limpia sesión si membresía deja de existir
- Auto-selecciona primera empresa disponible si no hay selección

**Managers (`core/managers.py`):**
- `CompanyManager` NO filtra automáticamente (evita falsa sensación de seguridad)
- Método explícito `for_company(company)` obligatorio en todas las consultas
- `get_or_404_for_company()` con validación de pertenencia

**Mixins (`core/mixins.py`):**
- `CompanyRequiredMixin`: Requiere empresa activa, redirige si no hay
- `CompanyFilterMixin`: Filtra automáticamente querysets por empresa
- `CompanyObjectMixin`: Valida que objeto pertenezca a empresa activa
- `RoleRequiredMixin`: Valida permisos según rol en empresa activa

**Validaciones en Services:**
- Todos los services reciben `company` como parámetro explícito
- Validación de pertenencia antes de crear/modificar
- Lanzan excepciones si hay discrepancia de empresa

### 4.2 Garantías de Aislamiento

**Imposible Acceso Cross-Tenant:**
- Intentar acceder a objeto de otra empresa por ID retorna 404
- No hay forma de "adivinar" IDs de otra empresa
- Todas las consultas filtran por empresa activa

**Filtrado Automático:**
- Listados solo muestran datos de empresa activa
- Búsquedas solo buscan en empresa activa
- Reportes solo incluyen datos de empresa activa
- Exportaciones solo exportan datos de empresa activa

**Logging de Seguridad:**
- Registra intentos de acceso cross-tenant (nivel WARNING)
- Registra discrepancias de company detectadas (nivel ERROR)
- Incluye: user_id, username, company_id, path, method, IP, user_agent
- Logs en archivo rotativo en producción, consola en desarrollo

**Doble Verificación:**
- Middleware valida antes de establecer contexto
- Mixins validan en vistas
- Services validan en lógica de negocio
- Models tienen constraints a nivel de base de datos

### 4.3 Seguridad de Datos

**Autenticación:**
- Obligatoria para todas las rutas protegidas
- Passwords hasheados con bcrypt (estándar de Django)
- Rate limiting en intentos de login
- Sesiones seguras con protección CSRF

**Roles y Permisos:**
- Roles definidos por empresa activa
- Un usuario puede tener diferentes roles en diferentes empresas
- Permisos validados en cada acción
- ADMIN tiene acceso completo, otros roles tienen restricciones

**Protección de Datos:**
- Sanitización de inputs (Django lo hace automáticamente)
- Protección SQL injection (ORM de Django previene esto)
- Protección XSS (templates de Django escapan automáticamente)
- Protección CSRF (tokens en todos los formularios)

**Backups:**
- Backup diario automático de toda la base de datos
- Retención de backups por 30 días
- Restauración disponible en caso de necesidad

---

## 5. Experiencia de Usuario

### 5.1 Interfaz

**Diseño Responsive:**
- Bootstrap 5 garantiza que funcione en desktop, tablet y móvil
- Layout se adapta automáticamente al tamaño de pantalla
- Navegación clara y accesible en todos los dispositivos

**Navegación Intuitiva:**
- Menú principal con acceso a todos los módulos
- Breadcrumbs para orientación
- Iconos Font Awesome para identificación visual rápida
- Colores consistentes y profesionales

**Formularios:**
- Validación en tiempo real (feedback inmediato)
- Mensajes de error claros y específicos
- Mensajes de éxito después de acciones
- Campos requeridos claramente marcados

**Consistencia:**
- Mismo patrón de diseño en todos los módulos
- Botones con iconos y texto
- Tablas con estilo uniforme
- Cards y alerts con diseño consistente

### 5.2 Rendimiento y Fluidez

**HTMX para Interactividad:**
- Actualizaciones parciales sin recargar página completa
- Búsqueda en tiempo real con debounce (500ms)
- Filtros que actualizan resultados sin recargar
- Paginación que carga solo la lista, no toda la página

**Optimizaciones de Base de Datos:**
- Índices compuestos para búsquedas rápidas: `(company, name)`, `(company, code)`, etc.
- Paginación eficiente: 25 registros por página
- Select_related y prefetch_related para evitar consultas N+1
- Consultas optimizadas en services

**Rendimiento Percibido:**
- Respuesta inmediata a acciones del usuario
- Sin tiempos de espera largos
- Feedback visual durante operaciones (mensajes, estados)

### 5.3 Usabilidad

**Búsqueda y Filtros:**
- Visibles y accesibles en todos los listados
- Búsqueda por múltiples campos simultáneamente
- Filtros claros y fáciles de usar
- Resultados actualizados en tiempo real

**Acciones Claras:**
- Botones con iconos descriptivos
- Texto explicativo en cada acción
- Confirmaciones para acciones destructivas (eliminar)
- Estados visuales (badges para estados de operaciones)

**Feedback Inmediato:**
- Mensajes de éxito después de crear/editar/eliminar
- Mensajes de error claros si algo falla
- Validaciones que se muestran mientras el usuario escribe
- Estados de carga cuando aplica

**Exportación CSV:**
- Un solo clic en botón "Export CSV"
- Descarga directa, sin pantallas intermedias
- Nombre de archivo descriptivo con nombre de empresa
- Respeta filtros activos automáticamente

---

## 6. Exportación de Datos y Propiedad

### 6.1 Funcionalidad de Exportación

**Disponibilidad:**
- Disponible en todos los módulos principales: Operaciones, Clientes, Proveedores, Productos
- Botón visible y accesible en cada listado
- Sin restricciones de cantidad de registros
- Sin necesidad de permisos especiales (cualquier usuario autenticado puede exportar)

**Formato Técnico:**
- CSV con encoding UTF-8 + BOM (Byte Order Mark)
- Compatible con Excel (Windows y Mac)
- Compatible con Google Sheets
- Compatible con cualquier herramienta que lea CSV estándar

**Filtros Respetados:**
- Si hay búsqueda activa, solo exporta resultados de búsqueda
- Si hay filtros activos (tipo, estado, etc.), solo exporta lo filtrado
- Si no hay filtros, exporta todos los registros de la empresa activa
- Filtros se pasan automáticamente en la URL de exportación

**Columnas Exportadas:**
- **Operaciones:** Fecha, Tipo, Número, Cliente/Proveedor, Subtotal, Impuesto, Total, Estado
- **Clientes:** Código, Nombre, CUIT/RUT/NIT, Email, Teléfono, Dirección, Estado
- **Proveedores:** Código, Nombre, CUIT/RUT/NIT, Email, Teléfono, Dirección, Estado
- **Productos:** Código, Nombre, Tipo, Precio, Unidad de Medida, Descripción, Estado

### 6.2 Política de Propiedad de Datos

**Principio Fundamental:**
El cliente es el único dueño de sus datos. El sistema está diseñado con esta filosofía desde el inicio.

**Exportación Sin Restricciones:**
- Disponible en cualquier momento, sin solicitudes especiales
- Sin costos adicionales
- Sin límites de frecuencia
- Sin necesidad de justificar el motivo

**Formato Estándar:**
- CSV es un formato abierto y estándar
- No requiere software propietario para leer
- Compatible con cualquier herramienta de análisis
- Los datos son portables y reutilizables

**En Caso de Cancelación:**
- Si el cliente cancela el servicio, se entrega exportación completa de todos sus datos
- Entrega dentro de 30 días de la cancelación
- Formato: CSV para datos operativos, SQL dump si se requiere
- Sin costos adicionales por exportación final

**Sin Lock-in:**
- El sistema no "encierra" la información del cliente
- No hay dependencia técnica que impida migrar datos
- El cliente puede mantener copias de seguridad independientes
- El cliente puede migrar a otro sistema cuando quiera

**Garantía:**
Si alguna vez el cliente necesita sus datos y no se los proporcionamos, se devuelve el 100% del mantenimiento pagado.

---

## 7. Beneficios Concretos para el Cliente

### 7.1 Ahorro de Tiempo

**Eliminación de Búsquedas Manuales:**
- Antes: Buscar en múltiples archivos Excel dispersos
- Ahora: Búsqueda instantánea en un solo lugar
- Ahorro estimado: 30-60 minutos diarios en búsquedas

**Automatización de Cálculos:**
- Antes: Calcular totales, impuestos manualmente en Excel
- Ahora: Cálculos automáticos al crear operación
- Ahorro estimado: 15-30 minutos por operación
- Reducción de errores: 0% vs. 5-10% en cálculos manuales

**Reducción de Tareas Repetitivas:**
- Antes: Copiar/pegar datos entre archivos, actualizar múltiples hojas
- Ahora: Datos centralizados, actualización automática
- Ahorro estimado: 2-4 horas semanales en tareas administrativas

**Búsqueda Instantánea:**
- Antes: Abrir archivos, buscar manualmente, comparar versiones
- Ahora: Búsqueda en tiempo real, resultados inmediatos
- Ahorro estimado: 20-40 minutos diarios

**ROI de Tiempo:**
Si el sistema ahorra 5 horas/semana en tareas administrativas, se paga solo en menos de un mes (considerando costo de tiempo del empleado).

### 7.2 Control y Visibilidad

**Centralización de Información:**
- Todo en un solo lugar: clientes, proveedores, productos, operaciones
- Sin archivos dispersos, sin versiones desactualizadas
- Acceso inmediato a cualquier información

**Reportes Operativos:**
- Ventas por período: Ver rendimiento en cualquier rango de fechas
- Compras por período: Control de gastos y proveedores
- Resúmenes por cliente/proveedor: Identificar principales relaciones comerciales
- Toma de decisiones informada basada en datos reales

**Trazabilidad Completa:**
- Auditoría de quién hizo qué y cuándo
- Historial completo de cambios
- Identificación de responsables de acciones
- Cumplimiento de procesos internos

**Historial de Operaciones:**
- Ver todas las operaciones de un cliente específico
- Ver todas las operaciones de un proveedor específico
- Análisis de patrones de compra/venta
- Identificación de oportunidades de negocio

### 7.3 Reducción de Errores

**Validaciones Automáticas:**
- Códigos únicos: Imposible duplicar códigos de clientes/proveedores/productos
- Campos requeridos: Sistema no permite guardar datos incompletos
- Tipos de datos: Validación de formatos (emails, números, fechas)
- Relaciones: Validación de que cliente/proveedor pertenece a empresa

**Cálculos Automáticos:**
- Eliminación de errores matemáticos manuales
- Consistencia garantizada en totales
- Impuestos calculados correctamente según configuración
- Sin discrepancias entre cálculos manuales

**Numeración Automática:**
- Sin duplicados de números de operación
- Secuencia garantizada
- Sin saltos ni errores en numeración

**Estados de Operación:**
- Borrador → Confirmado: Evita confirmaciones accidentales
- Confirmado → Cancelado: Requiere acción explícita de admin/manager
- Imposible editar operaciones confirmadas (previene modificaciones accidentales)

**Reducción de Errores Estimada:**
- Errores en cálculos: De 5-10% a 0%
- Duplicados de códigos: De posible a imposible
- Datos incompletos: De común a imposible
- Modificaciones accidentales: De posible a imposible

### 7.4 Seguridad y Acceso

**Multi-Usuario Real:**
- Múltiples personas pueden trabajar simultáneamente
- Sin conflictos de edición (a diferencia de Excel)
- Cada usuario ve los cambios de otros en tiempo real
- Colaboración eficiente sin bloqueos

**Roles y Permisos:**
- Control de quién puede hacer qué
- ADMIN: Acceso completo para gestión
- MANAGER: Puede confirmar operaciones, gestionar datos
- OPERATOR: Puede crear operaciones, gestionar datos básicos
- VIEWER: Solo lectura para reportes

**Backups Automáticos:**
- Protección contra pérdida de datos por errores humanos
- Protección contra fallos de hardware
- Retención de 30 días para recuperación
- Restauración disponible en caso de necesidad

**Acceso desde Cualquier Lugar:**
- Sistema web accesible desde cualquier navegador
- No requiere instalación de software
- Funciona en desktop, tablet, móvil
- Acceso remoto seguro con autenticación

**Seguridad de Datos:**
- Datos protegidos con autenticación
- Aislamiento completo entre empresas (multi-tenant)
- Logs de seguridad para auditoría
- Protección contra accesos no autorizados

---

## 8. Cliente Ideal

### 8.1 Perfil del Cliente

**Tamaño de Empresa:**
- Pequeñas y medianas empresas (5-50 empleados)
- Volumen de operaciones: 10-200 operaciones comerciales por mes
- Número de clientes: 20-500 clientes
- Número de proveedores: 10-200 proveedores
- Número de productos/servicios: 50-1000 items

**Situación Actual:**
- Actualmente usan Excel, Google Sheets o métodos manuales
- Tienen archivos dispersos, versiones desactualizadas
- Procesos manuales que consumen tiempo
- Necesitan ordenar operaciones sin complejidad

**Necesidades:**
- Implementación rápida (7-14 días, no meses)
- Solución simple de aprender (mínima capacitación)
- Control de acceso multi-usuario
- Reportes operativos básicos
- Propiedad de datos (exportación, sin lock-in)

**Valores:**
- Valoran rapidez de implementación
- Valoran simplicidad sobre complejidad
- Valoran propiedad de datos
- Valoran soporte profesional
- Valoran relación precio/valor

### 8.2 Sectores Ideales

**Comercio Minorista:**
- Tiendas físicas o online
- Gestión de clientes y productos
- Registro de ventas diarias
- Control de proveedores

**Servicios Profesionales:**
- Consultorías, estudios profesionales
- Gestión de clientes y proyectos
- Registro de servicios prestados
- Control de gastos y proveedores

**Distribución:**
- Mayoristas, distribuidores
- Gestión de clientes y productos
- Registro de ventas y compras
- Control de inventario básico

**Manufactura Pequeña:**
- Talleres, pequeñas fábricas
- Gestión de clientes y productos
- Registro de producción y ventas
- Control de materias primas (proveedores)

### 8.3 NO Adecuado Para

**Empresas que Requieren:**
- Facturación electrónica integrada (puede agregarse después como módulo adicional)
- Control de inventario avanzado en tiempo real (el sistema tiene campo stock básico, no control avanzado)
- Integraciones complejas con sistemas externos (bancos, procesadores de pago, etc.)

**Grandes Corporaciones:**
- Procesos altamente complejos y personalizados
- Múltiples departamentos con necesidades muy diferentes
- Requisitos de compliance estricto (SOX, HIPAA) que exijan separación física de datos

**Empresas que Buscan:**
- Soluciones "gratis" o extremadamente baratas sin soporte
- Desarrollo custom desde cero (este es un producto base configurable)
- Sistemas experimentales o en beta

---

## 9. Qué NO Hace el Sistema (Límites del Alcance)

### 9.1 Excluido del MVP v1

**Facturación y Documentos Fiscales:**
- ❌ Facturación electrónica integrada
- ❌ Generación automática de facturas PDF
- ❌ Integración con sistemas fiscales gubernamentales
- ❌ Emisión de comprobantes fiscales electrónicos

**Integraciones Externas:**
- ❌ Integraciones con bancos
- ❌ Integraciones con procesadores de pago (Stripe, PayPal, etc.)
- ❌ Integraciones con sistemas de contabilidad externos
- ❌ APIs REST públicas (la arquitectura está preparada, pero no está expuesta)

**Aplicaciones Móviles:**
- ❌ App móvil nativa (iOS/Android)
- ❌ Aplicación móvil híbrida
- ❌ Notificaciones push en móvil

**Análisis y BI:**
- ❌ Dashboard con gráficos complejos
- ❌ Business Intelligence avanzado
- ❌ Análisis predictivo
- ❌ Machine Learning o IA

**Funcionalidades Avanzadas:**
- ❌ Sistema de turnos o agendas
- ❌ Notificaciones en tiempo real (websockets)
- ❌ Chat interno o mensajería
- ❌ Sistema de tareas o proyectos

**Inventario Avanzado:**
- ❌ Control de stock en tiempo real con alertas
- ❌ Gestión de almacenes múltiples
- ❌ Control de lotes y fechas de vencimiento
- ❌ Movimientos de stock automáticos

**Puntos de Venta:**
- ❌ POS (Point of Sale) integrado
- ❌ Terminal de venta física
- ❌ Integración con impresoras fiscales

**Presupuestos y Cotizaciones:**
- ❌ Sistema de presupuestos para ventas
- ❌ Cotizaciones múltiples por cliente
- ❌ Aprobación de presupuestos con workflow

**Otros:**
- ❌ Multi-idioma completo (solo español en MVP)
- ❌ Importación masiva de datos desde Excel (se hace manualmente en setup)
- ❌ Exportación a Excel avanzada (solo CSV básico)
- ❌ Categorías de productos (excluidas del MVP)

### 9.2 Lo que SÍ Hace (Resumen)

✅ Gestión completa de clientes, proveedores y productos  
✅ Registro de ventas y compras con múltiples items  
✅ Cálculos automáticos de totales e impuestos  
✅ Reportes operativos básicos (ventas/compras por período, resúmenes)  
✅ Exportación CSV completa de todos los datos  
✅ Multi-usuario con roles y permisos  
✅ Auditoría operativa básica (quién hizo qué)  
✅ Búsqueda y filtros en todos los módulos  
✅ Sistema multi-tenant seguro (múltiples empresas en una instancia)  
✅ Configuración por empresa (moneda, impuestos, datos fiscales)

---

## 10. Modelo Comercial

### 10.1 Setup Inicial (Implementación)

**Precio:**
- **Basic:** $1,200 USD (una vez)
- **Standard:** $1,500 USD (una vez) - Recomendado
- **Premium:** $1,800 USD (una vez)

**Incluye:**
- Instalación y configuración del sistema según necesidades específicas
- Migración inicial de datos (según paquete: 200-500 registros o ilimitado)
- Configuración de usuarios iniciales y roles
- Personalización de datos de empresa (logo, información fiscal, configuración)
- Capacitación según paquete (2-4 horas vía videollamada)
- Documentación de usuario
- Garantía de funcionamiento por 30 días post-implementación

**Tiempo de Implementación:**
- 7 a 14 días calendario desde la contratación
- Depende de: complejidad de datos iniciales, disponibilidad del cliente, personalizaciones requeridas

**Entregables:**
- Sistema funcionando y accesible vía web
- Credenciales de acceso para administradores
- Documentación de usuario (PDF o web)
- Sesión(es) de capacitación grabada(s)

### 10.2 Mantenimiento Mensual

**Precio:**
- **Basic:** $200 USD/mes
- **Standard:** $250 USD/mes - Recomendado
- **Premium:** $300 USD/mes

**Incluye (según paquete):**

**Soporte Técnico:**
- Resolución de consultas técnicas vía email
- Soporte para problemas del sistema
- Asistencia en configuración de usuarios y permisos
- Horas incluidas: Basic (2h/mes), Standard (4h/mes), Premium (6h/mes)
- Tiempo de respuesta: Standard (12 horas hábiles), Premium (6 horas hábiles)

**Actualizaciones del Sistema:**
- Parches de seguridad (automáticos, sin costo adicional)
- Actualizaciones menores de funcionalidad estándar
- Corrección de bugs reportados
- Mejoras de rendimiento

**Backups y Seguridad:**
- Backup diario automático de toda la base de datos
- Retención de backups por 30 días
- Monitoreo básico de seguridad y disponibilidad
- Restauración de backups en caso de necesidad (dentro de horas de soporte)

**Mejoras Menores (según paquete):**
- Ajustes de campos o formularios
- Modificaciones menores en reportes
- Cambios en permisos o roles
- Ajustes de configuración por empresa
- Standard: 1 mejora menor/mes | Premium: 2 mejoras menores/mes
- **Límite:** Mejoras que requieren menos de 2 horas de desarrollo

**NO Incluye:**
- Desarrollo de nuevas funcionalidades significativas
- Integraciones con sistemas externos (APIs, facturación electrónica, etc.)
- Migraciones masivas de datos adicionales (después de setup inicial)
- Capacitación adicional extensiva (más allá de la incluida en setup)
- Consultoría estratégica extensa (solo Premium tiene 2h/mes de consultoría incluida)

### 10.3 Paquetes Detallados

**Paquete BASIC - $1,200 setup / $200/mes**
- Hasta 3 usuarios simultáneos
- Hasta 200 registros iniciales (clientes + proveedores + productos)
- Capacitación: 2 horas (1 sesión)
- Soporte: 2 horas/mes incluidas
- **Ideal para:** Empresas pequeñas (5-15 empleados), volumen bajo de operaciones

**Paquete STANDARD - $1,500 setup / $250/mes (Recomendado)**
- Hasta 10 usuarios simultáneos
- Hasta 500 registros iniciales
- Capacitación: 3 horas (2 sesiones)
- Soporte: 4 horas/mes incluidas, respuesta en 12 horas
- 1 mejora menor por mes incluida
- **Ideal para:** Empresas medianas (15-30 empleados), volumen medio de operaciones

**Paquete PREMIUM - $1,800 setup / $300/mes**
- Usuarios ilimitados
- Registros iniciales ilimitados
- Capacitación: 4 horas (3 sesiones) + sesión de seguimiento
- Soporte: 6 horas/mes incluidas, respuesta en 6 horas
- 2 mejoras menores por mes incluidas
- 2 horas de consultoría mensual incluida
- **Ideal para:** Empresas en crecimiento (30+ empleados), alto volumen de operaciones

---

## 11. Argumentos de Venta

### 11.1 vs. Excel / Google Sheets

**Multi-Usuario Real:**
- **Excel/Sheets:** Conflictos cuando múltiples personas editan simultáneamente
- **Este sistema:** Múltiples usuarios trabajan simultáneamente sin conflictos
- **Ventaja:** Colaboración eficiente, sin bloqueos ni pérdida de datos

**Seguridad:**
- **Excel/Sheets:** ¿Quién tiene acceso al archivo? ¿Dónde está respaldado?
- **Este sistema:** Roles y permisos, backups automáticos diarios, acceso controlado
- **Ventaja:** Datos protegidos, control de quién accede a qué

**Escalabilidad:**
- **Excel/Sheets:** Con 50+ clientes y 100+ operaciones/mes, se vuelve lento y propenso a errores
- **Este sistema:** Maneja miles de registros sin problemas de rendimiento
- **Ventaja:** Crece con el negocio sin limitaciones técnicas

**Automatización:**
- **Excel/Sheets:** Cálculos manuales, fórmulas que se rompen, validaciones manuales
- **Este sistema:** Cálculos automáticos, validaciones automáticas, numeración automática
- **Ventaja:** Eliminación de errores, consistencia garantizada

**Flexibilidad:**
- **Excel/Sheets:** Puede seguir usando Excel para análisis
- **Este sistema:** Exporta todo a CSV, compatible con Excel
- **Ventaja:** Lo mejor de ambos mundos: sistema profesional + análisis en Excel si lo prefiere

### 11.2 vs. Software Genérico

**Personalización:**
- **Software genérico:** Configuración limitada, no se adapta a necesidades específicas
- **Este sistema:** Configurado según necesidades específicas del cliente
- **Ventaja:** Sistema que se adapta al negocio, no al revés

**Implementación:**
- **Software genérico:** Meses de configuración, capacitación extensa, curva de aprendizaje
- **Este sistema:** 7-14 días, capacitación mínima, fácil de aprender
- **Ventaja:** Funcionando rápido, sin interrumpir operaciones

**Soporte:**
- **Software genérico:** Soporte genérico, respuestas lentas, sin personalización
- **Este sistema:** Soporte directo, respuesta rápida, mejoras según feedback
- **Ventaja:** Atención personalizada, problemas resueltos rápido

**Precio:**
- **Software genérico:** Licencias complejas, costos ocultos, contratos largos
- **Este sistema:** Pago simple, mes a mes, sin sorpresas
- **Ventaja:** Transparencia, flexibilidad, sin compromisos largos

### 11.3 vs. Soluciones "Baratas"

**Tecnología:**
- **Soluciones baratas:** Tecnología experimental, no probada, riesgosa
- **Este sistema:** Django + PostgreSQL, mismo stack que Instagram, Spotify, NASA
- **Ventaja:** Tecnología empresarial probada, producción-ready

**Seguridad:**
- **Soluciones baratas:** Multi-tenant experimental, riesgo de fugas de datos
- **Este sistema:** Multi-tenant probado, aislamiento garantizado, logs de seguridad
- **Ventaja:** Seguridad real, no experimental

**Soporte:**
- **Soluciones baratas:** Soporte limitado o inexistente, sin garantías
- **Este sistema:** Horas incluidas, respuesta garantizada, mejoras continuas
- **Ventaja:** Soporte profesional, sistema que mejora con el tiempo

**Propiedad de Datos:**
- **Soluciones baratas:** Lock-in, difícil exportar datos, dependencia total
- **Este sistema:** Exportación completa, sin lock-in, datos en formato estándar
- **Ventaja:** Control total, independencia, migración posible cuando quiera

---

## 12. Why Choose This System?

**Sección lista para usar en propuestas y presentaciones:**

### Fast Implementation
Your system will be running in 7-14 days, not months. No lengthy development cycles or extensive training required. From Excel to professional system in less than 2 weeks.

### You Own Your Data
Export everything in CSV format anytime, without restrictions. No vendor lock-in. Your data, your control. If you cancel, we deliver all your data within 30 days.

### Professional Technology
Built with Django and PostgreSQL - the same enterprise-grade technology used by companies like Instagram, Spotify, and NASA. Not experimental, production-ready.

### Ongoing Support
Monthly maintenance includes technical support, security updates, automatic backups, and minor improvements. Your system improves over time, not just stays the same.

### Multi-User Ready
Multiple team members can work simultaneously without conflicts. Role-based access control ensures security and proper permissions. No more file sharing or version conflicts.

### Scalable
Handles hundreds of customers, thousands of operations, and multiple users without performance issues. Grows with your business without needing to migrate to a new system.

### Simple but Powerful
All the core functionality you need without the complexity of traditional ERP systems. Easy to learn, quick to implement, straightforward to use daily.

### Secure Multi-Tenant
Your data is completely isolated from other companies. Multi-tenant architecture proven in production, not experimental. Security logging and monitoring included.

### Cost-Effective
Starting from $1,200 setup and $200/month maintenance. Compare to custom development ($5,000-15,000+) or traditional ERP ($3,000+ setup, $500+/month). Professional solution at a fraction of the cost.

### No Lock-in
Export your data anytime. Standard CSV format compatible with Excel and any analysis tool. If you need to migrate, your data comes with you. No technical barriers.

---

## 13. Frases Clave (Selling Points)

**Lista lista para copiar/pegar en Upwork, emails comerciales, propuestas:**

### Implementación y Velocidad
- "Sistema funcionando en 7-14 días, no meses"
- "De Excel a sistema profesional en menos de 2 semanas"
- "Implementación rápida sin interrumpir operaciones"
- "Sin desarrollo desde cero: sistema base configurado para usted"

### Propiedad de Datos
- "Usted es dueño de sus datos, siempre"
- "Exporte todo en CSV cuando quiera, sin restricciones"
- "Sin lock-in: sus datos, su control"
- "Si cancela, le entregamos todos sus datos en 30 días"

### Tecnología Profesional
- "Tecnología empresarial probada: Django + PostgreSQL"
- "Mismo stack que usan empresas como Instagram y Spotify"
- "No es un proyecto experimental: es tecnología de producción"
- "Seguridad real: multi-tenant probado, no experimental"

### Seguridad y Aislamiento
- "Multi-tenant seguro: sus datos completamente aislados"
- "Backups diarios automáticos incluidos"
- "Roles y permisos: controle quién accede a qué información"
- "Logging de seguridad: rastreo de accesos y acciones"

### Soporte y Mantenimiento
- "Soporte profesional incluido: [X] horas/mes según paquete"
- "Actualizaciones de seguridad automáticas"
- "Mejoras menores incluidas: el sistema mejora con el tiempo"
- "Respuesta garantizada: [X] horas según paquete"

### Valor y ROI
- "Ahorre 5+ horas/semana en tareas administrativas"
- "Se paga solo en menos de un mes"
- "Compare con desarrollo custom: $5,000-15,000+ vs. $1,200-1,800"
- "Compare con ERP tradicional: $3,000+ setup vs. $1,200-1,800"

### Usabilidad
- "Fácil de aprender: capacitación mínima requerida"
- "Interfaz intuitiva: sus empleados lo usarán desde el día uno"
- "Multi-usuario real: sin conflictos de edición simultánea"
- "Búsqueda instantánea: encuentre cualquier dato en segundos"

### Funcionalidades
- "Gestión completa: clientes, proveedores, productos, operaciones"
- "Reportes operativos: ventas, compras, resúmenes por cliente/proveedor"
- "Cálculos automáticos: totales, impuestos, sin errores"
- "Exportación CSV: análisis en Excel cuando quiera"

---

## Conclusión

Este documento de referencia proporciona una descripción completa y precisa del Custom Internal Management System. Todas las funcionalidades mencionadas existen en el código y han sido probadas. Todos los precios y paquetes están alineados con la estrategia comercial definida.

**Uso Recomendado:**
- Base para propuestas comerciales
- Referencia en llamadas de ventas
- Material para presentaciones
- Respuestas a preguntas técnicas y comerciales
- Contenido para sitio web o materiales de marketing

**Actualización:**
Este documento debe actualizarse cuando se agreguen nuevas funcionalidades o se modifiquen precios/paquetes. Mantener alineado con el código real y la estrategia comercial.

---

**Última actualización:** Enero 2026  
**Versión del documento:** 1.0  
**Mantener sincronizado con:** ARCHITECTURE.md, PRODUCT_OVERVIEW.md, COMMERCIAL_STRATEGY.md

