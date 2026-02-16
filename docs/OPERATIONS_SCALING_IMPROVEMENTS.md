# Mejoras de escalado: Operaciones (descuentos y múltiples impuestos)

Este documento propone mejoras para el módulo de operaciones cuando el sistema escale: **descuentos** (por ítem o por operación) y **múltiples tasas de impuestos** (por ítem o por tipo).

---

## Estado actual (resumen)

- **Impuesto:** Una sola tasa por empresa (`CompanySettings.tax_rate_default`), aplicada sobre el subtotal de la operación. Cálculo: `tax = subtotal * (tasa / 100)`, todo en `Decimal` con cuantización a 2 decimales.
- **Descuentos:** No implementados.
- **Atomicidad:** La creación de operación + ítems se hace dentro de `transaction.atomic()` en la vista; la confirmación ya era atómica con `@transaction.atomic` en el servicio.

---

## 1. Descuentos

### 1.1 Descuento por ítem

**Objetivo:** Poder aplicar un descuento (porcentaje o monto fijo) a cada línea.

**Cambios sugeridos:**

- **Modelo `OperationItem`:**
  - `discount_type`: `CharField` con choices `('percent', 'amount')` (opcional, default `'percent'`).
  - `discount_value`: `DecimalField(max_digits=12, decimal_places=2, default=0)`.
  - Subtotal del ítem:  
    `subtotal_item = (quantity * unit_price) - descuento_calculado`  
    con `descuento_calculado` en `Decimal` y cuantizado a 2 decimales.

- **Servicios:**
  - En `add_item_to_operation` y `update_operation_item`: aceptar `discount_type` y `discount_value` opcionales; calcular subtotal del ítem restando el descuento.
  - En `recalculate_operation_totals`: subtotal de la operación = suma de los `subtotal` de cada ítem (ya con descuento aplicado). No sumar `quantity * unit_price` y restar descuentos a nivel operación para evitar inconsistencias.

- **Precisión:** Todo en `Decimal`; descuento en %:  
  `descuento = (quantity * unit_price * discount_value / 100).quantize(TWOPLACES, ROUND_HALF_UP)`.

### 1.2 Descuento a nivel operación

**Objetivo:** Un descuento global (ej. “10% sobre el total” o “$500 off”).

**Cambios sugeridos:**

- **Modelo `Operation`:**
  - `discount_type`: `('percent', 'amount')`, opcional.
  - `discount_value`: `DecimalField(..., default=0)`.

- **Cálculo de totales (orden recomendado):**
  1. Subtotal operación = suma de subtotales de ítems (con descuentos por ítem ya aplicados).
  2. Descuento operación = según `discount_type` sobre subtotal (o sobre subtotal − otros descuentos, según regla de negocio).
  3. Base imponible = subtotal − descuento operación (cuantizado).
  4. Impuesto = base imponible × tasa(s) — ver sección 2.
  5. Total = base imponible + impuesto.

- **Servicios:** Actualizar `recalculate_operation_totals` para aplicar descuento de operación antes de calcular impuesto y total; mantener todo en `Decimal` y cuantizar en cada paso.

---

## 2. Múltiples tasas de impuesto

### 2.1 Una tasa por operación (actual + mejora opcional)

- Hoy: una sola tasa en `CompanySettings.tax_rate_default`; en `recalculate_operation_totals` se usa `get_company_tax_rate(operation.company)`.
- Mejora posible: permitir **sobrescribir la tasa en la operación** (ej. factura exportación 0%): en `Operation` agregar `tax_rate_override` (nullable `DecimalField`); en el servicio, si está definido usar ese valor, si no usar `get_company_tax_rate(operation.company)`.

### 2.2 Una tasa por ítem (por producto o por línea)

**Objetivo:** Diferentes alícuotas por línea (ej. 21%, 10.5%, 0%).

**Opción A – Tasa en el ítem:**

- **Modelo `OperationItem`:**
  - `tax_rate`: `DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)`.
  - Si es `None`, usar la tasa por defecto de la empresa (o de la operación si se implementa `tax_rate_override`).

- **Cálculo:**
  - Subtotal por ítem (con descuentos de ítem ya aplicados).
  - Impuesto ítem = `subtotal_ítem * (tax_rate_ítem / 100)`.
  - En `recalculate_operation_totals`:  
    - `operation.subtotal` = suma de subtotales de ítems.  
    - `operation.tax` = suma de impuestos por ítem.  
    - `operation.total` = subtotal + tax.  
  - Todo en `Decimal` y cuantizado a 2 decimales.

**Opción B – Tasa por tipo de producto:**

- En `Product` agregar `tax_rate` (o FK a un modelo `TaxRate`).
- Al crear/actualizar ítem, tomar la tasa del producto por defecto y permitir sobrescribir en la línea (como en Opción A).

### 2.3 Varios impuestos por ítem (IVA + otros)

**Objetivo:** Varias líneas de impuesto (ej. IVA 21% + impuesto interno 5%).

**Cambios sugeridos:**

- **Modelo nuevo `OperationItemTax`:**
  - `operation_item`: FK a `OperationItem`.
  - `tax_name`: CharField (ej. "IVA", "Impuesto interno").
  - `tax_rate`: DecimalField.
  - `amount`: DecimalField (monto calculado).

- **Cálculo:** Por cada ítem, para cada impuesto:  
  `amount = (subtotal_ítem * rate / 100).quantize(TWOPLACES)`.

- **Operación:**  
  - `operation.tax` = suma de todos los `OperationItemTax.amount` de la operación (o mantener un campo `tax` calculado y dejar `OperationItemTax` para el detalle/exportación).

- **Servicios:** Recalcular `OperationItemTax` en cada `recalculate_operation_totals` (o al guardar ítems) dentro de la misma transacción para mantener consistencia.

---

## 3. Orden de implementación sugerido

1. **Fase 1 – Descuento por ítem**  
   Campos en `OperationItem`, ajuste de subtotal ítem y de `recalculate_operation_totals` (subtotal operación = suma de subtotales ítem). Sin cambiar modelo de impuesto.

2. **Fase 2 – Tasa por ítem (o override por operación)**  
   Opción más simple según necesidad: solo `tax_rate` en ítem o solo `tax_rate_override` en operación. Actualizar `recalculate_operation_totals` para impuesto por ítem o por operación según corresponda.

3. **Fase 3 – Descuento a nivel operación**  
   Campos en `Operation`, orden de cálculo: subtotal → descuento operación → base imponible → impuesto → total.

4. **Fase 4 – Múltiples impuestos por ítem**  
   Modelo `OperationItemTax`, cálculo y persistencia en la misma transacción que el recálculo de totales.

En todos los pasos conviene mantener:
- Uso exclusivo de `Decimal` y cuantización a 2 decimales en cada paso intermedio.
- Total de la operación = subtotal − descuentos + impuestos, con redondeo final explícito.
