# ICGC

ICGC plugin for PSI measurements.

TODO:
- Implementar el ST_Convex_hull para la geometría de todos los puntos.
- Problema con \\ y simbolos raros (editar a mano el nombre cuando se modifique).
- Lento al borrar.

(30/5/2018)
- Cambios en las fechas de asociadas a los nombres para las condiciones si los datos ya existen o no

(1/5/2018)
- Cambiadas las fechas de inicio y final a la primera y ultima columna de los datos (no lo que pone en el nombre del archivo)
- Correcciones en la GUI (acentos)

(19/3/2018)
- Cambiada la query que busca las ids en geophobject con los datos de temporal. Habia un problema si utmx,utmy estaba repetido.
Cambiado IN a INNER JOIN.

(13/3/2018)
- Cambiada la forma de carga de los procesados. Cambiada la relacion entre las tablas processes y geoset
- Cambiada la gui en la pestaña 2. Una vez se ha creado una geoset, podemos asignarle (cargar csv) de processados usando el boton que se activa si queremos cargar cosas parciales.
- Solventados los problemas en la funcion delete_campaign con el nuevo esquema de los procesados.


(12/3/2018)
- Corregido un bug con el geosetid. Ahora deberia funcionar bien para los dos casos (carga total y parcial).
- Modificado la pestaña III añadido con geoset, para mostrar las medidas por campaña y geoset. 
- Mejoradas las querys para el borrado de observaciones.

(12/3/2018)

- Corregido bug en la obtencion de la idgeoset si no existe. Habia problemas entre la funcion check_dependencias y la writetogeoset.
En el orden de llamada.
- Mejoradas las queryes para la carga de muchos datos 


(9/3/2018)

Cambiado la creacion de la tabla log_obs. Problemas con el if not exists (psql version)


v1.5beta.5 (8/3/2018)
Cambios mayores:
- El tag de la medida+zona no es suficiente para describirlo. A partir de ahora, se necesita tambien el rango de fechas (como aparece en el nombre del archivo). Modificado comparadores de medidas en check_dependencias para saber si puedes o no puedes subir la medida, lo mismo para borrar, etc..
Ej: LOS_XY_FECHA1 != LOS_XY_FECHA2 (se consideran diferentes y se permite subir uno y el otro).
    Cuando borres uno, el otro sigue vivo.
    Lo mismo con las medidas que dependen del LOS.
- Creada tabla que contiene las medidas introducidas en la bd sin necesidad de filtrar por la tabla observationresult. Mas rapidez para saber que hemos subido a la bd.
- TabIII, cambio en la forma de mostrar los datos.


v1.5beta.4 (7/3/2018)
- Añadido archivo auxiliar psi_zone.txt con todas las zonas que se pueden cargar. Si intentas cargar un archivo csv con un nombre diferente a lo que hay en ese archivo, da error y no se carga. Carga de este archivo auxiliar en psi_config.py.
- Solucionado mas campos repetidos en los desplegables

v1.5beta.3 (6/3/2018)
- Borrado de la tabla samplingfeature
- Cambiado queryes de busqueda de duplicidades por otras mas simples

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
