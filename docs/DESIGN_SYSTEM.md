# Sistema de Diseño Premium
## Guía de Referencia Visual

**Versión:** 1.0  
**Fecha:** Enero 2026  
**Propósito:** Documento de referencia para mantener consistencia visual premium en todo el sistema

---

## 1. Filosofía de Diseño

### 1.1 Principios Fundamentales

- **Confianza:** Transmitir seguridad y profesionalismo
- **Orden:** Jerarquía visual clara y estructurada
- **Simplicidad:** Menos elementos, más aire
- **Profesionalismo:** Producto premium, no template genérico
- **Atemporalidad:** Diseño que resiste el paso del tiempo

### 1.2 Inspiración

- SaaS B2B premium internacional
- Dashboards financieros modernos
- Software empresarial de alto nivel
- Productos utilizados diariamente durante años

---

## 2. Paleta de Colores

### 2.1 Colores Principales

```css
--color-primary: #2563eb        /* Azul profesional */
--color-primary-dark: #1e40af   /* Azul oscuro */
--color-primary-light: #3b82f6  /* Azul claro */
```

### 2.2 Colores de Estado

```css
--color-success: #10b981        /* Verde - éxito */
--color-warning: #f59e0b        /* Ámbar - advertencia */
--color-danger: #ef4444         /* Rojo - peligro */
--color-info: #06b6d4           /* Cyan - información */
```

### 2.3 Escala de Grises (Neutros)

```css
--color-gray-50: #f8fafc        /* Fondo más claro */
--color-gray-100: #f1f5f9
--color-gray-200: #e2e8f0       /* Bordes sutiles */
--color-gray-300: #cbd5e1
--color-gray-400: #94a3b8       /* Texto secundario */
--color-gray-500: #64748b       /* Texto deshabilitado */
--color-gray-600: #475569
--color-gray-700: #334155       /* Texto normal */
--color-gray-800: #1e293b       /* Texto fuerte */
--color-gray-900: #0f172a       /* Texto más oscuro */
```

### 2.4 Uso de Colores

**Primario:**
- Botones principales
- Links importantes
- Indicadores activos
- Acentos visuales

**Éxito:**
- Confirmaciones
- Estados positivos
- Ventas

**Advertencia:**
- Alertas
- Estados pendientes
- Requiere atención

**Peligro:**
- Eliminaciones
- Cancelaciones
- Errores críticos

**Información:**
- Compras
- Información general
- Comunicaciones

---

## 3. Tipografía

### 3.1 Familia de Fuentes

**Inter** - Fuente principal
- Moderna, legible y profesional
- Optimizada para pantallas
- Excelente legibilidad en todos los tamaños

**Fallback:**
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

### 3.2 Escala Tipográfica

```css
/* Tamaños */
--font-size-base: 0.9375rem    /* 15px - Body text */
h1: 1.875rem                    /* 30px - Títulos principales */
h2: 1.5rem                      /* 24px - Subtítulos */
h3: 1.25rem                     /* 20px - Encabezados sección */
h4: 1.125rem                    /* 18px - Encabezados menores */
small: 0.875rem                 /* 14px - Texto pequeño */
caption: 0.75rem                /* 12px - Etiquetas */

/* Pesos */
300: Light
400: Regular (normal)
500: Medium (semi-bold)
600: Semi-bold
700: Bold
```

### 3.3 Line Height

```css
--line-height-base: 1.6        /* Cómodo para lectura */
```

### 3.4 Espaciado de Texto

- Letras: normal (sin tracking excesivo)
- Secciones títulos: `letter-spacing: 0.05em` (mayúsculas)

---

## 4. Espaciado

### 4.1 Sistema de Espaciado

Basado en múltiplos de 0.5rem (8px):

```
0.25rem = 4px   (xs)
0.5rem = 8px    (sm)
0.75rem = 12px  (md)
1rem = 16px     (base)
1.5rem = 24px   (lg)
2rem = 32px     (xl)
2.5rem = 40px   (2xl)
3rem = 48px     (3xl)
```

### 4.2 Uso de Espaciado

