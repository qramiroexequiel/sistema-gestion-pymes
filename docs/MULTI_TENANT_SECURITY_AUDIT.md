# Auditoría de Seguridad Multi-Tenant
## Revisión Completa del Sistema

**Fecha:** Enero 2026  
**Revisado por:** Ingeniero de Software Senior  
**Estado:** ✅ Sistema cumple con principios fundamentales de seguridad multi-tenant

---

## 1. Arquitectura Multi-Tenant - ✅ CUMPLE

### 1.1 Base de Datos Compartida
- ✅ Una sola base de datos PostgreSQL compartida
- ✅ Separación lógica mediante `company_id` en todas las tablas de negocio
- ✅ No hay múltiples bases de datos ni schemas separados

### 1.2 Modelos con Campo `company`

**Modelos que DEBEN tener `company` (y lo tienen):**
- ✅ `Customer` - Hereda de `CompanyModelMixin`
- ✅ `Supplier` - Hereda de `CompanyModelMixin`
- ✅ `Product` - Hereda de `CompanyModelMixin`
- ✅ `Operation` - Hereda de `CompanyModelMixin`
- ✅ `AuditLog` - Tiene `company` FK explícita
- ✅ `CompanySettings` - OneToOne con `Company` (equivalente)

**Modelos que NO requieren `company` (justificado):**
- ✅ `Company` - Modelo global (correcto)
- ✅ `Membership` - Modelo de relación usuario-empresa (correcto)
- ✅ `User` - Modelo estándar de Django (correcto)
- ⚠️ `OperationItem` - No tiene `company` directamente, pero:
  - Siempre se accede a través de `Operation` (que sí tiene `company`)
  - En services, se valida que `operation` pertenezca a `company`
  - No hay acceso directo a `OperationItem` sin pasar por `Operation`
  - **Recomendación:** Considerar agregar `company` denormalizado en futuras versiones para mayor seguridad defensiva

### 1.3 Validación de `company` en Modelos
- ✅ `CompanyModelMixin` garantiza `null=False, blank=False`
- ✅ Índices en `(company, ...)` para optimización
- ✅ Constraints `unique_together` incluyen `company` donde aplica

---

## 2. Middleware Multi-Tenant - ✅ CUMPLE

### 2.1 CompanyMiddleware (`core/middleware.py`)
- ✅ Valida `Membership` activa antes de establecer `request.current_company`
- ✅ Verifica que `company.active=True`
- ✅ Limpia sesión si membresía deja de existir
- ✅ Auto-selecciona primera empresa disponible si no hay selección
- ✅ Maneja rutas públicas correctamente (`/login/`, `/static/`, `/media/`)
- ✅ Permite acceso a `/admin/` para superusers sin empresa
- ✅ Logging de seguridad para eventos críticos

### 2.2 Garantías del Middleware
- ✅ `request.current_company` es `None` o una instancia válida de `Company`
- ✅ `request.current_membership` es `None` o una instancia válida de `Membership`
- ✅ Imposible tener `current_company` sin `Membership` activa
- ✅ Imposible tener `current_company` inactiva

---

## 3. Managers y QuerySets - ✅ CUMPLE

### 3.1 CompanyManager (`core/managers.py`)
- ✅ NO filtra automáticamente (evita falsa sensación de seguridad)
- ✅ Método explícito `for_company(company)` obligatorio
- ✅ `get_or_404_for_company()` con validación de pertenencia
- ✅ Lanza `ValidationError` si `company` es `None`

### 3.2 Uso de Managers en Modelos
- ✅ `Customer.objects = CompanyManager()`
- ✅ `Supplier.objects = CompanyManager()`
- ✅ `Product.objects = CompanyManager()`
- ✅ `Operation.objects = CompanyManager()`

### 3.3 Regla Obligatoria
- ✅ Todas las consultas usan `.for_company(company)` explícitamente
- ✅ No hay uso de `Model.objects.all()` sin filtrar
- ✅ No hay uso de `Model.objects.get()` sin filtrar por company

---

## 4. Mixins de Seguridad - ✅ CUMPLE

### 4.1 CompanyRequiredMixin
- ✅ Requiere autenticación
- ✅ Requiere `current_company` activa
- ✅ Redirige a selección de empresa si no hay empresa pero hay memberships
- ✅ Cierra sesión si no hay memberships válidas
- ✅ Alias `TenantRequiredMixin` disponible

### 4.2 CompanyFilterMixin
- ✅ Fuerza filtrado por empresa en `get_queryset()`
- ✅ Preserva optimizaciones del queryset (select_related, prefetch_related)
- ✅ Imposible omitir el filtrado
- ✅ Retorna queryset vacío si no hay empresa

### 4.3 CompanyObjectMixin
- ✅ Obtiene objeto desde queryset filtrado por empresa
- ✅ Preserva optimizaciones del queryset
- ✅ Doble verificación: filtra por company y valida pertenencia
- ✅ Logging de intentos de acceso cross-tenant
- ✅ Retorna 404 si objeto no pertenece a empresa

