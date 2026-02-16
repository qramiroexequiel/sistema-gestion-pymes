# Principios de Seguridad Multi-Tenant
## Guía de Referencia para Desarrollo

**Versión:** 1.0  
**Fecha:** Enero 2026  
**Propósito:** Documento de referencia para mantener seguridad multi-tenant en todo el código

---

## Principio Fundamental (NO NEGOCIABLE)

**Bajo ninguna circunstancia una empresa puede ver, modificar o inferir datos de otra empresa.**

Toda decisión técnica debe evaluarse primero desde la perspectiva de seguridad multi-tenant.

---

## 1. Arquitectura Multi-Tenant

### 1.1 Base de Datos Compartida

- ✅ **UNA sola base de datos PostgreSQL compartida**
- ✅ **Separación lógica mediante `company_id`** en todas las tablas de negocio
- ❌ **NO múltiples bases de datos** ni schemas separados (en versión 1)

### 1.2 Modelos con Campo `company`

**Regla Obligatoria:**
- Todos los modelos de negocio DEBEN tener campo `company` (ForeignKey a Company)
- Usar `CompanyModelMixin` para garantizar consistencia
- `company` debe ser `null=False, blank=False`

**Modelos que NO requieren `company` (justificados):**
- `Company` - Modelo global
- `Membership` - Modelo de relación usuario-empresa
- `User` - Modelo estándar de Django
- `OperationItem` - Se accede solo a través de `Operation` (que sí tiene `company`)

**Nunca asumir** que un objeto pertenece a la empresa activa sin validarlo explícitamente.

---

## 2. Middleware Multi-Tenant

### 2.1 CompanyMiddleware

**Responsabilidades:**
- Resolver y asignar `request.current_company`
- Validar que usuario tenga `Membership` activa
- Evitar estados inválidos (usuario autenticado sin empresa válida)
- Limpiar sesión si membresía deja de existir

**Garantías:**
- `request.current_company` es `None` o instancia válida de `Company`
- `request.current_membership` es `None` o instancia válida de `Membership`
- Imposible tener `current_company` sin `Membership` activa

**Rutas Públicas:**
- `/login/`, `/logout/`, `/empresa/seleccionar/`
- `/static/`, `/media/`, `/favicon.ico`
- `/admin/` (solo para superusers sin empresa)

---

## 3. Managers y QuerySets

### 3.1 CompanyManager

**Regla Obligatoria:**
- **NUNCA usar `Model.objects.all()` sin filtrar**
- **NUNCA usar `Model.objects.get(pk=...)` sin filtrar por company**
- **SIEMPRE usar `.for_company(company)` explícitamente**

**Ejemplos Correctos:**
```python
# ✅ CORRECTO
customers = Customer.objects.for_company(company).filter(active=True)
customer = Customer.objects.for_company(company).get(pk=pk)
customer = Customer.objects.get_or_404_for_company(company, pk=pk)
```

**Ejemplos Incorrectos:**
```python
# ❌ INCORRECTO - FALTA DE SEGURIDAD
customers = Customer.objects.filter(active=True)  # Sin filtrar por company
customer = Customer.objects.get(pk=pk)  # Sin filtrar por company
```

### 3.2 CompanyManager NO Filtra Automáticamente

**Razón:** Evitar falsa sensación de seguridad. El filtrado debe ser explícito y consciente.

---

## 4. Mixins de Seguridad

### 4.1 CompanyRequiredMixin

**OBLIGATORIO para todas las views protegidas.**

**Comportamiento:**
- Requiere autenticación
- Requiere `current_company` activa
- Redirige a selección de empresa si no hay empresa pero hay memberships
- Cierra sesión si no hay memberships válidas

**Uso:**
```python
class CustomerListView(CompanyRequiredMixin, ListView):
    # ...
```

### 4.2 CompanyFilterMixin

**OBLIGATORIO para todas las ListView.**

**Comportamiento:**
- Fuerza filtrado por empresa en `get_queryset()`
- Preserva optimizaciones del queryset (select_related, prefetch_related)
- Imposible omitir el filtrado
- Retorna queryset vacío si no hay empresa

**Uso:**
```python
class CustomerListView(CompanyRequiredMixin, CompanyFilterMixin, ListView):
    # get_queryset() automáticamente filtra por company
```

### 4.3 CompanyObjectMixin

**OBLIGATORIO para DetailView, UpdateView, DeleteView.**

