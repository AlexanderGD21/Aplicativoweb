# Revisión editorial de ejemplos de uso

Al iniciar esta fase, las 4.509 entradas tenían en `ejemplo_uso` la equivalencia
automática «palabra - traducción». No eran oraciones. La migración 0025 elimina
únicamente esos marcadores; cualquier texto heredado distinto queda conservado
para revisión, pero no se publica directamente.

Los ejemplos nuevos se gestionan en **Django Admin → Ejemplos de uso**. Cada
borrador requiere una oración en Kichwa, su traducción completa al español y una
fuente identificable (obra, informante autorizado o autoría propia). El personal
editorial debe comprobar con una persona competente la variedad lingüística,
ortografía, sentido en contexto y permiso de publicación de la fuente. El estado
de revisión de la entrada del diccionario es independiente del ejemplo.

Después de esa comprobación, la acción **Publicar tras revisión editorial**
registra al responsable y la fecha. Solo entonces aparece el ejemplo bilingüe y
su fuente en el detalle público. La acción **Retirar publicación** lo oculta.
Editar la oración, traducción, fuente o entrada asociada lo devuelve a borrador y
exige una nueva revisión.

No se generaron oraciones artificiales ni se declararon revisados contenidos que
no hayan pasado por este flujo. El siguiente trabajo editorial consiste en
incorporar oraciones auténticas, empezando por vocabulario prioritario.
