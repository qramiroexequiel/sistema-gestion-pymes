# Guía Completa de Stress Test - Suite Business

## Objetivo

Realizar un stress test completo del sistema simulando un entorno REAL con alto volumen de datos y uso intensivo, como si el sistema ya tuviera clientes activos desde hace meses.

---

## FASE 1: CARGA MASIVA DE DATOS

### Requisitos Previos

1. Tener una empresa creada en el sistema
2. Obtener el ID de la empresa:
   ```bash
   python manage.py shell
   >>> from core.models import Company
   >>> Company.objects.all().values('id', 'name')
   ```

### Ejecutar Carga de Datos

```bash
# Activar entorno virtual
source venv/bin/activate

# Cargar todos los datos (500 clientes, 100 proveedores, 5000 productos, 100 operaciones)
python manage.py load_stress_test_data --company-id=1

# O solo cargar datos base (sin operaciones)
python manage.py load_stress_test_data --company-id=1 --skip-operations
```

### Verificar Carga

```bash
# Generar informe de datos cargados
python manage.py generate_stress_test_report --company-id=1
```

**Resultado esperado:**
- ✓ 500 clientes
- ✓ 100 proveedores
- ✓ 5000 productos/servicios (70% productos, 30% servicios)
- ✓ 100 operaciones (70 ventas, 30 compras)

---

## FASE 2: SIMULACIÓN INTENSIVA DE REPORTES

### Ejecutar Simulación de Reportes

```bash
# Simular 2000 reportes (default)
python manage.py stress_test_reports --company-id=1

# Simular más reportes
python manage.py stress_test_reports --company-id=1 --count=5000
```

**Qué hace:**
- Ejecuta combinaciones reales de filtros
- Mide tiempos de ejecución
- Cuenta queries ejecutadas
- Detecta errores

**Resultado esperado:**
- Tiempo promedio < 1.0s
- Tiempo máximo < 3.0s
- Queries por reporte < 10 (idealmente)

---

## FASE 3: SIMULACIÓN DE USO REAL

### Navegación Manual

1. **Dashboard:**
   - Verificar que los KPIs se carguen correctamente
   - Verificar legibilidad con datos reales
   - Verificar jerarquía visual

2. **Clientes:**
   - Navegar lista de 500 clientes
   - Usar filtros (búsqueda, estado)
   - Verificar paginación
   - Verificar tiempos de carga

3. **Proveedores:**
   - Navegar lista de 100 proveedores
   - Usar filtros
   - Verificar paginación

4. **Productos:**
   - Navegar lista de 5000 productos
   - Usar filtros (tipo, estado, búsqueda)
   - Verificar paginación
   - Verificar tiempos de carga

5. **Operaciones:**
   - Navegar lista de 100 operaciones
   - Usar filtros (tipo, estado, búsqueda)
   - Verificar paginación
   - Verificar tiempos de carga

6. **Reportes:**
   - Generar reportes con diferentes rangos de fechas
   - Exportar a CSV
   - Verificar tiempos de generación

---

## FASE 4: PERFORMANCE Y ESCALABILIDAD

### Detectar Problemas

1. **Queries N+1:**
   - Activar Django Debug Toolbar (si está disponible)
   - Revisar logs de queries
   - Verificar uso de `select_related` y `prefetch_related`

2. **Listados Lentos:**
   - Verificar índices en base de datos
   - Verificar paginación
   - Verificar filtros eficientes

3. **Reportes Lentos:**
   - Revisar queries de agregación
   - Verificar uso de índices
   - Considerar caché si es necesario

### Comandos Útiles

```bash
# Verificar índices en base de datos
python manage.py dbshell
# Luego ejecutar: \d+ customers_customer

# Activar logging de queries (en settings)
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

---

## FASE 5: UX CON DATOS REALES

### Checklist de UX

- [ ] Dashboard se ve claro con datos reales
- [ ] Listados no se sienten saturados
- [ ] Filtros son intuitivos
- [ ] Búsquedas funcionan correctamente
- [ ] Paginación es clara
- [ ] Empty states no aparecen incorrectamente
- [ ] Textos siguen siendo claros con muchos datos
- [ ] Jerarquía visual se mantiene

### Ajustes Necesarios

Si se detectan problemas:
1. Documentar el problema
2. Evaluar impacto
3. Priorizar correcciones
4. Implementar solo si mejora claridad/lectura/toma de decisiones

---

## FASE 6: VALIDACIÓN DE BRANDING

### Checklist de Branding

- [ ] "Suite Business" aparece correctamente en todo el sistema
- [ ] "by ReqTech" es discreto y solo en footer/login
- [ ] No quedan textos genéricos ("Sistema de Gestión", etc.)
- [ ] El sistema se siente premium, no de prueba
- [ ] Tagline aparece en login
- [ ] Branding es consistente en todas las pantallas

---

## FASE 7: INFORME FINAL

### Generar Informe

```bash
python manage.py generate_stress_test_report --company-id=1 --output=stress_test_report.txt
```

### Evaluar Resultados

**Preguntas clave:**
1. ¿Qué funcionó perfecto?
2. ¿Qué funciona pero puede mejorar?
3. ¿Qué sería un problema en producción?
4. ¿Impacto de 2000+ reportes?
5. ¿Soporta 10 clientes reales?
6. ¿Soporta 50 clientes reales?
7. ¿Soporta 100 clientes reales?
8. ¿La demo impresiona?
9. ¿Justifica el precio?
10. ¿Dónde se puede ganar más valor?

---

## COMANDOS RÁPIDOS

```bash
# Cargar datos
python manage.py load_stress_test_data --company-id=1

# Simular reportes
python manage.py stress_test_reports --company-id=1 --count=2000

# Generar informe
python manage.py generate_stress_test_report --company-id=1

# Limpiar datos (opcional, usar con cuidado)
python manage.py shell
>>> from core.models import Company
>>> company = Company.objects.get(id=1)
>>> company.customers.all().delete()
>>> company.suppliers.all().delete()
>>> company.products.all().delete()
>>> company.operations.all().delete()
```

---

## NOTAS IMPORTANTES

⚠️ **NO optimizar prematuramente**
- Solo optimizar lo crítico
- Solo lo que afecte demo o producción

⚠️ **NO romper arquitectura**
- Mantener separación multi-tenant
- Mantener seguridad
- Mantener lógica de negocio

⚠️ **TODO debe ser reproducible**
- Documentar todos los pasos
- Guardar resultados
- Comparar antes/después

---

## RESULTADO ESPERADO

Un sistema que:
- ✅ Soporta alto volumen de datos
- ✅ Genera reportes rápidamente
- ✅ Se ve profesional con datos reales
- ✅ Está listo para demo comercial
- ✅ Está listo para producción

---

**Este stress test valida que Suite Business es un producto SaaS real, no un prototipo.**