### 4.4 RoleRequiredMixin
- ✅ Valida rol en empresa activa
- ✅ Requiere `current_membership` válida
- ✅ Lanza `PermissionDenied` si rol no es suficiente

---

## 5. Views y Acceso a Datos - ✅ CUMPLE

### 5.1 Uso de Mixins en Views
- ✅ Todas las ListView usan `CompanyFilterMixin`
- ✅ Todas las DetailView/UpdateView/DeleteView usan `CompanyObjectMixin`
- ✅ Todas las views protegidas usan `CompanyRequiredMixin`
- ✅ Views que requieren roles usan `RoleRequiredMixin`

### 5.2 Uso de `.objects.get()` y `get_object_or_404()`

**Casos Revisados:**

1. **`operations/views.py` líneas 254, 305:**
   ```python
   operation = get_object_or_404(
       Operation.objects.for_company(company),
       pk=pk
   )
   ```
   ✅ **CORRECTO:** Filtra por company primero

2. **`operations/services.py` línea 145:**
   ```python
   item = OperationItem.objects.get(id=item_id, operation=operation)
   ```
   ✅ **CORRECTO:** Filtra por `operation` que ya está validado que pertenece a `company`

3. **`core/views.py` línea 56:**
   ```python
   membership = Membership.objects.get(
       user=request.user,
       company_id=company_id,
       active=True
   )
   ```
   ✅ **CORRECTO:** `Membership` es modelo de relación, no de negocio directo. Filtra por `user` y `company_id` explícitamente.

4. **`core/mixins.py` línea 231:**
   ```python
   obj = get_object_or_404(queryset_filtered, pk=pk)
   ```
   ✅ **CORRECTO:** `queryset_filtered` ya está filtrado por company

### 5.3 Regla Aplicada
- ✅ **NUNCA** se usa `Model.objects.get(pk=...)` sin filtrar por company
- ✅ **SIEMPRE** se filtra por company antes de obtener objeto por ID
- ✅ Todas las vistas usan mixins que garantizan el filtrado

---

## 6. Services Layer - ✅ CUMPLE

### 6.1 Separación de Lógica
- ✅ Toda la lógica de negocio está en `services.py`
- ✅ Views son delgadas: validan, delegan a services, renderizan
- ✅ Cálculos (totales, impuestos) en services
- ✅ Validaciones de negocio en services

### 6.2 Validaciones Multi-Tenant en Services

**`operations/services.py`:**
- ✅ `create_operation()` valida que `customer.company == company`
- ✅ `create_operation()` valida que `supplier.company == company`
- ✅ `add_item_to_operation()` valida que `product.company == operation.company`
- ✅ `remove_item_from_operation()` filtra por `operation` (ya validado)
- ✅ `recalculate_operation_totals()` filtra items por `operation` (ya validado)

**Regla Aplicada:**
- ✅ Todos los services reciben `company` como parámetro explícito
- ✅ Validación de pertenencia a empresa antes de crear/modificar
- ✅ Lanzan `ValidationError` si hay discrepancia de empresa

---

## 7. Admin de Django - ✅ CUMPLE

### 7.1 Protección en Admin

**Todos los admins implementan `get_queryset()`:**
- ✅ `CustomerAdmin` - Filtra por `company` para no-superusers
- ✅ `SupplierAdmin` - Filtra por `company` para no-superusers
- ✅ `ProductAdmin` - Filtra por `company` para no-superusers
- ✅ `OperationAdmin` - Filtra por `company` para no-superusers
- ✅ `OperationItemAdmin` - Filtra por `operation__company` para no-superusers
- ✅ `AuditLogAdmin` - Filtra por `company` para no-superusers
- ✅ `MembershipAdmin` - Filtra por `user` para no-superusers (solo ven sus propias memberships)

**Regla Aplicada:**
- ✅ Superusers pueden ver todo (correcto para administración)
- ✅ No-superusers solo ven datos de su empresa activa
- ✅ Retorna queryset vacío si no hay empresa activa

### 7.2 Campos en Admin
- ✅ `company` visible en list_display donde aplica
- ✅ `company` en list_filter para superusers
- ✅ `raw_id_fields` para relaciones (mejora performance)

---

## 8. Reportes - ✅ CUMPLE

### 8.1 Filtrado por Empresa
- ✅ `SalesByPeriodView` - Usa `Operation.objects.for_company(company)`
- ✅ `PurchasesByPeriodView` - Usa `Operation.objects.for_company(company)`
- ✅ `SummaryByCustomerView` - Filtra por empresa activa
- ✅ `SummaryBySupplierView` - Filtra por empresa activa

### 8.2 Exportación CSV
- ✅ Todas las exportaciones respetan filtros de empresa
- ✅ Solo exportan datos de empresa activa
- ✅ No hay forma de exportar datos de otra empresa

