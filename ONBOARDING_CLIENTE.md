# Checklist de Onboarding - Suite Business

**Versión:** 1.0  
**Última actualización:** 2026-01-09

Este checklist guía el proceso de incorporación de un nuevo cliente a Suite Business.

---

## 📋 PRE-ONBOARDING

### 1. Información del cliente
- [ ] Nombre de la empresa
- [ ] CUIT/RUT/NIT
- [ ] Email de contacto
- [ ] Teléfono de contacto
- [ ] Dirección (opcional)
- [ ] Usuarios iniciales (nombres, emails, roles)

### 2. Preparar cuenta
- [ ] Crear empresa en el sistema
- [ ] **NO marcar como demo** (`is_demo=False`)
- [ ] Configurar datos básicos de la empresa
- [ ] Crear usuarios iniciales
- [ ] Asignar roles apropiados

---

## 🚀 ONBOARDING PASO A PASO

### Paso 1: Crear Empresa

```python
# Desde Django shell o admin
from core.models import Company

company = Company.objects.create(
    name="Nombre de la Empresa",
    tax_id="20-12345678-9",  # Si aplica
    email="contacto@empresa.com",
    phone="+54 11 1234-5678",
    active=True,
    is_demo=False  # IMPORTANTE: No es demo
)
```

**Verificar:**
- [ ] Empresa creada correctamente
- [ ] `is_demo=False`
- [ ] Datos completos

---

### Paso 2: Crear Usuarios

```python
from django.contrib.auth.models import User
from core.models import Membership

# Crear usuario
user = User.objects.create_user(
    username='usuario@empresa.com',
    email='usuario@empresa.com',
    first_name='Nombre',
    last_name='Apellido',
    password='password-temporal'  # Cambiar en primer login
)

# Crear membresía
membership = Membership.objects.create(
    user=user,
    company=company,
    role='admin',  # o 'manager', 'operator', 'viewer'
    active=True
)
```

**Verificar:**
- [ ] Usuarios creados
- [ ] Membresías asignadas
- [ ] Roles correctos
- [ ] Emails válidos

---

### Paso 3: Configuración Inicial

**Datos mínimos recomendados:**
- [ ] Al menos 3-5 clientes principales
- [ ] Al menos 2-3 proveedores principales
- [ ] Catálogo básico de productos/servicios (10-20 items)
- [ ] 1-2 operaciones de ejemplo (opcional, para mostrar)

**⚠️ IMPORTANTE:**
- No cargar datos de prueba masivos
- No usar datos del stress test
- Usar datos reales o representativos del cliente

---

## 📞 PRIMERA LLAMADA CON EL CLIENTE

### Objetivo
Mostrar el sistema y guiar los primeros pasos.

### Duración
30-45 minutos

### Agenda

#### 1. Introducción (5 min)
- Presentar Suite Business
- Explicar qué van a ver
- Confirmar que tienen acceso

#### 2. Login y Dashboard (5 min)
- Mostrar cómo hacer login
- Explicar el dashboard
- Mostrar KPIs principales

#### 3. Primeros Pasos (15 min)

**Recomendación de orden:**
1. **Clientes** (5 min)
   - Mostrar cómo agregar un cliente
   - Explicar por qué es importante
   - "Una vez que tengas clientes, podés seleccionarlos rápido al registrar ventas"

2. **Productos** (5 min)
   - Mostrar cómo agregar un producto
   - Explicar catálogo
   - "Una vez que tengas productos, podés agregarlos con un click a las operaciones"

3. **Primera Operación** (5 min)
   - Crear una venta de ejemplo juntos
   - Mostrar el flujo completo
   - Explicar borrador vs confirmado

#### 4. Reportes (5 min)
- Mostrar dónde están los reportes
- Explicar para qué sirve cada uno
- Mencionar exportación a Excel

#### 5. Preguntas y Cierre (10 min)
- Responder dudas
- Confirmar próximos pasos
- Agendar seguimiento (opcional)

---

## ✅ QUÉ MOSTRAR EN LA PRIMERA LLAMADA

### ✅ SÍ mostrar:
- Dashboard con KPIs
- Cómo agregar clientes
- Cómo agregar productos
- Cómo crear una operación
- Cómo ver reportes
- Exportación a Excel

### ❌ NO mostrar:
- Configuraciones técnicas
- Django admin
- Logs o consola
- Funcionalidades no implementadas
- Datos de otros clientes
- Código fuente

---

## ⚠️ QUÉ NO TOCAR

### Durante el onboarding:
- ❌ No modificar modelos
- ❌ No cambiar configuraciones del sistema
- ❌ No acceder a Django admin (a menos que sea necesario)
- ❌ No mostrar datos de otros clientes
- ❌ No crear datos de prueba masivos
- ❌ No modificar lógica de negocio

### Si el cliente pide algo:
1. Escuchar la necesidad
2. Documentar la solicitud
3. Evaluar si es configuración o desarrollo
4. No improvisar cambios en producción

---

## 📝 SEGUIMIENTO POST-ONBOARDING

### Día 1
- [ ] Enviar email de bienvenida
- [ ] Confirmar que pueden hacer login
- [ ] Responder dudas iniciales

### Semana 1
- [ ] Verificar que están usando el sistema
- [ ] Preguntar si tienen dudas
- [ ] Ofrecer ayuda adicional

### Mes 1
- [ ] Revisar uso del sistema
- [ ] Identificar mejoras necesarias
- [ ] Confirmar satisfacción

---

## 🎯 OBJETIVOS DEL ONBOARDING

### Que el cliente:
1. ✅ Entienda cómo funciona el sistema
2. ✅ Sepa cómo empezar a usarlo
3. ✅ Tenga confianza en el producto
4. ✅ Vea valor inmediato
5. ✅ Quiera seguir usándolo

### Que nosotros:
1. ✅ Tengamos un cliente satisfecho
2. ✅ Reduzcamos soporte futuro
3. ✅ Identifiquemos mejoras
4. ✅ Generemos confianza

---

## 📋 CHECKLIST RÁPIDO

### Antes de la llamada:
- [ ] Empresa creada
- [ ] Usuarios creados
- [ ] Acceso verificado
- [ ] Datos iniciales cargados (opcional)
- [ ] Agenda preparada

### Durante la llamada:
- [ ] Login exitoso
- [ ] Dashboard explicado
- [ ] Primeros pasos mostrados
- [ ] Dudas respondidas
- [ ] Próximos pasos acordados

### Después de la llamada:
- [ ] Email de seguimiento enviado
- [ ] Documentación compartida
- [ ] Próximo contacto agendado

---

## 🆘 TROUBLESHOOTING

### Cliente no puede hacer login
- Verificar que el usuario existe
- Verificar que la membresía está activa
- Verificar que la empresa está activa
- Verificar credenciales

### Cliente no ve su empresa
- Verificar membresía
- Verificar que seleccionó la empresa
- Verificar que la empresa está activa

### Cliente ve datos de otro cliente
- **PROBLEMA CRÍTICO DE SEGURIDAD**
- Detener inmediatamente
- Revisar middleware de multi-tenant
- Contactar al equipo técnico

---

## 📞 CONTACTO

Para dudas sobre onboarding:
- Revisar este documento
- Consultar con el equipo
- Documentar nuevas situaciones

---

**Última revisión:** 2026-01-09  
**Próxima revisión:** Después de cada onboarding importante

