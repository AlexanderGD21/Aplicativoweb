# Secuencia de aprendizaje

Orden acordado para continuar el Diccionario Kichwa. El estado describe el código
actual; no implica que el contenido lingüístico haya recibido revisión humana.

1. **Juegos y progreso por palabra — completada.** Seis modalidades, selección de
   vocabulario por tema y dificultad, respuestas validadas por el servidor y
   progreso individual por palabra.
2. **Puntos, niveles, misiones y perfil de aprendizaje — completada.** Diez puntos
   por el primer acierto en cada palabra; nivel de práctica cada 100 puntos;
   cuatro misiones calculadas desde aciertos, partidas y rachas; perfil privado
   con métricas, objetivos e historial. El nivel de práctica no sustituye el
   nivel de Kichwa que declara la persona. Las misiones no dan puntos extra.
3. **Inicio con reto semanal, tendencias y ranking opcional — completada.** El
   reto rota entre las cinco modalidades cada lunes y cuenta cinco palabras
   distintas acertadas durante la semana para la persona autenticada. Las
   tendencias agregadas muestran los últimos siete días y el ranking requiere
   participación voluntaria.
4. **Sonidos interactivos y juego de escucha — completada.** Los juegos tienen
   efectos de respuesta que se pueden silenciar. La modalidad de escucha usa
   grabaciones del corpus, ofrece reproducción lenta y texto alternativo, y
   guarda el progreso por palabra sin generar pronunciaciones artificiales.
5. **Oraciones de ejemplo revisadas — completada en alcance documental.** Se retiraron de la vista pública
   las equivalencias automáticas que se mostraban como ejemplos. Django Admin
   permite preparar oraciones bilingües con fuente, aprobarlas con responsable y
   fecha, y devolverlas a borrador si cambian. Se cotejaron y publicaron 29
   oraciones de 11 lemas del módulo autorizado, con página, sección y alcance de
   revisión visibles; 20 amplían las tablas de conjugación. El cotejo documental
   no se presenta como validación lingüística independiente.
6. **Imágenes para vocabulario prioritario — completada y ampliable por lotes.** Once acepciones
   concretas tienen ilustraciones originales, infantiles y educativas en formato
   WebP, con texto alternativo y crédito. Se muestran en resultados, temas y
   detalle; no se reutilizan imágenes de terceros incluidas en el PDF. PostgreSQL
   contiene además la clasificación visual de las 4.454 acepciones y una cola con
   estados de generación, revisión y publicación. El lote inicial de expansión
   reúne 100 acepciones concretas sin publicarlas automáticamente. La integración
   opcional con Pexels busca y descarga fotografías candidatas, registra autoría
   y enlaces de origen y mantiene la aprobación humana antes de mostrarlas.
7. **Internacionalización de la interfaz y traducciones al inglés — pendiente.**
   Traducir la interfaz y revisar el contenido en inglés antes de habilitarlo.

La aplicación usa Python, Django y PostgreSQL. La actividad y las estadísticas
personales pertenecen al titular de la cuenta; el personal administrador con
permiso de lectura puede consultarlas en Django Admin. No hay acceso de tutores.
