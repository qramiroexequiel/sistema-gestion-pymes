# Seguridad Multi-Tenant: Validación y Buenas Prácticas

**Versión:** 1.0  
**Fecha:** Enero 2026  
**Contexto:** Sistema Django multi-empresa con separación lógica por `company_id`

---

## 1. Validación del Enfoque Actual

### 1.1 Arquitectura: DB Compartida + `company_id`

**Decisión:** Separación lógica mediante `company_id` en todas las entidades de negocio.

**¿Es correcto para un producto comercial?**

✅ **SÍ**, bajo estas condiciones:

- **Escala objetivo:** 10-100 empresas (no miles)
- **Costo de infraestructura:** Crítico (una DB es más barata que múltiples)
- **Velocidad de implementación:** Prioritaria (7-14 días por cliente)
- **Complejidad de mantenimiento:** Debe ser mínima

**Ventajas comerciales:**
- Setup rápido: no requiere crear DBs/schemas por cliente
- Backups simples: un solo backup cubre todos los clientes
- Migraciones unificadas: un `migrate` actualiza todos los clientes
- Monitoreo centralizado: una sola instancia a monitorear
- Costos predecibles: hosting fijo independiente del número de clientes

**Limitaciones aceptadas:**
- No es adecuado para empresas con requerimientos de compliance estricto (SOX, HIPAA) que exijan separación física
- No escala a miles de empresas sin optimizaciones adicionales (sharding, read replicas)
- Requiere disciplina estricta en código para evitar fugas

**Conclusión:** El enfoque es **correcto y comercialmente viable** para el MVP y los primeros 50-100 clientes.

---

## 2. Buenas Prácticas Concretas

### 2.1 Middleware de Empresa Activa

**Implementación actual:** `core/middleware.py`

**Buenas prácticas aplicadas:**
- ✅ Valida `Membership` activa antes de establecer `request.current_company`
- ✅ Verifica que la empresa esté activa (`company__active=True`)
- ✅ Limpia sesión si la membresía deja de existir
- ✅ Auto-selecciona primera empresa disponible si no hay selección

**Mejoras recomendadas:**

```python
# Agregar logging de intentos de acceso inválidos
import logging
logger = logging.getLogger('security')

# En CompanyMiddleware.process_request(), después de Membership.DoesNotExist:
except Membership.DoesNotExist:
    logger.warning(
        f'Intento de acceso a empresa {company_id} sin membresía válida. '
        f'Usuario: {request.user.id}, IP: {get_client_ip(request)}'
    )
```

**Regla de oro:** El middleware **NUNCA** debe establecer `request.current_company` sin validar `Membership` activa.

---

### 2.2 Managers y QuerySets Filtrados

**Implementación actual:** `core/managers.py`

**Buenas prácticas aplicadas:**
- ✅ `CompanyManager` NO filtra automáticamente (evita falsa sensación de seguridad)
- ✅ Método explícito `for_company(company)` obligatorio
- ✅ `get_or_404_for_company()` con validación de pertenencia

**Reglas obligatorias:**

1. **NUNCA usar `Model.objects.all()` o `Model.objects.filter()` sin `for_company()`**
   ```python
   # ❌ INCORRECTO
   customers = Customer.objects.filter(active=True)
   
   # ✅ CORRECTO
   customers = Customer.objects.for_company(company).filter(active=True)
   ```

2. **En services, SIEMPRE recibir `company` como parámetro explícito**
   ```python
   # ✅ CORRECTO
   def create_customer(company, name, code, ...):
       customer = Customer.objects.for_company(company).create(...)
   ```

3. **En views, usar mixins que fuerzan el filtrado**
   ```python
   # ✅ CORRECTO
   class CustomerListView(CompanyFilterMixin, ListView):
       # get_queryset() ya está filtrado por empresa automáticamente
   ```

**Validación defensiva en managers:**

```python
def for_company(self, company):
    if company is None:
        raise ValidationError('Se requiere una empresa para filtrar.')
    if not isinstance(company, Company):
        raise ValidationError('company debe ser una instancia de Company.')
    return self.get_queryset().filter(company=company)
```

---

### 2.3 Validaciones Defensivas en Views

**Implementación actual:** `core/mixins.py`

**Buenas prácticas aplicadas:**
- ✅ `CompanyFilterMixin` fuerza filtrado en `get_queryset()`
- ✅ `CompanyObjectMixin` verifica pertenencia en `get_object()`
- ✅ Doble verificación: queryset filtrado + validación de atributo `company`

**Reglas obligatorias:**

1. **TODAS las ListView deben usar `CompanyFilterMixin`**
   ```python
   # ✅ CORRECTO
   class CustomerListView(CompanyFilterMixin, ListView):
       model = Customer
   ```

