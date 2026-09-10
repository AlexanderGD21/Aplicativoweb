THESIS
Inicio, resultados y detalle forman una misma mesa de consulta. Inicio invita a buscar con ejemplos reales; resultados permite comparar entradas de un vistazo; detalle concentra significado, pronunciación, contexto y relaciones sin contenedores vacíos.

OWN-WORLD
- Se mantiene “Mesa de consulta viva”: azul noche, verde bosque, ocre y papeles fríos.
- Los colores suaves provienen de tintes semánticos de categoría y dificultad, nunca de gradientes dominantes.
- Las palabras son el material visual: términos Kichwa translúcidos se desplazan lentamente en el fondo de Inicio.
- Bootstrap conserva la retícula y los componentes funcionales; CSS propio define identidad y movimiento.

STORY
1. Inicio demuestra la búsqueda bilingüe dentro del primer viewport y ofrece temas reales del corpus.
2. Los resultados ocupan el ancho con unidades compactas de dos columnas en escritorio y una en móvil.
3. Ver entrada presenta la equivalencia primero y distribuye contenido sólo cuando existe.
4. La ficha muestra definición y notas a la izquierda; metadatos y acciones quedan en un rail compacto.
5. Las relaciones explican por qué cada sugerencia está conectada y nunca rellenan espacios al azar.

FIRST VIEWPORT
En escritorio, Inicio abre con una demostración de consulta sobre azul noche y deja visibles estadísticas/temas. El detalle usa una cabecera compacta y permite comenzar a leer la definición antes de un desplazamiento largo. En móvil, búsqueda, contenido y acciones se apilan sin anchos fijos ni controles menores de 44 px.

MOTION
- Focal: palabras Kichwa ambientales cruzan suavemente el fondo de Inicio como vocabulario en circulación.
- Continuidad: navegación entre páginas usa View Transitions cuando el navegador lo admite y una llegada corta sin ocultar contenido.
- Feedback: botones y enlaces responden entre 120 y 180 ms.
- Presupuesto: sólo transform y opacidad; las animaciones ambientales se detienen con `prefers-reduced-motion`.

FINISH
Debe sentirse como una herramienta lingüística específica y cuidada: densa donde se compara vocabulario, tranquila donde se lee y honesta cuando no existe una relación demostrable.