**Padding:**
- Cards: `1.5rem` (24px)
- Botones: `0.625rem 1.25rem` (10px vertical, 20px horizontal)
- Inputs: `0.625rem 0.875rem` (10px vertical, 14px horizontal)

**Margin:**
- Entre secciones: `2rem` (32px)
- Entre elementos: `1rem` (16px)
- Entre elementos pequeños: `0.5rem` (8px)

---

## 5. Sombras

### 5.1 Sistema de Sombras

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)
```

### 5.2 Uso de Sombras

- **sm:** Bordes sutiles, elementos en reposo
- **md:** Cards al hover, elementos elevados
- **lg:** Modales, dropdowns, elementos destacados

---

## 6. Bordes

### 6.1 Border Radius

```css
--border-radius: 0.5rem        /* 8px - Cards, contenedores */
--border-radius-sm: 0.375rem   /* 6px - Botones, inputs */
```

### 6.2 Border Color

```css
--border-color: var(--color-gray-200)  /* Bordes sutiles */
```

### 6.3 Border Width

- Normal: `1px`
- Acentos: `2px` (líneas de estado, separadores)

---

## 7. Layout

### 7.1 Estructura Principal

```
┌─────────────────────────────────────┐
│ Sidebar (260px) │ Main Content      │
│                 │                   │
│ Navigation      │ Top Header        │
│                 │                   │
│                 │ Page Content      │
│                 │                   │
└─────────────────────────────────────┘
```

### 7.2 Sidebar

- **Ancho:** 260px (fijo)
- **Fondo:** Blanco
- **Borde:** Derecha, 1px, gris claro
- **Posición:** Fija, izquierda
- **Scroll:** Personalizado, discreto

### 7.3 Main Content

- **Margen izquierdo:** 260px (desktop)
- **Background:** Gris muy claro (#f8fafc)
- **Padding:** 2rem (32px)

### 7.4 Top Header

- **Altura:** Auto (padding 1rem)
- **Posición:** Sticky, top
- **Background:** Blanco
- **Borde inferior:** 1px, gris claro
- **Sombra:** Sutil

---

## 8. Componentes

### 8.1 Botones

**Primario:**
- Background: `var(--color-primary)`
- Color: Blanco
- Padding: `0.625rem 1.25rem`
- Border radius: `0.375rem`
- Hover: Elevación sutil, color más oscuro

**Secundario (Outline):**
- Border: `1px solid var(--color-primary)`
- Color: `var(--color-primary)`
- Background: Transparente
- Hover: Background primary, color blanco

**Tamaños:**
- Normal: `0.625rem 1.25rem`
- Small: `0.5rem 1rem`
- Large: `0.75rem 1.5rem`

### 8.2 Cards

- Background: Blanco
- Border: `1px solid var(--border-color)`
- Border radius: `0.5rem`
- Shadow: `var(--shadow-sm)`
- Hover: `var(--shadow-md)`

**Card Header:**
- Background: `var(--color-gray-50)`
- Border bottom: `1px solid var(--border-color)`
- Padding: `1rem 1.5rem`
- Font weight: 600

**Card Body:**
- Padding: `1.5rem`

### 8.3 Tablas

**Header:**
- Background: `var(--color-gray-50)`
- Border bottom: `2px solid var(--border-color)`
- Font weight: 600
- Text transform: uppercase
- Font size: `0.75rem`
- Letter spacing: `0.05em`
- Color: `var(--color-gray-700)`

**Celdas:**
- Padding: `1rem`
- Border bottom: `1px solid var(--border-color)`

**Hover:**
- Background: `var(--color-gray-50)`

### 8.4 Formularios

**Labels:**
- Font weight: 500
- Color: `var(--color-gray-700)`
- Font size: `0.875rem`
- Margin bottom: `0.5rem`

**Inputs:**
- Border: `1px solid var(--border-color)`
- Border radius: `0.375rem`
- Padding: `0.625rem 0.875rem`
- Font size: `0.9375rem`

**Focus:**
- Border color: `var(--color-primary)`
- Box shadow: `0 0 0 3px rgba(37, 99, 235, 0.1)`

### 8.5 Badges

- Font weight: 500
- Padding: `0.375rem 0.75rem`
- Border radius: `0.375rem`
- Font size: `0.75rem`

### 8.6 Alerts

- Border radius: `0.375rem`
- Border: Ninguno
- Padding: `1rem 1.25rem`
- Font size: `0.9375rem`

---

## 9. KPIs / Métricas

### 9.1 KPI Card

**Estructura:**
```
┌─────────────────────────────┐
│ Label (uppercase, small)    │
│                             │
│ Value (large, bold)         │
│                             │
│ Change/Meta (small)         │
│                             │
│ [Icon]                      │
└─────────────────────────────┘
```

**Estilos:**
- Background: Blanco
- Border: `1px solid var(--border-color)`
- Border left: `4px solid` (color de estado)
- Border radius: `0.5rem`
- Padding: `1.5rem`
- Hover: Elevación, transform subtle

**Label:**
- Font size: `0.875rem`
- Font weight: 500
- Text transform: uppercase
- Letter spacing: `0.05em`
- Color: Color de estado

**Value:**
- Font size: `2rem`
- Font weight: 700
- Color: `var(--color-gray-900)` o color de estado

**Icon:**
- Tamaño: `56px x 56px`
- Border radius: `12px`
- Background: Gradiente sutil con color de estado
- Color: Color de estado

---

## 10. Navegación

### 10.1 Sidebar Navigation

**Secciones:**
- Título: `0.75rem`, uppercase, letter-spacing, gris medio
- Items: `0.9375rem`, font-weight 500

**Links:**
- Padding: `0.625rem 1.25rem`
- Border left: `3px solid transparent`
- Transition: `all 0.2s ease`

**Active State:**
- Background: `rgba(37, 99, 235, 0.1)`
- Color: `var(--color-primary)`
- Border left: `3px solid var(--color-primary)`
- Font weight: 600

**Hover State:**
- Background: `var(--color-gray-50)`
- Color: `var(--color-primary)`
- Border left: `3px solid var(--color-primary)`

### 10.2 Top Header

**Company Selector:**
- Background: `var(--color-gray-50)`
- Border radius: `0.375rem`
- Padding: `0.5rem 1rem`
- Font weight: 500
- Font size: `0.875rem`

**User Menu:**
- Avatar: `36px x 36px`, gradiente primary
- Hover: Background `var(--color-gray-50)`

---

## 11. Responsive

### 11.1 Breakpoints (Bootstrap 5)

- **sm:** 576px
- **md:** 768px
- **lg:** 992px
- **xl:** 1200px
- **xxl:** 1400px

### 11.2 Mobile (< 768px)

- Sidebar: Oculto por defecto, slide-in
- Main content: Full width
- Padding: Reducido a `1rem`

---

## 12. Accesibilidad

### 12.1 Contraste

- Texto normal: Mínimo 4.5:1
- Texto grande: Mínimo 3:1
- Elementos interactivos: Mínimo 3:1

### 12.2 Tamaños Clickables

- Mínimo: `44px x 44px`
- Recomendado: `48px x 48px`

### 12.3 Focus States

- Visible y claro
- Color: `var(--color-primary)`
- Box shadow: `0 0 0 3px rgba(37, 99, 235, 0.1)`

---

## 13. Mejores Prácticas

### 13.1 Consistencia

- Usar siempre las variables CSS definidas
- Mantener espaciado consistente
- Usar tipografía según escala definida

### 13.2 Jerarquía Visual

- Títulos más grandes que subtítulos
- Énfasis con color, no solo tamaño
- Usar peso de fuente para jerarquía

### 13.3 Espaciado

- Más espacio, no menos
- Agrupar elementos relacionados
- Separar visualmente secciones distintas

### 13.4 Colores

- Usar colores de estado consistentemente
- No inventar nuevos colores sin justificación
- Mantener contraste suficiente

### 13.5 Animaciones

- Transiciones sutiles (0.2s ease)
- No exagerar
- Usar para feedback, no decoración

---

**Última actualización:** Enero 2026  
**Mantener este documento actualizado** cuando se agreguen nuevos componentes o se modifiquen estilos.