2. **TODAS las DetailView/UpdateView/DeleteView deben usar `CompanyObjectMixin`**
   ```python
   # ✅ CORRECTO
   class CustomerDetailView(CompanyObjectMixin, DetailView):
       model = Customer
   ```

3. **NUNCA usar `get_object_or_404(Model, pk=pk)` directamente**
   ```python
   # ❌ INCORRECTO - permite acceso cross-tenant
   customer = get_object_or_404(Customer, pk=pk)
   
   # ✅ CORRECTO
   customer = Customer.objects.get_or_404_for_company(company, pk=pk)
   ```

4. **En FBVs, SIEMPRE filtrar explícitamente**
   ```python
   # ✅ CORRECTO
   def customer_detail(request, pk):
       company = request.current_company
       customer = Customer.objects.get_or_404_for_company(company, pk=pk)
   ```

---

### 2.4 Validaciones Defensivas en Services

**Implementación actual:** `operations/services.py`

**Buenas prácticas aplicadas:**
- ✅ Valida que `customer.company == company` antes de crear operación
- ✅ Valida que `product.company == operation.company` antes de añadir item
- ✅ Recibe `company` como parámetro explícito

**Reglas obligatorias:**

1. **SIEMPRE validar pertenencia a empresa en services**
   ```python
   # ✅ CORRECTO
   def create_operation(company, type, customer=None, ...):
       if customer and customer.company != company:
           raise ValidationError('El cliente debe pertenecer a la empresa actual.')
   ```

2. **NUNCA confiar en que el objeto ya viene filtrado**
   ```python
   # ❌ INCORRECTO - asume que customer ya está filtrado
   operation = Operation.objects.create(company=company, customer=customer)
   
   # ✅ CORRECTO - valida explícitamente
   if customer.company != company:
       raise ValidationError('Cliente no pertenece a la empresa.')
   operation = Operation.objects.create(company=company, customer=customer)
   ```

3. **En operaciones relacionadas, validar ambas empresas**
   ```python
   # ✅ CORRECTO
   def add_item_to_operation(operation, product, ...):
       if product.company != operation.company:
           raise ValidationError('El producto debe pertenecer a la empresa actual.')
   ```

---

### 2.5 Validaciones en Formularios

**Reglas obligatorias:**

1. **Formularios deben recibir `company` y filtrar querysets de FKs**
   ```python
   # ✅ CORRECTO
   class OperationForm(forms.ModelForm):
       def __init__(self, *args, company=None, **kwargs):
           super().__init__(*args, **kwargs)
           if company:
               self.fields['customer'].queryset = Customer.objects.for_company(company)
   ```

2. **Validar `clean()` que el objeto pertenece a la empresa**
   ```python
   # ✅ CORRECTO
   def clean_customer(self):
       customer = self.cleaned_data.get('customer')
       company = self.company
       if customer and customer.company != company:
           raise ValidationError('El cliente no pertenece a su empresa.')
       return customer
   ```

---

## 3. Errores Comunes que DEBES Evitar

### 3.1 Filtrado Incompleto en Querysets

**Error:**
```python
# ❌ INCORRECTO
customers = Customer.objects.filter(name__icontains=search)
```

**Corrección:**
```python
# ✅ CORRECTO
customers = Customer.objects.for_company(company).filter(name__icontains=search)
```

---

### 3.2 Acceso Directo por ID sin Validación

**Error:**
```python
# ❌ INCORRECTO - permite acceso cross-tenant
customer = Customer.objects.get(pk=pk)
```

**Corrección:**
```python
# ✅ CORRECTO
customer = Customer.objects.get_or_404_for_company(company, pk=pk)
```

---

### 3.3 Asumir que `request.current_company` Existe

**Error:**
```python
# ❌ INCORRECTO - puede ser None
company = request.current_company
customers = Customer.objects.for_company(company)
```

**Corrección:**
```python
# ✅ CORRECTO
company = request.current_company
if not company:
    raise Http404('No tiene una empresa activa.')
customers = Customer.objects.for_company(company)
```

---

### 3.4 Crear Objetos sin Asociar `company`

**Error:**
```python
# ❌ INCORRECTO - objeto sin empresa
customer = Customer.objects.create(name='Cliente', code='C001')
```

**Corrección:**
```python
# ✅ CORRECTO
customer = Customer.objects.for_company(company).create(
    company=company,
    name='Cliente',
    code='C001'
)
```

---

### 3.5 Validar Solo en Frontend

**Error:**
```python
# ❌ INCORRECTO - validación solo en template
# En template: {% if customer.company == current_company %}
```

**Corrección:**
```python
# ✅ CORRECTO - validación en backend
customer = Customer.objects.get_or_404_for_company(company, pk=pk)
```