**Comportamiento:**
- Obtiene objeto desde queryset filtrado por empresa
- Doble verificación: filtra y valida pertenencia
- Retorna 404 si objeto no pertenece a empresa
- Logging de intentos de acceso cross-tenant

**Uso:**
```python
class CustomerDetailView(CompanyRequiredMixin, CompanyObjectMixin, DetailView):
    # get_object() automáticamente valida pertenencia a company
```

### 4.4 RoleRequiredMixin

**OBLIGATORIO para views que requieren roles específicos.**

**Comportamiento:**
- Valida rol en empresa activa
- Requiere `current_membership` válida
- Lanza `PermissionDenied` si rol no es suficiente

**Uso:**
```python
class CustomerCreateView(CompanyRequiredMixin, RoleRequiredMixin, CreateView):
    required_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR]
```

---

## 5. Services Layer (OBLIGATORIA)

### 5.1 Separación de Lógica

**Regla Obligatoria:**
- Toda lógica de negocio y cálculos debe vivir en `services.py`
- Las Views deben ser delgadas:
  - Recibir request
  - Validar permisos
  - Delegar lógica a services
  - Renderizar respuesta

**Ejemplos de lógica que DEBE ir en services:**
- Cálculo de totales
- Impuestos
- Validaciones de negocio
- Manejo de estados
- Cálculo de stock o saldos

**Está prohibido:**
- ❌ Lógica compleja en Views
- ❌ Cálculos en templates
- ❌ Efectos secundarios ocultos en modelos

### 5.2 Validaciones Multi-Tenant en Services

**Regla Obligatoria:**
- Todos los services reciben `company` como parámetro explícito
- Validar que todos los objetos recibidos pertenezcan a la misma empresa
- Ante inconsistencias de empresa, fallar de forma segura (404 o excepción controlada)

**Ejemplo Correcto:**
```python
def create_operation(company, type, date, customer=None, supplier=None, ...):
    # Validar que pertenezcan a la misma empresa
    if customer and customer.company != company:
        raise ValidationError('El cliente debe pertenecer a la empresa actual.')
    if supplier and supplier.company != company:
        raise ValidationError('El proveedor debe pertenecer a la empresa actual.')
    # ...
```

---

## 6. Admin de Django

### 6.1 Protección Obligatoria

**Regla Obligatoria:**
- Todos los admins de modelos de negocio DEBEN implementar `get_queryset()`
- Filtrar por `company` para usuarios no-superuser
- Superusers pueden ver todo (correcto para administración)

**Ejemplo Correcto:**
```python
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request, 'current_company') and request.current_company:
            return qs.filter(company=request.current_company)
        return qs.none()
```

**Modelos que requieren protección:**
- ✅ `Customer`, `Supplier`, `Product`, `Operation`
- ✅ `OperationItem` (filtrar por `operation__company`)
- ✅ `AuditLog` (filtrar por `company`)
- ✅ `Membership` (filtrar por `user` para no-superusers)

**Modelos que NO requieren protección:**
- `Company` - Modelo global, correcto que todos lo vean

---

## 7. Checklist de Seguridad

### 7.1 Al Crear un Nuevo Modelo

- [ ] ¿Tiene campo `company` (FK a Company)?
- [ ] ¿Hereda de `CompanyModelMixin`?
- [ ] ¿Usa `CompanyManager`?
- [ ] ¿Tiene índices en `(company, campo_búsqueda)`?
- [ ] ¿Tiene constraints `unique_together` que incluyan `company`?

### 7.2 Al Crear una Nueva View

- [ ] ¿Usa `CompanyRequiredMixin`?
- [ ] ¿Si es ListView, usa `CompanyFilterMixin`?
- [ ] ¿Si es DetailView/UpdateView/DeleteView, usa `CompanyObjectMixin`?
- [ ] ¿Si requiere roles, usa `RoleRequiredMixin`?
- [ ] ¿Nunca usa `Model.objects.get()` sin filtrar por company?

### 7.3 Al Crear un Nuevo Service

- [ ] ¿Recibe `company` como parámetro explícito?
- [ ] ¿Valida que todos los objetos pertenezcan a `company`?
- [ ] ¿Lanza excepción clara si hay discrepancia de empresa?
- [ ] ¿Toda la lógica de negocio está aquí, no en views?

### 7.4 Al Crear un Nuevo Admin

- [ ] ¿Implementa `get_queryset()` que filtre por company?
- [ ] ¿Permite acceso a superusers sin filtrar?
- [ ] ¿Retorna queryset vacío si no hay empresa activa?