---

## 9. Logging de Seguridad - ✅ CUMPLE

### 9.1 Eventos Registrados
- ✅ Intento de acceso sin membresía válida (WARNING)
- ✅ Usuario sin empresas activas (WARNING)
- ✅ Ruta protegida sin empresa activa (WARNING)
- ✅ Intento de acceso cross-tenant (404) (WARNING)
- ✅ Discrepancia de company detectada (ERROR)

### 9.2 Datos Registrados
- ✅ `user_id`, `username`
- ✅ `company_id` (cuando aplica)
- ✅ `path`, `method`
- ✅ `ip_address`
- ✅ `user_agent` (truncado a 100 caracteres)

### 9.3 Configuración
- ✅ Logger dedicado `security`
- ✅ Desarrollo: salida a consola
- ✅ Producción: salida a archivo rotativo + consola
- ✅ Nivel WARNING para eventos de seguridad

---

## 10. Validaciones Defensivas - ✅ CUMPLE

### 10.1 A Nivel de Modelo
- ✅ `Operation.clean()` valida cliente/proveedor según tipo
- ✅ `CompanyModelMixin` garantiza `company` no nulo
- ✅ Constraints `unique_together` incluyen `company`

### 10.2 A Nivel de Service
- ✅ Validación de pertenencia a empresa antes de operaciones
- ✅ Validación de relaciones (cliente/proveedor/producto pertenecen a misma empresa)
- ✅ Lanzan excepciones claras si hay discrepancias

### 10.3 A Nivel de View
- ✅ Mixins validan antes de procesar request
- ✅ Doble verificación en `CompanyObjectMixin`
- ✅ Logging de intentos sospechosos

---

## 11. Puntos de Mejora Recomendados (No Críticos)

### 11.1 OperationItem - Campo `company` Denormalizado

**Situación Actual:**
- `OperationItem` no tiene campo `company` directamente
- Se accede siempre a través de `Operation` (que sí tiene `company`)
- En services, se valida que `operation` pertenezca a `company`

**Recomendación:**
- Agregar campo `company` denormalizado en `OperationItem` para:
  - Mayor seguridad defensiva
  - Consultas más eficientes sin JOIN
  - Validación directa sin depender de `operation`

**Prioridad:** Baja (el sistema actual es seguro, pero la denormalización añadiría una capa extra de protección)

**Implementación:**
```python
class OperationItem(models.Model):
    operation = models.ForeignKey(Operation, ...)
    company = models.ForeignKey(Company, ...)  # Denormalizado desde operation
    # ... otros campos
```

**Migración requerida:** Sí, pero no urgente.

---

### 11.2 Constraint de Base de Datos para OperationItem

**Recomendación:**
- Agregar constraint CHECK en base de datos:
  ```sql
  CHECK (company_id = (SELECT company_id FROM operations_operation WHERE id = operation_id))
  ```
- Garantiza consistencia a nivel de base de datos
- Previene inconsistencias incluso si hay bugs en código

**Prioridad:** Media (añade protección a nivel de DB)

---

### 11.3 Tests Adicionales

**Recomendación:**
- Test para verificar que `OperationItem` no puede ser accedido directamente sin validar `operation.company`
- Test para verificar constraint de `OperationItem.company == Operation.company`
- Test de performance para queries con muchos items

**Prioridad:** Media (los tests actuales cubren casos principales)

---

## 12. Conclusión

### 12.1 Estado General: ✅ SEGURO

El sistema cumple con todos los principios fundamentales de seguridad multi-tenant:

- ✅ Arquitectura correcta (DB compartida + `company_id`)
- ✅ Middleware robusto
- ✅ Managers que requieren filtrado explícito
- ✅ Mixins que previenen fugas
- ✅ Services que validan pertenencia
- ✅ Admin protegido
- ✅ Logging de seguridad
- ✅ Validaciones defensivas en múltiples capas

### 12.2 Garantías de Aislamiento

**Bajo ninguna circunstancia una empresa puede:**
- ✅ Ver datos de otra empresa (filtrado obligatorio)
- ✅ Modificar datos de otra empresa (validación en múltiples capas)
- ✅ Inferir datos de otra empresa (404 en lugar de información)

### 12.3 Recomendaciones

1. **Inmediatas:** Ninguna (sistema es seguro)
2. **Corto plazo:** Considerar denormalización de `company` en `OperationItem`
3. **Mediano plazo:** Agregar constraints de DB para mayor robustez

### 12.4 Próximos Pasos

- ✅ Sistema listo para producción
- ✅ Mantener disciplina en código futuro (usar mixins, managers, services)
- ✅ Revisar periódicamente que no se introduzcan accesos directos sin filtrado
- ✅ Monitorear logs de seguridad en producción

---

**Última actualización:** Enero 2026  
**Próxima revisión:** Después de agregar nuevas funcionalidades significativas

