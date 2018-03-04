# ICGC

ICGC plugin for PSI measurements.

TODO:
-	Implementar el ST_Convex_hull para la geometría de todos los puntos.
- Problema con \\ y simbolos raros (editar a mano el nombre cuando se modifique).
- La base de datos tiene problemas.

v1.5beta.2 (4/3/2018)
- Añadida carpeta de tests para realizar pruebas
- Acabada la nueva implementacion de carga de datos y borrado. El peso del trabajo ahora lo lleva psql y no pyhton. Añadido ademas buscador de puntos duplicados.

v1.5beta.1 (1/03/2018)
Cambios menores
- Añadidos print y cronometros para ver donde gasta mas tiempo.

v1.5beta (28/02/2018)

Cambios mayores:
- Proceso de carga de los datos. Se crea una tabla temporal en la base de datos que almacena todos los datos del archivo csv. Desde ahi se reparten a las diferentes tablas. Al final del proceso, esta tabla temporal se borra. Se sigue este procedimiento por temas de velocidad y eficiencia.

Cambios menores:
- Arreglado un problema de formato con comillas al editar strings compuestos por dos palabras.
- Documentacion del formulario del "conjunt de dades" pasado a opcional. (Acepta volor null).
- Voids repetidos (creo que arreglado)



v1.4beta.4 (14/02/2018)

- Solucionado el problema con la carga del archivo csv para dibujarlo.
- Añadida opcion para editar los registros del conjunto de datos (geoset registro).

v1.4beta.3.1 (7/02/2018)

Cambios menores:
-	Cambiado nombre de la primera pestaña a “carregar nova informacio” .
- Borrado comillas que aparecen en el campo link de la documentacion
- Añadido beginlife_void en el formulario (tabla geocol)
- Cambiado metadades de geoset a combobox con las citaciones.


v1.4beta.3 (4/02/2018)

Eliminado boton informacio de la observacion. Con el nuevo esquema de solo un geoset, no tiene mucho sentido


v1.4beta.2 (3/02/2018)

Nuevas funcionalidades:
-	Añadida opcion de editar los registros de la tabla campaña, documentcitation y geologiccollection. Nuevo boton editar que carga la info del elemento seleccionado y puedes alterar el registro en la base de datos.
-	La carga de datos se ha separado en dos partes:

1 La primera parte implica rellenar la tabla geophobjectset.

2 La segunda parte, si ya existe un registro en geophobjectset, puedes directamente cargar los datos ahí seleccionándolo de la campaña adecuada. Se activa con los checkboxes de la tabla II. Asi se pueden añadir nuevos datos a un geoset ya existente.


Cambios mayores
-	Cuando introduces un nuevo registro de estos tres (campaña, documentcitation o geocollection) no puedes repetir el nombre de un registro ya existente.
-	InspireId del processat automatico de la forma “es.icgc.ge.psi_nombre”
-	Cambiado formato en la lectura de la fecha del processado.
-	La tabla geophobjectset se carga una sola vez por campaña..
-	Distributioninfo (codi informe metadates) pasa a ser un text que has de rellenar (tabla geophobjectset). Con opcion de ser vacio.
-	Añadido largework_void (geophobjectset)  en el formulario.
-	Modificada la carga de datos, busca los LOS existentes en la base de datos y los LOS que vas a cargar. De esta forma, si el archivo que cargas no es LOS y no existe un LOS asociado a su zona (no existe en la bd o no lo cargas) da error.


Cambios menores
-	Cambiado nombre de la primera pestaña a “carregar nova informacio” .
-	Cambios en los iconos de los mensajes, diferenciando entre error e información.
-	Correccion de listados con registros duplicados
-	Modificaciones a la apariencia de las graficas (leyenda fuera de la grafica, rango de la grafica corregido)
- Cambiados los botones aceptar/cancelar que se crearon por defecto en el plugin por un salir.


v1.4beta.1 (25/01/2018)

- Añadido otra vez la id a la query. Pero con la key apropiada.

- En los desplegables se eliminan los repetidos

v1.4beta (24/01/2018)

- Cambios realizados en la forma en la que se llama la query. Los argumentos antes eran posicionales y ademas pasabamos la id de la tabla. Ahora, la id de la tabla no se pasa y los argumentos van con su key value asociada para cada tabla.

- Cambios en la forma en la que se visualizan los desplegables void.

- Añadida nueva entrada en la GUI para el campo reference_void
