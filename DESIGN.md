---
name: Diccionario Kichwa
description: Una mesa de consulta bilingüe clara, sobria y accesible.
colors:
  ink: "#142923"
  muted: "#52645f"
  paper: "#fcfdfa"
  ground: "#eef2ef"
  navy: "#151f38"
  green: "#17684d"
  green-deep: "#0f533c"
  gold: "#c48a18"
  line: "#d9ded8"
typography:
  display:
    fontFamily: "Inter, sans-serif"
    fontSize: "clamp(2rem, 4vw, 3.7rem)"
    fontWeight: 760
    lineHeight: 1.04
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "Inter, sans-serif"
    fontSize: "clamp(1.45rem, 2.5vw, 2rem)"
    fontWeight: 760
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Inter, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 750
rounded:
  control: "10px"
  field: "13px"
  surface: "16px"
  pill: "999px"
spacing:
  xs: "0.45rem"
  sm: "0.85rem"
  md: "1.25rem"
  lg: "2.25rem"
  xl: "4.5rem"
components:
  button-primary:
    backgroundColor: "{colors.green}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
    height: "44px"
  input-search:
    backgroundColor: "#ffffff"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    height: "54px"
  result-surface:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "14px"
---

# Design System: Diccionario Kichwa

## Overview

**Creative North Star: "Mesa de consulta viva"**

El sistema visual convierte el diccionario en un espacio de consulta lingüística: sobrio, ordenado y suficientemente cálido para el aprendizaje cotidiano. La interfaz da prioridad a las palabras, sus equivalencias y los filtros; la ornamentación queda subordinada a esa tarea.

El azul noche conecta con la identidad existente, el verde indica acciones y el ocre aporta un acento Kichwa controlado. Las superficies claras son frías y silenciosas para que las categorías conserven su función semántica.

**Key Characteristics:**

- Jerarquía compacta y legible.
- Una acción primaria verde por contexto.
- Categorías expresadas con pequeños marcadores de color.
- Controles táctiles y foco visible.

## Colors

La paleta combina azul noche, verde bosque y ocre sobre papeles fríos; los colores de categoría solo aparecen en etiquetas o marcadores.

**The Semantic Accent Rule.** El verde activa; el ocre orienta; el color de categoría identifica, pero ninguno debe competir con el contenido léxico.

## Typography

**Display Font:** Inter (sans-serif)
**Body Font:** Inter (sans-serif)

**Character:** Una sola familia de trabajo, con títulos densos y texto sereno. El peso y la escala crean la jerarquía sin efectos tipográficos decorativos.

### Hierarchy

- **Display:** peso 760 y escala fluida; reservado para el título principal.
- **Headline:** peso 760 y tracking compacto; abre resultados y grupos.
- **Title:** entre 1.05rem y 1.22rem; nombra paneles, entradas y categorías.
- **Body:** 1rem con línea 1.65 y medida máxima cercana a 70 caracteres.
- **Label:** 0.8rem y peso 750; identifica filtros y metadatos.

**The One Typeface Rule.** La claridad bilingüe depende de una voz estable; se varían peso y tamaño, no la familia.

## Layout

El contenido vive en el contenedor Bootstrap del proyecto. El buscador usa dos columnas equilibradas y se convierte en una sola columna bajo 900px; filtros y resultados se apilan bajo 680px. Los objetivos interactivos tienen al menos 44px y las listas conservan densidad de consulta, no densidad de tarjetas promocionales.

## Elevation & Depth

La profundidad es excepcional. Solo la mesa principal usa una sombra ambiental suave (`0 18px 42px rgba(13, 32, 27, 0.14)`); listas y estados vacíos se separan mediante borde fino.

**The One Lift Rule.** Una vista puede elevar su espacio de trabajo principal; el resto de superficies permanece plano.

## Shapes

Los controles usan curvas de 10–13px y las superficies principales 14–16px. Las píldoras se reservan para dificultad, filtros activos y categorías. Los marcadores de tema son círculos pequeños, nunca franjas decorativas.

## Components

### Buttons

- **Shape:** control suavemente redondeado (10px), altura mínima de 44px.
- **Primary:** verde bosque con texto blanco y peso 750.
- **Hover / Focus:** verde profundo y desplazamiento vertical mínimo; foco ocre de 3px.

### Chips

- **Style:** fondo tintado a partir del color semántico, texto oscuro y forma de píldora.
- **State:** identifica un filtro o dato; no reemplaza una acción.

### Cards / Containers

- **Corner Style:** 14–16px.
- **Background:** papel frío.
- **Shadow Strategy:** solo la mesa de búsqueda; listas con borde fino.
- **Internal Padding:** entre 1.2rem y 1.65rem.

### Inputs / Fields

- **Style:** fondo blanco, borde gris verdoso y radio de 10–13px.
- **Focus:** borde verde y halo verde translúcido.
- **Error / Disabled:** error rojo textual; estado deshabilitado gris verdoso y sin movimiento.

### Navigation

La navegación global conserva azul noche, marca ocre y enlaces blancos. En móvil se repliega con el componente Bootstrap existente.

### Bilingual Result Row

La palabra Kichwa encabeza; la equivalencia española lleva una etiqueta textual; pronunciación, dificultad, tema y acceso al detalle completan la fila sin crear tarjetas anidadas.

## Do's and Don'ts

### Do:

- **Do** mantener Kichwa y español visibles en la misma unidad de lectura.
- **Do** mostrar conteos y filtros activos con numerales tabulares.
- **Do** usar el color de categoría solo en marcadores y etiquetas pequeñas.
- **Do** preservar navegación por teclado, foco visible y estados de carga o vacío.

### Don't:

- **Don't** duplicar filtros equivalentes de dificultad o pronunciación.
- **Don't** convertir cada contenido en una tarjeta flotante.
- **Don't** usar gradientes dominantes, texto degradado ni halos decorativos.
- **Don't** presentar una clasificación automática como validación lingüística humana.
