---
name: Diccionario Kichwa
description: Una mesa de consulta bilingüe viva, compacta y confiable.
colors:
  bosque-accion: "#17684d"
  bosque-profundo: "#0f533c"
  azul-noche: "#151f38"
  ocre-kichwa: "#c48a18"
  tinta: "#142923"
  tinta-suave: "#52645f"
  papel-frio: "#fcfdfa"
  suelo-frio: "#eef2ef"
  linea: "#d9ded8"
  blanco: "#ffffff"
typography:
  display:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "clamp(3rem, 7vw, 6rem)"
    fontWeight: 790
    lineHeight: 0.94
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "clamp(2.5rem, 5.2vw, 5.25rem)"
    fontWeight: 780
    lineHeight: 0.98
    letterSpacing: "-0.04em"
  title:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "clamp(1.7rem, 3vw, 2.5rem)"
    fontWeight: 780
    letterSpacing: "-0.03em"
  body:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "0.72rem"
    fontWeight: 780
    letterSpacing: "0.04em"
rounded:
  control: "10px"
  card: "14px"
  feature: "16px"
  pill: "999px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2rem"
  2xl: "3rem"
components:
  button-primary:
    backgroundColor: "{colors.bosque-accion}"
    textColor: "{colors.blanco}"
    rounded: "{rounded.control}"
    padding: "0.65rem 0.9rem"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.bosque-profundo}"
    textColor: "{colors.blanco}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.blanco}"
    rounded: "{rounded.control}"
    padding: "0.65rem 0.9rem"
    height: "44px"
  search-field:
    backgroundColor: "{colors.blanco}"
    textColor: "{colors.tinta}"
    rounded: "13px"
    padding: "0.75rem 0.5rem"
    height: "54px"
  filter-field:
    backgroundColor: "{colors.blanco}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.control}"
    padding: "0.65rem 2.2rem 0.65rem 0.8rem"
    height: "46px"
  category-chip:
    textColor: "{colors.tinta}"
    rounded: "{rounded.pill}"
    padding: "0.45rem 0.68rem"
  result-card:
    backgroundColor: "{colors.papel-frio}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.card}"
    padding: "1.3rem"
  detail-panel:
    backgroundColor: "{colors.papel-frio}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.feature}"
    padding: "clamp(1.5rem, 4vw, 2.6rem)"
---

# Design System: Diccionario Kichwa

## Overview

**Creative North Star: "Mesa de consulta viva"**

La interfaz se comporta como una mesa de consulta lingüística: ofrece amplitud para comparar vocabulario, calma para leer una entrada y señales suficientes para entender de dónde viene cada relación. La identidad nace del azul noche, el verde bosque, el ocre y los papeles fríos; el contenido bilingüe, no la decoración, lleva el peso expresivo.

Inicio, resultados, detalle y recorridos de confianza comparten una densidad deliberada y una jerarquía compacta. El Inicio puede desplegar un campo de palabras Kichwa ambientales; autenticación limita ese recurso a un solo lexema fantasma dentro de su panel de orientación. Las categorías tiñen fichas y etiquetas con baja intensidad; el detalle y los documentos legales priorizan lectura continua sin contenedores vacíos.

**Key Characteristics:**

- Azul noche estructural, verde bosque operativo y ocre Kichwa dosificado.
- Superficies de papel frío con tintes semánticos de categoría y dificultad.
- Comparación compacta en resultados y lectura serena en detalle.
- Acceso y registro reúnen orientación y tarea en un solo marco; los documentos legales separan índice y lectura sin perder continuidad.
- Movimiento de continuidad breve, cancelable y limitado a transformación y opacidad.
- Relaciones acompañadas por una razón visible; nunca se rellenan al azar.

## Colors

La paleta combina una base fría y sobria con dos acentos funcionales; los colores de categoría entran sólo como tintes suaves o marcadores pequeños.

### Primary

- **Bosque de acción** (`#17684d`): acciones principales, enlaces operativos, foco contextual y selección.
- **Bosque profundo** (`#0f533c`): estado hover de las acciones verdes.

### Secondary

- **Azul noche** (`#151f38`): mastheads y campos de apertura que enmarcan el vocabulario.
- **Ocre Kichwa** (`#c48a18`): remates de identidad, iconos y acentos breves sobre azul noche.

### Neutral

