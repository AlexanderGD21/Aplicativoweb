---
version: 1
slug: "templates-diccionario-juegos-html"
primary_target: "templates/diccionario/juegos.html"
related_targets: ["templates/diccionario/juegos/base_juego.html","static/css/games-learning.css","static/js/games-learning.js"]
---

THESIS
Los juegos forman una ruta de práctica, no una colección de minijuegos aislados. La persona elige tema y dificultad, entiende qué habilidad ejercita y recibe una siguiente acción clara después de cada respuesta.

OWN-WORLD
- Hereda la mesa de consulta viva: azul noche para orientar, verde bosque para actuar, ocre medido para el vocabulario Kichwa y papel frío para jugar.
- Las categorías tiñen sólo etiquetas y pequeños indicadores.
- Cada modalidad usa un tinte suave propio para facilitar reconocimiento sin convertir el color en la única señal.
- Un único panel de juego elevado concentra pregunta, respuesta y avance; el resto permanece plano.
- Font Awesome aporta iconos consistentes; no se usan emojis ni ilustraciones genéricas.

STORY
1. La portada explica la ruta Reconocer, Asociar, Recordar, Producir y Explorar.
2. Tema y dificultad permanecen visibles y nunca se sustituyen por una muestra aleatoria de otro filtro.
3. Cada juego muestra avance, aciertos, racha y tiempo con etiquetas compactas.
4. La respuesta comunica acierto o recuperación y permite continuar sin perder contexto.
5. Una cuenta iniciada conserva progreso por palabra; una persona anónima puede practicar sin bloqueo.
6. Acierto, error y final de partida tienen respuesta visual y sonora opcional.
7. Una salida accidental se detiene con una franja superior que permite continuar o abandonar la partida.

FIRST VIEWPORT
En escritorio, la ruta y el selector ocupan una franja compacta y dejan ver las cinco modalidades como tarjetas diferenciadas. Dentro de una partida, el tablero es protagonista y los datos forman un rail breve. En móvil, filtros, tablero y acciones se apilan; el arrastre de la sopa es opcional porque se conserva la selección por dos toques y teclado, y los objetivos táctiles miden al menos 44 px.

FORM
Extensión code-led del sistema existente, confirmada por el usuario como continuación directa de la ruta acordada. No aplica concept roll ni seed porque no se crea ni reemplaza el mundo visual. La interacción distintiva es el cambio de estado del mismo panel de papel: pregunta, validación y siguiente paso ocurren sin modales ni saltos decorativos.

MOTION
- La tarjeta señala su modalidad mediante color, marcador y una línea inferior que responde al foco o hover.
- Aciertos revelan el mensaje de izquierda a derecha; errores hacen un desplazamiento breve; parejas y palabras encontradas fijan visualmente su estado.
- Los tonos se sintetizan con Web Audio después de una acción de la persona y pueden silenciarse con una preferencia persistente.
- `prefers-reduced-motion` conserva los cambios de estado y reduce el desplazamiento a una duración imperceptible.

DECISION
Confirmación textual del usuario, 2026-09-11: “claro entonces vayamos por ese orden, te doy los permisos para que hagas los cambios de los juegos con las palabras”. Esta aprobación cierra la dirección ya conversada y autoriza su ejecución directa; no abre una ronda de conceptos nueva.

Ampliación textual del usuario, 2026-09-11: solicita confirmación al salir a mitad de una partida, animaciones, sonidos de acierto y error, arrastre en la sopa, tooltips, tarjetas diferenciadas por color y mejores etiquetas. Esta ampliación mantiene el mismo mundo visual y suma respuesta y orientación interactiva.

FINISH
This should feel authored, coherent, and clearly derived from the approved brief—not like a generic template, not like a component-library assembly, and not like the cheapest acceptable version of the idea.