---

## 8. Errores Comunes a Evitar

### 8.1 ❌ Asumir que un objeto pertenece a la empresa

```python
# ❌ INCORRECTO
operation = Operation.objects.get(pk=pk)
if operation.company == request.current_company:  # RACE CONDITION
    # ...
```

```python
# ✅ CORRECTO
operation = Operation.objects.for_company(request.current_company).get(pk=pk)
# Si no pertenece, lanza DoesNotExist
```

### 8.2 ❌ Usar `.objects.get()` sin filtrar

```python
# ❌ INCORRECTO
customer = Customer.objects.get(pk=pk)
```

```python
# ✅ CORRECTO
customer = Customer.objects.for_company(company).get(pk=pk)
# O mejor:
customer = Customer.objects.get_or_404_for_company(company, pk=pk)
```

### 8.3 ❌ Olvidar validación en services

```python
# ❌ INCORRECTO
def add_item(operation, product):
    item = OperationItem(operation=operation, product=product)
    item.save()  # No valida que product.company == operation.company
```

```python
# ✅ CORRECTO
def add_item(operation, product):
    if product.company != operation.company:
        raise ValidationError('El producto debe pertenecer a la misma empresa.')
    item = OperationItem(operation=operation, product=product)
    item.save()
```

### 8.4 ❌ Admin sin protección

```python
# ❌ INCORRECTO
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email']
    # Sin get_queryset() - usuarios no-superuser pueden ver todas las empresas
```

```python
# ✅ CORRECTO
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request, 'current_company') and request.current_company:
            return qs.filter(company=request.current_company)
        return qs.none()
```

---

## 9. Testing de Seguridad Multi-Tenant

### 9.1 Tests Obligatorios

**Para cada modelo de negocio:**
- [ ] Test: Usuario de empresa A no puede ver objetos de empresa B
- [ ] Test: Usuario de empresa A recibe 404 al acceder por ID a objeto de empresa B
- [ ] Test: Usuario de empresa A no puede modificar objetos de empresa B
- [ ] Test: Usuario de empresa A no puede eliminar objetos de empresa B

**Para cada service:**
- [ ] Test: Service valida pertenencia a empresa
- [ ] Test: Service lanza excepción si hay discrepancia de empresa

**Para cada admin:**
- [ ] Test: Usuario no-superuser solo ve datos de su empresa
- [ ] Test: Superuser puede ver todos los datos

---

## 10. Logging de Seguridad

### 10.1 Eventos a Registrar

- Intento de acceso sin membresía válida (WARNING)
- Usuario sin empresas activas (WARNING)
- Ruta protegida sin empresa activa (WARNING)
- Intento de acceso cross-tenant (404) (WARNING)
- Discrepancia de company detectada (ERROR)

### 10.2 Datos a Registrar

- `user_id`, `username`
- `company_id` (cuando aplica)
- `path`, `method`
- `ip_address`
- `user_agent` (truncado)

---

## 11. Revisión de Código

### 11.1 Antes de Hacer Commit

**Preguntas obligatorias:**
1. ¿Este cambio puede permitir que una empresa vea datos de otra?
2. ¿Todas las consultas filtran por `company`?
3. ¿Los services validan pertenencia a empresa?
4. ¿Los admins están protegidos?
5. ¿Hay tests que verifiquen el aislamiento?

### 11.2 Code Review Checklist

- [ ] No hay uso de `.objects.get()` sin filtrar por company
- [ ] Todas las views usan mixins correctos
- [ ] Todos los services validan pertenencia a empresa
- [ ] Todos los admins filtran por company
- [ ] Hay tests de seguridad multi-tenant

---

## 12. Mantenimiento Continuo

### 12.1 Disciplina en Código

- **Nunca relajar** las reglas de seguridad por "conveniencia"
- **Siempre validar** pertenencia a empresa, incluso si "parece obvio"
- **Siempre usar** mixins y managers, nunca acceso directo
- **Siempre probar** con múltiples empresas en tests

### 12.2 Monitoreo

- Revisar logs de seguridad periódicamente
- Investigar cualquier WARNING o ERROR de seguridad
- Mantener tests de seguridad actualizados
- Documentar cualquier excepción justificada

---

**Última actualización:** Enero 2026  
**Mantener este documento actualizado** cuando se agreguen nuevas funcionalidades o se modifiquen patrones de seguridad.