- **Tinta** (`#142923`): texto principal y títulos sobre superficies claras.
- **Tinta suave** (`#52645f`): metadatos, ayuda y contenido secundario.
- **Papel frío** (`#fcfdfa`): superficies de lectura y consulta.
- **Suelo frío** (`#eef2ef`): fondo general que separa las superficies.
- **Línea** (`#d9ded8`): divisores y bordes estructurales.
- **Blanco** (`#ffffff`): texto sobre fondos oscuros y controles de máxima claridad.

### Named Rules

**The Semantic Tint Rule.** El color de categoría aparece como mezcla suave, etiqueta o marcador; nunca como bloque decorativo dominante.

**The Ocher Measure Rule.** El ocre señala identidad y orientación, pero no compite con el verde reservado para actuar.

## Typography

**Display Font:** Inter (with system sans-serif fallbacks)

**Body Font:** Inter (with system sans-serif fallbacks)

**Character:** Una sola familia sostiene toda la experiencia. Los títulos son compactos, pesados y de espaciado cerrado; el cuerpo mantiene una cadencia abierta para definiciones y notas.

### Hierarchy

- **Display** (790, `clamp(3rem, 7vw, 6rem)`, 0.94): la palabra Kichwa protagonista en el detalle.
- **Headline** (780, `clamp(2.5rem, 5.2vw, 5.25rem)`, 0.98): la invitación principal del Inicio.
- **Title** (780, `clamp(1.7rem, 3vw, 2.5rem)`): títulos de secciones y grupos.
- **Body** (400, `1rem`, 1.6): lectura general; definiciones y notas se limitan aproximadamente a 68–72 caracteres.
- **Label** (780, `0.72rem`, `0.04em`, uppercase cuando nombra un idioma): metadatos compactos y contexto de traducción.

### Named Rules

**The Word Leads Rule.** En una ficha, la palabra Kichwa y su equivalencia preceden a los metadatos y acciones.

## Layout

La retícula usa contenedores Bootstrap como marco y CSS propio para la composición. Inicio abre en dos columnas con una demostración de búsqueda y una entrada; resultados forman una cuadrícula compacta de dos columnas que pasa a una a 760px; el detalle combina lectura (`1.55fr`) y rail (`0.55fr`) hasta 900px, cuando ambos se apilan. Acceso y registro dividen orientación y tarea hasta 860px; los documentos legales combinan un índice de 250px y lectura flexible hasta 840px. El Inicio completa su apilado móvil a 680px, autenticación y detalle a 620px, y la lectura legal se aplana a 560px.

Los objetivos interactivos mantienen un mínimo de 44px. La separación crece de controles compactos a secciones amplias usando la escala de `0.25rem` a `3rem`; los bloques de lectura evitan anchos fijos y las definiciones se mantienen entre 68 y 72 caracteres por línea.

**The Context Density Rule.** Resultados compara en unidades compactas; detalle reduce la densidad y reserva ancho continuo para significado y notas.

**The Trust Surface Rule.** Autenticación reúne contexto y formulario dentro de un solo marco; los documentos legales mantienen el índice fuera de la única hoja elevada para que la lectura conserve prioridad.

## Elevation & Depth

El sistema es plano por defecto y separa planos mediante tono, borde y tinte. Cada vista admite una sola superficie elevada en reposo: la demostración de búsqueda en Inicio, el banco de búsqueda en resultados, el marco indivisible de autenticación o la hoja de lectura legal. Menús, índices, foco y transiciones son estados temporales o superficies planas, no una segunda capa permanente.

### Shadow Vocabulary

- **Banco de búsqueda** (`box-shadow: 0 18px 42px rgba(13, 32, 27, 0.14)`): única elevación en reposo de la vista de resultados.
- **Búsqueda de Inicio** (`box-shadow: 0 18px 42px rgba(3, 15, 12, 0.24)`): única elevación en reposo sobre el hero azul noche.
- **Marco de acceso** (`box-shadow: 0 22px 54px rgba(13, 32, 27, 0.16)`): une orientación y tarea como una sola puerta de entrada.
- **Hoja legal** (`box-shadow: 0 18px 42px rgba(13, 32, 27, 0.12)`): eleva únicamente el documento; el índice permanece plano.

### Named Rules

**The One Resting Elevation Rule.** Cada vista usa como máximo una elevación persistente; el resto de la jerarquía se resuelve con papel, línea y tinte.

## Shapes

Los controles usan esquinas contenidas (`10px`), las fichas y rails usan curvas suaves (`14px`) y las superficies protagonistas alcanzan `16px`. Etiquetas de categoría, dificultad y razón usan forma de píldora (`999px`). Los bordes son finos y estructurales; una superficie no combina borde y sombra salvo el banco de búsqueda aprobado.

