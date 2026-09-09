# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Estudiantes, docentes y personas interesadas en consultar y aprender Kichwa Unificado desde español o desde Kichwa, principalmente en navegadores de escritorio y móvil.

## Product Purpose

El Diccionario Kichwa permite encontrar equivalencias bilingües, comprender significados, escuchar pronunciaciones y explorar el vocabulario por temas útiles para el aprendizaje. El éxito significa que una persona encuentre una palabra sin conocer de antemano el idioma de entrada y pueda confiar en que los filtros temáticos no mezclan conceptos sin relación.

## Positioning

Combina un corpus bilingüe de 4.509 entradas con búsqueda en ambas direcciones, audio y una clasificación temática explícitamente auditable en lugar de categorías asignadas al azar.

## Operating Context

La consulta principal ocurre en el buscador. El usuario puede escribir una palabra en español o Kichwa, limitar por tema y dificultad de pronunciación, revisar resultados paginados y abrir la ficha completa. El personal administrador puede corregir categorías y contenido desde Django Admin.

## Capabilities and Constraints

- Aplicación existente en Django con PostgreSQL en desarrollo y compatibilidad local con SQLite.
- El corpus tiene campos de Kichwa, traducción al español, definición, pronunciación y audio.
- La categoría y la dificultad automática deben conservar trazabilidad y permitir revisión humana.
- Las búsquedas deben tolerar mayúsculas y tildes editoriales sin perder caracteres propios del Kichwa.
- Los filtros deben combinarse entre sí y conservarse durante la paginación.
- No se deben publicar secretos, bases locales, respaldos ni archivos cargados por usuarios.

## Brand Commitments

El nombre visible es “Diccionario Kichwa”. La voz es educativa, directa y respetuosa con la lengua y la cosmovisión Kichwa. No se inventan validaciones lingüísticas ni se presenta una clasificación automática como revisión experta.

## Evidence on Hand

- Corpus real de 4.509 entradas disponible en la base configurada por el proyecto.
- Archivos de audio estáticos en `static/audios/`.
- Modelos, vistas y plantillas existentes en `apps/diccionario/` y `templates/diccionario/`.
- No existe todavía una validación lingüística humana completa de todas las categorías.

## Product Principles

- Buscar primero, comprender después: el idioma de entrada nunca debe ser una barrera.
- Clasificar con evidencia: una categoría automática debe explicar por qué fue elegida.
- No rellenar con ruido: una clasificación incierta se marca como tal, no se disfraza de certeza.
- Mantener el aprendizaje legible: un solo filtro expresa la dificultad de pronunciación.
- Proteger el corpus: cada cambio relevante queda versionado y es reversible mediante Git.

## Accessibility & Inclusion

La interfaz debe funcionar con teclado, mostrar foco visible, usar etiquetas explícitas, mantener contraste legible y respetar `prefers-reduced-motion`.