---

### 3.6 Usar `get_object_or_404()` sin Filtro de Empresa

**Error:**
```python
# ❌ INCORRECTO
from django.shortcuts import get_object_or_404
customer = get_object_or_404(Customer, pk=pk)
```

**Corrección:**
```python
# ✅ CORRECTO
customer = Customer.objects.get_or_404_for_company(company, pk=pk)
```

---

### 3.7 No Validar en Services

**Error:**
```python
# ❌ INCORRECTO - asume que customer ya está validado
def create_operation(company, customer, ...):
    operation = Operation.objects.create(company=company, customer=customer)
```

**Corrección:**
```python
# ✅ CORRECTO
def create_operation(company, customer, ...):
    if customer and customer.company != company:
        raise ValidationError('El cliente debe pertenecer a la empresa actual.')
    operation = Operation.objects.create(company=company, customer=customer)
```

---

### 3.8 Filtrado en Admin sin Restricción

**Error:**
```python
# ❌ INCORRECTO - admin muestra todos los registros
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
```

**Corrección:**
```python
# ✅ CORRECTO
class CustomerAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Para usuarios no-superuser, filtrar por empresa
        if hasattr(request, 'current_company') and request.current_company:
            return qs.filter(company=request.current_company)
        return qs.none()
```

---

## 4. Checklist de Seguridad Multi-Tenant para Producción

### 4.1 Código

- [ ] **Todos los modelos de negocio tienen `company` (FK)**
  - Verificar: `grep -r "class.*Model" apps/*/models.py | grep -v "company"`
  
- [ ] **Todos los managers usan `CompanyManager`**
  - Verificar: `grep -r "objects = " apps/*/models.py | grep -v "CompanyManager"`
  
- [ ] **Todas las ListView usan `CompanyFilterMixin`**
  - Verificar: `grep -r "class.*ListView" apps/*/views.py | grep -v "CompanyFilterMixin"`
  
- [ ] **Todas las DetailView/UpdateView/DeleteView usan `CompanyObjectMixin`**
  - Verificar: `grep -r "class.*(Detail|Update|Delete)View" apps/*/views.py | grep -v "CompanyObjectMixin"`
  
- [ ] **No hay `.objects.all()` o `.objects.filter()` sin `for_company()`**
  - Verificar: `grep -r "\.objects\.(all|filter|get)\(" apps/*/views.py apps/*/services.py`
  
- [ ] **Todos los services reciben `company` como parámetro explícito**
  - Verificar: `grep -r "def.*\(.*\):" apps/*/services.py | grep -v "company"`
  
- [ ] **Todos los formularios filtran querysets de FKs por empresa**
  - Verificar: `grep -r "queryset.*objects" apps/*/forms.py | grep -v "for_company"`

---

### 4.2 Middleware

- [ ] **Middleware valida `Membership` activa antes de establecer `current_company`**
- [ ] **Middleware verifica `company.active == True`**
- [ ] **Middleware limpia sesión si membresía inválida**
- [ ] **Middleware no establece `current_company` para rutas públicas**
- [ ] **Middleware permite acceso a `/admin/` solo para superusers**

---

### 4.3 Tests

- [ ] **Tests de aislamiento: usuario con 2 empresas no ve datos cruzados**
  - Verificar: `grep -r "test.*cross.*company\|test.*isolation" apps/*/tests.py`
  
- [ ] **Tests de acceso: usuario de otra empresa recibe 404**
  - Verificar: `grep -r "test.*404\|test.*other.*company" apps/*/tests.py`
  
- [ ] **Tests de managers: `for_company()` filtra correctamente**
  - Verificar: `grep -r "test.*manager.*company" apps/*/tests.py`

---

### 4.4 Base de Datos

- [ ] **Índices en `company` para todas las tablas de negocio**
  - Verificar: `grep -r "Index.*company" apps/*/models.py`
  
- [ ] **Constraints `unique_together` incluyen `company`**
  - Verificar: `grep -r "unique_together" apps/*/models.py | grep -v "company"`
  
- [ ] **Foreign Keys a `Company` con `on_delete=CASCADE`**
  - Verificar: `grep -r "ForeignKey.*Company" apps/*/models.py | grep -v "CASCADE"`

---

### 4.5 Admin de Django

- [ ] **Admin restringe querysets por empresa para usuarios no-superuser**
  - Verificar: `grep -r "get_queryset" apps/*/admin.py | grep -v "current_company"`
  
- [ ] **Admin no permite crear objetos sin empresa (excepto superuser)**
  - Verificar: `grep -r "save_model\|save_formset" apps/*/admin.py`

---

### 4.6 Logging y Monitoreo