## Components

### Buttons

- **Shape:** rectángulo compacto y accesible (`10px`, mínimo `44px`).
- **Primary:** blanco sobre verde bosque, con padding compacto (`0.65rem 0.9rem`).
- **Hover / Focus:** el hover profundiza el verde entre 150 y 160ms; el foco visible usa un contorno ocre de 3px con offset de 3px.
- **Ghost:** fondo transparente, borde fino y texto blanco dentro del masthead.

### Chips

- **Style:** píldora de baja intensidad (`999px`) con mezcla del color semántico sobre blanco.
- **State:** categoría, dificultad y razón relacional conservan su función textual; el color nunca sustituye la etiqueta.

### Cards / Containers

- **Corner Style:** fichas compactas (`14px`) y paneles protagonistas (`16px`).
- **Background:** papel frío o mezcla de 5% del color de categoría con papel frío.
- **Shadow Strategy:** planas, salvo la única elevación definida para cada vista.
- **Border:** mezcla de 20% del color semántico con la línea base cuando la categoría aporta contexto.
- **Internal Padding:** `1.3rem` en fichas compactas y `clamp(1.5rem, 4vw, 2.6rem)` en el significado.

### Inputs / Fields

- **Style:** fondo blanco, trazo gris verdoso, radio de 10–13px y altura de 46–54px.
- **Focus:** borde verde y halo de 3px con verde al 15%; el foco global conserva el contorno ocre.
- **Error / Disabled:** los errores usan texto rojo oscuro; las acciones deshabilitadas pierden contraste y no se desplazan.

### Navigation

Enlaces de avance y retorno usan verde bosque, peso alto y objetivos de 44px. El índice legal mantiene el mismo mínimo, usa fondo verde pálido para el apartado activo y comunica la ubicación con `aria-current`. View Transitions aporta continuidad entre páginas cuando está disponible; la llegada alternativa dura 240ms y `prefers-reduced-motion` reduce animaciones y transiciones a 0.01ms.

### Ambient Lexeme Accent

El Inicio puede usar un campo de palabras Kichwa translúcidas sobre azul noche, con opacidad de `0.035–0.085` y duraciones de `17–23s`. Las pantallas de autenticación admiten un solo lexema grande, tenue y recortado dentro del panel azul, con deriva de 18s. Ambos se detienen por completo con movimiento reducido.

### Trust Access Frame

Acceso, registro, recuperación y estados de cuenta comparten un marco de papel frío dividido entre orientación azul noche y tarea. Los formularios usan campos de 48px, botones de al menos 46px, errores próximos al control y agrupaciones compactas; en móvil el marco pierde radio y sombra para convertirse en una sola lectura vertical.

### Legal Reading Surface

Términos y Privacidad abren con un masthead azul noche y continúan en una retícula de índice más documento. El índice es plano y adhesivo sólo cuando hay espacio; la hoja de papel frío concentra la única elevación, limita la prosa a 72 caracteres y usa divisores, resúmenes verdes y llamados ocres para estructurar sin ornamentar.

### Entry Reading + Rail

El detalle abre con un masthead compacto y distribuye definición y notas a la izquierda, datos y acciones en un rail adhesivo a la derecha. Las relaciones usan fichas teñidas y siempre muestran una razón visible antes de la palabra relacionada.

## Do's and Don'ts

### Do:

- **Do** usar el azul noche para abrir la consulta y el verde bosque para actuar.
- **Do** tintar fichas de resultado y relación con el color real de su categoría a baja intensidad.
- **Do** mantener resultados en dos columnas compactas y pasarlos a una a 760px.
- **Do** mostrar una razón visible para cada palabra relacionada.
- **Do** reunir orientación y tarea en una sola superficie elevada en los recorridos de cuenta, y dejar plano el índice de los documentos legales.
- **Do** respetar View Transitions y `prefers-reduced-motion` como un mismo contrato de continuidad.

### Don't:

- **Don't** extender el campo de palabras Kichwa fuera del Inicio ni usar más de un lexema fantasma en la orientación de autenticación.
- **Don't** mantener más de una elevación persistente por vista.
- **Don't** convertir colores de categoría en fondos saturados o bloques decorativos dominantes.
- **Don't** presentar relaciones sin explicación ni rellenar espacios con coincidencias al azar.
- **Don't** mostrar contenedores vacíos cuando una definición, nota o relación no existe.
