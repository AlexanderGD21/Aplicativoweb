---
version: 1
slug: "templates-usuarios-login-html"
primary_target: "templates/usuarios/login.html"
related_targets: ["templates/usuarios/registro.html","templates/usuarios/password_reset.html","templates/usuarios/password_reset_done.html","templates/usuarios/password_reset_confirm.html","templates/usuarios/password_reset_complete.html","templates/usuarios/terminos.html","templates/usuarios/privacidad.html","static/css/auth.css","static/js/auth.js"]
---

THESIS
Acceder, crear una cuenta y comprender el uso de los datos forman un solo recorrido de confianza. Cada pantalla debe explicar qué se solicita, para qué sirve y cuál es el siguiente paso, sin promesas técnicas o legales que la aplicación no pueda demostrar.

OWN-WORLD
- Extiende “Mesa de consulta viva”: azul noche para orientar, verde bosque para actuar, ocre en detalles identitarios y papel frío para leer.
- La palabra y el aprendizaje siguen siendo protagonistas; la seguridad se comunica con lenguaje claro y estados verificables, no con iconografía alarmista.
- Bootstrap mantiene la base funcional y CSS propio construye una composición compacta, accesible y coherente con Inicio, Buscar y Ver entrada.

STORY
1. Acceso presenta el formulario como tarea principal y explica en un panel lateral qué conserva una cuenta: favoritos y progreso.
2. Registro organiza los campos en grupos breves, distingue lo obligatorio de lo opcional y separa la aceptación contractual de las comunicaciones voluntarias.
3. Recuperación conserva mensajes neutrales para no revelar si un correo está registrado.
4. Términos y Privacidad comparten un índice legible, navegación persistente y contenido fiel a las funciones actuales.
5. Los enlaces entre acceso, registro, recuperación y documentos legales preservan contexto y siempre ofrecen retorno claro.

FIRST VIEWPORT
En escritorio, acceso y registro usan una sola superficie elevada dividida entre orientación y tarea. El formulario de acceso cabe completo en el primer viewport; el registro reduce altura con una retícula de dos columnas. En móvil, la orientación se condensa y los campos pasan a una columna sin controles menores de 44 px ni desplazamiento horizontal.

MOTION
- Focal: una única línea de palabras Kichwa cambia suavemente de posición en el panel de orientación.
- Continuidad: se heredan View Transitions y la llegada breve del sistema global.
- Feedback: foco, validación y estado de envío responden entre 120 y 180 ms.
- `prefers-reduced-motion` elimina desplazamientos y mantiene los estados visibles.

FINISH
Debe sentirse como una puerta segura y serena hacia el aprendizaje: compacta, honesta, fácil de completar con teclado y consistente en cada estado de autenticación y lectura legal.