- [x] **Logging de intentos de acceso inválidos (sin membresía)**
- [ ] **Logging de validaciones fallidas en services**
- [ ] **Monitoreo de queries sin filtro de empresa (si es posible)**
- [ ] **Alertas si se detectan patrones sospechosos**

**Eventos registrados en el logger `security`:**

1. **Intento de acceso sin membresía válida** (WARNING)
   - Se dispara cuando un usuario intenta acceder con `company_id` en sesión pero no tiene `Membership` activa
   - Incluye: `user_id`, `username`, `company_id`, `path`, `method`, `ip`, `user_agent`

2. **Usuario sin empresas activas** (WARNING)
   - Se dispara cuando un usuario autenticado no tiene ninguna `Membership` activa
   - Incluye: `user_id`, `username`, `path`, `method`, `ip`

3. **Ruta protegida sin empresa activa** (WARNING)
   - Se dispara cuando un usuario autenticado intenta acceder a una ruta protegida sin `current_company`
   - Incluye: `user_id`, `username`, `path`, `method`, `ip`, `user_agent`

4. **Intento de acceso cross-tenant (404)** (WARNING)
   - Se dispara cuando un usuario intenta acceder a un objeto de otra empresa
   - Incluye: `user_id`, `username`, `company_id`, `model`, `object_pk`, `path`, `method`, `ip`, `user_agent`

5. **Discrepancia de company detectada** (ERROR)
   - Se dispara cuando se detecta que un objeto no pertenece a la empresa esperada (doble verificación)
   - Incluye: `user_id`, `username`, `expected_company_id`, `object_company_id`, `model`, `object_pk`, `path`, `method`, `ip`

**Configuración:**
- **Desarrollo:** Logs a consola (handler `security_console`)
- **Producción:** Logs a archivo rotativo `logs/security.log` (10MB, 5 backups) + consola
- **Nivel:** WARNING (solo eventos de seguridad, no info rutinario)

---

### 4.7 Documentación

- [ ] **README técnico explica el modelo multi-tenant**
- [ ] **Comentarios en código explican por qué se filtra por empresa**
- [ ] **Onboarding de desarrolladores incluye guía de multi-tenant**

---

## 5. Recomendaciones Adicionales

### 5.1 Monitoreo Proactivo

Implementar un middleware de logging que detecte queries potencialmente peligrosas:

```python
# En settings/base.py
LOGGING = {
    'loggers': {
        'security.multi_tenant': {
            'handlers': ['file'],
            'level': 'WARNING',
        },
    },
}

# Middleware opcional para detectar queries sin company
class QueryMonitoringMiddleware:
    def process_response(self, request, response):
        # Log queries que no incluyen filtro de company (solo en desarrollo)
        if settings.DEBUG:
            # Analizar queries ejecutadas
            pass
        return response
```

### 5.2 Tests Automatizados de Seguridad

Agregar tests que verifiquen explícitamente que no hay fugas:

```python
def test_no_cross_company_data_leakage():
    """Verifica que un usuario no puede acceder a datos de otra empresa."""
    company1 = Company.objects.create(name='Empresa 1')
    company2 = Company.objects.create(name='Empresa 2')
    
    customer1 = Customer.objects.for_company(company1).create(...)
    customer2 = Customer.objects.for_company(company2).create(...)
    
    # Usuario de company1 no debe ver customer2
    customers = Customer.objects.for_company(company1).all()
    assert customer2 not in customers
```

### 5.3 Code Review Checklist

Incluir en proceso de code review:

- [ ] ¿Todas las queries filtran por `company`?
- [ ] ¿Todos los services validan pertenencia a empresa?
- [ ] ¿Todas las views usan mixins correctos?
- [ ] ¿Todos los formularios filtran querysets de FKs?

---

## 6. Conclusión

El enfoque actual (DB compartida + `company_id`) es **correcto y comercialmente viable** para el MVP y los primeros 50-100 clientes.

**Puntos críticos:**
1. **Disciplina en código:** Todos los desarrolladores deben seguir las reglas obligatorias
2. **Tests exhaustivos:** Tests de aislamiento son no negociables
3. **Code review estricto:** Revisar cada PR buscando fugas potenciales
4. **Monitoreo:** Detectar patrones sospechosos en producción

**Escalabilidad futura:**
- Para 100+ empresas: considerar read replicas
- Para 500+ empresas: considerar sharding por región
- Para compliance estricto: considerar schemas separados por cliente

**Prioridad comercial:**
- MVP: Aislamiento total con DB compartida ✅
- Fase 2: Optimizaciones de performance si es necesario
- Fase 3: Separación física solo si es requerimiento de cliente específico

---

**Documento vivo:** Actualizar este documento cuando se agreguen nuevas validaciones o se detecten nuevos vectores de fuga.

