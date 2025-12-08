# 🔍 PREGUNTAS DE CLARIFICACIÓN - MÓDULOS 11-27

**Propósito**: Aclarar ambigüedades, integración y funcionalidad de los módulos 11-27 del sistema Kibray.

**Instrucciones**: 
- Responde cada pregunta con el nivel de detalle necesario
- Marca con ✅ las preguntas respondidas
- Si algo no aplica o no es necesario, marca con ❌ y explica brevemente
- Puedes agregar ejemplos o casos de uso

---

## 📋 MÓDULO 11: TAREAS (TASKS)

### **Clarificaciones Generales**

**Q11.1**: ¿Las tareas tienen fecha de vencimiento (due date) además del estado?
- [ ] Respuesta: no tienen  fecha de vencimineto pero si se puede poner un limete opcional 

**Q11.2**: ¿Touch-up es solo un flag booleano (`is_touchup=True/False`) o necesita un sistema separado con tablero propio?
- [ ] Respuesta: si el touch up para no confundir necesitara un tablero propio, ya que el touch up sera mas como algo que requiere un atencion a resolver 

**Q11.3**: ¿Un cliente puede crear una tarea y asignarla directamente a un empleado, o solo el PM puede asignar?
- [ ] Respuesta: el clinete crea tareas esas tareas se ven visibles en el panel del admin y el de PM y ellos lo asignan, no el cliente

**Q11.4**: ¿Una tarea SIEMPRE debe estar vinculada a un schedule item o puede existir sin él?
- [ ] Respuesta: una tarea puede eistir sin schedulle, sin necesidad de estar atado a un schedulle o actividad 

**Q11.5**: ¿Completar una tarea actualiza automáticamente el progreso del schedule item vinculado?
- [ ] Respuesta: si si la tarea esta vinculada al schedulle eso le da segun el porcenje de la actividad actuliza la barra de completacion en el schedulle automaticmanete.

**Q11.6**: ¿Se necesita un sistema de priorización (Alta/Media/Baja) para las tareas?
- [ ] Respuesta: si es necesario crear un sistema de prioridad, que es necesario hace primero y que depsues, algunas qactividades o tareas son dependeintes, ejemplo primero tapar pisos, entonces se puede  poner o seguir con la actividad de lijar,

**Q11.7**: ¿Se manejan dependencias entre tareas? (Ejemplo: "Tarea B no puede empezar hasta que Tarea A esté completa")
- [ ] Respuesta: si a eso me referianteriormente en q11-7

**Q11.8**: ¿Las imágenes adjuntas a tareas se versionan o se reemplazan al subir una nueva?
- [ ] Respuesta: se versionan

**Q11.9**: ¿Quién puede eliminar una tarea y bajo qué condiciones?
- [ ] Respuesta: el admin y pm ello la eliminan si creen que es necesario o no es necesaria la tarea 

**Q11.10**: ¿Se notifican cambios de estado automáticamente al creador de la tarea y al PM?
- [ ] Respuesta: si al creador y al pm

**Q11.11**: ¿Los comentarios de una tarea son distintos de los comentarios globales del proyecto (módulo 22)?
- [ ] Respuesta: si los comentarios de la tarea son distintos son eclusivos de la tarea 

**Q11.12**: ¿Se puede reabrir una tarea "Completada"? Si sí, ¿se mantiene histórico de reaperturas?
- [ ] Respuesta: si si se mantiene un historico lo pueden hacer los empleados y pm, andim

**Q11.13**: ¿Se registra tiempo de trabajo directamente en una tarea (vinculándola con time tracking del módulo 3)?
- [ ] Respuesta: si se ouede hacer un boton iniciar tarea, entonces cunado abren la tarea empieza a hacer tracking hasta ue la cierra, esto no aplica para touch up. toup up se puede ver y cerrar con una foto y por quien

---

## 📅 MÓDULO 12: PLANES DIARIOS (DAILY PLANS)

### **Clarificaciones Generales**

**Q12.1**: ¿El plan diario se bloquea completamente al pasar a estado "Completed"?
- [ ] Respuesta: no, se puede editar, durante el proceso se puede agregar algo ma so eliminar o mover algo

**Q12.2**: ¿Las actividades del plan diario se convierten en tareas del módulo 11 o son entidades completamente distintas?
- [ ] Respuesta: si se convierten en tareas. lo que pensaba es crear tareas ene l trabajo o un creador de tareas asi tener una lista de pre-tareas cuando las selecionamos o las ponemos en la caja de actividades para el dayli plan esas actividades tareas ya tienen sus requisitos, lo que hacemos es agregar mas detalles si queremos pero estan en base asi optimizar el tiempo para rellenar o crera tareas todos los dias

**Q12.3**: ¿Las "horas reales" trabajadas se toman automáticamente del time tracking (módulo 3) o se ingresan manualmente en cada actividad?
- [ ] Respuesta: no se toman automaticmante, ejemplo empleado a tiene asignado projecto a esta manana cuando el empleado haga check in en la manana lo que puede hacer es del selector de projectos solo le aparecera el projecto asignado, asi al finalaizar el dia esas horas ya tiennen un destino claro

**Q12.4**: ¿Las alertas de "planes incompletos" (función 12.14) se disparan por qué criterios exactos?
- [ ] Respuesta: no hay tareas definidas ni asignacion de tareas

**Q12.5**: ¿Se necesita un histórico de planes diarios para comparar productividad por día/empleado?
- [ ] Respuesta: si 

**Q12.6**: ¿Se archivan los planes antiguos o permanecen accesibles indefinidamente?
- [ ] Respuesta: lo que recomiendes hacer esta bien conmigo

**Q12.7**: ¿Se pueden crear planes diarios futuros (programación anticipada)?
- [ ] Respuesta: si es el plan ir creando planes a fututro.

**Q12.8**: El campo "clima del día": ¿se ingresa como texto libre o estructura (temperatura, lluvia, humedad)?
- [ ] Respuesta: el clima debe de tormarse automaticamente segun la hubicacion del projecto

**Q12.9**: ¿Quién puede editar un plan una vez que ha sido publicado?
- [ ] Respuesta: el admin y PM

**Q12.10**: ¿Se integra con nómina (módulo 16) para validar que las horas registradas coincidan con las actividades completadas?
- [ ] Respuesta: no ya que las actividades pueden ser un poco confusas siempre y cuando se haga tracking de las horas por projecto sy dias considero que es sufieicnte, almenos que esto no sea complejo, ya qu ehabra actividades o touch up que no tienen un tracking time inicio a fin por lo que causaria muchos problemas 

---

## 📖 MÓDULO 13: SOPs (PLANTILLAS DE ACTIVIDADES)

### **Clarificaciones Generales**

**Q13.1**: ¿Al editar una SOP que ya se usó en planes previos, se actualiza retroactivamente o solo afecta planes futuros?
- [ ] Respuesta: si los SOP se iran mejoranmdo 

**Q13.2**: ¿Se requiere categorización obligatoria para cada SOP (ejemplo: Pintura, Carpintería, Limpieza)?
- [ ] Respuesta: si, asi se podra indentificar mejor en qu eetaoa se encuantran.

**Q13.3**: ¿Se necesita búsqueda avanzada en el catálogo de SOPs (por palabras clave, categoría, duración)?
- [ ] Respuesta: si que cada vez que se asigne una actividad o se cree una actividad haya una lupa que ayde a traer el SOP a la actividad tarea rapidamente asi se agerga automaticmante cuando slecionan lo que buscan, y tambien en el panel dedidado a sop ver creacion, edicion ect.

**Q13.4**: ¿Las SOPs tienen checklist de verificación que se debe completar paso a paso?
- [ ] Respuesta: si tiene sus check box asi se garantiza que se siguio cada paso

**Q13.5**: ¿Quién puede crear/editar/eliminar SOPs: solo Admin o también PM?
- [ ] Respuesta: admin pm

**Q13.6**: ¿Se mide el cumplimiento del tiempo estándar vs tiempo real para optimizar futuras SOPs?
- [ ] Respuesta: si actulamente no hemos agregado una manera de medir timepos de los sop, piensa en un ay si es posible hazlo

---

## 📦 MÓDULO 14: MATERIALES

### **Clarificaciones Generales**

**Q14.1**: El catálogo de materiales: ¿es global para toda la empresa o se pueden crear catálogos específicos por proyecto?
- [ ] Respuesta: si es global para toda la empresa

**Q14.2**: ¿El SKU debe ser único a nivel global o se permite duplicación por categoría?
- [ ] Respuesta: si

**Q14.3**: ¿El estado "Ordered" implica integración automática con proveedores externos (API) o es solo registro manual?
- [ ] Respuesta: manual 

**Q14.4**: ¿Las solicitudes de materiales requieren workflow de aprobación (PM solicita → Admin aprueba)?
- [ ] Respuesta: si 

**Q14.5**: ¿El "ticket de recepción de materiales" (14.13) genera ajuste automático al inventario (módulo 15)?
- [ ] Respuesta: si una vez que se registre recepcion, o que los empleados recogan o compren algo de la tienda eso afectara al prejcto al inventario

**Q14.6**: ¿La "compra directa" (14.14) crea automáticamente un gasto en el módulo 4?
- [ ] Respuesta: si, compra crea registors en inventario y gastos

**Q14.7**: ¿La unidad de medida es configurable (piezas, litros, metros cuadrados, galones)?
- [ ] Respuesta: si es configurable

**Q14.8**: ¿Se permite gestionar múltiples proveedores por material?
- [ ] Respuesta: si hay multiples 

**Q14.9**: ¿Se maneja costo promedio o último costo de compra?
- [ ] Respuesta: no aun

**Q14.10**: ¿Al recibir menos cantidad de la ordenada, qué pasa con la diferencia (backordered, cancelado)?
- [ ] Respuesta: si se recive menos se debe. de mandar notificacion al admin y pm, y marcar esto como aun en orden o regresarlos a solicitud al dashboard del admin

**Q14.11**: ¿Se puede cancelar parcialmente una solicitud de materiales?
- [ ] Respuesta: culaquier cosa que ello quieran se puede reducir la cantidad de materiales, o remover algo aun item 

**Q14.12**: ¿Se vinculan materiales directamente a líneas de presupuesto (módulo 9)?
- [ ] Respuesta: los gastos del costo si, pero tambien seria bueno capturar la infomraicon de que tanto se gasto en materiales como cuantos gallones use en esta casa datos de esos 

**Q14.13**: ¿Se necesita historial de cambios de costo de materiales?
- [ ] Respuesta: no los costos son muy variables

**Q14.14**: ¿Se notifica al PM cuando el estado de una solicitud cambia a "Received"?
- [ ] Respuesta: si 

---

## 📊 MÓDULO 15: INVENTARIO

### **Clarificaciones Generales**

**Q15.1**: Conceptualmente, ¿cuál es la diferencia entre "catálogo de materiales" (módulo 14) e "inventario" (módulo 15)?
- [ ] Respuesta: catalogo de materiales es como una lista de que materiales existen en genral pero esta lista no te dice que cantidad tinenes de ello es como el item por si solo para yudar a hacer ordenes mas rapidas, ya que sabes que buscan de la lista. el inventario es la lista de materiales con cantidad exacta de lo que hay y de lo que no hay.

**Q15.2**: Vincular inventario a un proyecto: ¿significa traslado físico o solo reserva virtual?
- [ ] Respuesta:  si el inventario habra inventario por projecto y inventario storage, que es lo que tengo ene l estorage base, el el projecto lo que tengo en cada projecto solo en ese projecto, puede ver multiples inventarios, storage, projecto 1, projecto 2.

**Q15.3**: ¿Qué tipos de movimientos de inventario se manejan? (entrada, salida, ajuste, transferencia entre proyectos)
- [ ] Respuesta: entrada salida, trasferencia entre. projectos, regreso a base estorage.

**Q15.4**: La ubicación física: ¿es estructura jerárquica (Almacén → Estante → Caja)?
- [ ] Respuesta: nonaun no tenemos ese sistema. si puede implementarlo como en notas o una casilla o algo y que sea opcional ya en un futuro tal vez lo hagamos rigido.

**Q15.5**: ¿Las alertas de stock bajo tienen umbral personalizable por item o es global?
- [ ] Respuesta: las definiran cuando se creen los items, cad aitem tendra su umbral. el cual se pude editar.

**Q15.6**: ¿El inventario se sincroniza automáticamente con materiales solicitados (módulo 14)?
- [ ] Respuesta: si ejemplo ya que la orden se recogio eso significa lo que tenmos y por categorias ha aumentado en el inventario del trabajo o de donde se solicite.

**Q15.7**: ¿El inventario soporta múltiples ubicaciones físicas simultáneas (multi-site)?
- [ ] Respuesta: no un item no puede estar en muchos lugares a la vez, tengo dos apiradoras feestol perto esas aspiradoras pueden definirse como aspiradora festool A y B.

**Q15.8**: ¿Se requiere valuación de inventario (FIFO/LIFO/costo promedio)?
- [ ] Respuesta:  si puede agregarlo esta bien aun no se como usar esta funcion pero puedo aprender en el futuro.

**Q15.9**: ¿Un movimiento de inventario puede vincularse a una tarea, proyecto o gasto específico?
- [ ] Respuesta: podria si en la tarea se solicita que se lleve algo escalera o algo.

**Q15.10**: ¿Se permite inventario negativo?
- [ ] Respuesta: no no puede haber invenyrio negativo.

**Q15.11**: ¿Se audita cada movimiento con usuario, timestamp y razón?
- [ ] Respuesta: no

**Q15.12**: ¿Se permiten transferencias de inventario entre proyectos?
- [ ] Respuesta: si

**Q15.13**: ¿Al consumir material en trabajo, se descuenta manual o automáticamente?
- [ ] Respuesta: automaticamnte ejemplo cerrando el dia se registra que se gasto 10 tapes, si se tenia 20 entonces ya solo que daran 10

**Q15.14**: ¿El dashboard de inventario muestra rotación y obsolescencia?
- [ ] Respuesta: si

---

## 💰 MÓDULO 16: NÓMINA (PAYROLL)

### **Clarificaciones Generales**

**Q16.1**: ¿El período de nómina es semanal fijo o configurable (quincenal/mensual)?
- [ ] Respuesta: semanal

**Q16.2**: "Generar registros automáticamente": ¿la fuente exclusiva son las time entries (módulo 3) o hay entradas manuales?
- [ ] Respuesta: pueden haber entradas manuales o correciones ejemplo un empleado olvido hacer check in o check out, ahi el admin hace estas ediciones o regristar entradas.

**Q16.3**: "Ajustar tarifa" (función 16.5): ¿aplica retroactivo a todo el período o solo para ese período específico?
- [ ] Respuesta: aplica hacia el fututro ejemplo si de hoy en adelante le aumento un dollar asi se mantine. ese salario la siguiente semnana almenos qu se edite, reduzca o aumente

**Q16.4**: La "referencia de pago": ¿almacena comprobante (archivo) o solo texto (número de cheque, ID de transferencia)?
- [ ] Respuesta: se almacena la infomacion basica nombr e fehc a depago, numbero de cheque, y el monto.

**Q16.5**: ¿Se calculan horas extras, bonos y deducciones?
- [ ] Respuesta:  agrega esa funcion aun no esta en uso pero podria estar en el futuro

**Q16.6**: ¿Los registros de nómina tienen estados (Draft, Reviewed, Paid)?
- [ ] Respuesta: si el draft es loq ue sale porque ellos hagan check in y check out, el pm los revisa y les da aprovar o reporta errores y el admin cuando registra los cheque numero y de la pagada a esa semana se cmabia el estautus a paid.

**Q16.7**: Vista moderna vs vista legacy: ¿cuál es la diferencia funcional real?
- [ ] Respuesta: considero que moderno sela laelecioon peor no tengo idea porque tengo dos modelos.

**Q16.8**: ¿Se calculan impuestos o solo pago bruto?
- [ ] Respuesta:  se paga en bruto pero agrega la funcion para que en el futuro se ponga.

**Q16.9**: ¿Se valida que no falten clock-ins antes de cerrar el período de nómina?
- [ ] Respuesta: si,

**Q16.10**: ¿Los ajustes manuales a registros se auditan (quién, cuándo, por qué)?
- [ ] Respuesta: el admin cunaod hay un error de caputra por el empleaod o se olvido de hacer correctmente chek in o prpoblemas con la app

**Q16.11**: ¿Se soportan múltiples tipos de tarifa (regular vs overtime)?
- [ ] Respuesta: si multiples y cada uno tiene su rate cada empleado

**Q16.12**: ¿Los registros de nómina se pueden regenerar si cambia la tarifa de un empleado?
- [ ] Respuesta: si del dia de cambio hacia adelante.

**Q16.13**: ¿Se relacionan los pagos de nómina con el módulo de ingresos/gastos?
- [ ] Respuesta: si el pago de nomina es el gasto por labor.

**Q16.14**: ¿Se requiere exportación a sistemas externos (ADP, QuickBooks)?
- [ ] Respuesta: si opcional

**Q16.15**: ¿Se detectan y marcan días sin registro automáticamente?
- [ ] Respuesta: si

**Q16.16**: ¿Las horas de múltiples proyectos se desglosan en el reporte de nómina?
- [ ] Respuesta: si, para verificacion de qu e todod se ingreso correctmente

---

## 👥 MÓDULO 17: CLIENTES

### **Clarificaciones Generales**

**Q17.1**: El acceso granular por proyecto: ¿se asigna manualmente o automáticamente al crear el proyecto?
- [ ] Respuesta: autpomaticmanete a todos con exepciond e los clientes esos solo tienne acceso por manual

**Q17.2**: "Hacer solicitudes" (17.10): ¿qué tipo de entidad es? (ticket, change request, solicitud general)
- [ ] Respuesta: solicitude  de material, solicitud de CO, colicitud de infmacion o general

**Q17.3**: ¿El cliente puede subir archivos (colores, planos, referencia)?
- [ ] Respuesta: si el cliente pude subri archivos pero esos archivos se quedaran en un espacio de archvos por cliente, ya el admin los copiara y mejorara

**Q17.4**: ¿Las aprobaciones de color (módulo 19) requieren firma digital? Si sí, ¿en qué formato se almacena (archivo, hash, timestamp)?
- [ ] Respuesta:  si nececita ser fimado y proquiien se firmo, si estan el panel del cleinte o dueno se registar su nombre correo y firma

**Q17.5**: Seguridad: ¿el cliente puede ver facturas de otros clientes del mismo proyecto?
- [ ] Respuesta: no las facturas estan por projecto, al menos que sean de la misma compania ejemplo cleinte A tiene 10 projectos, su staft de este cleinte si puede ver todo pero porque ypo le di acceso a ese usuario a ese projecto.

**Q17.6**: ¿El cliente puede iniciar órdenes de cambio o solo verlas?
- [ ] Respuesta: puede requerir CO

**Q17.7**: ¿El cliente puede crear tareas y etiquetarlas como "Client Request"?
- [ ] Respuesta:  si el puede

**Q17.8**: ¿Puede ver costos acumulados vs solo lo facturado?
- [ ] Respuesta: si ellos ven su budget el costo que les estoy cobrando por su projecto y lo que ellos ya han pagado

**Q17.9**: ¿Puede cancelar una solicitud previamente enviada?
- [ ] Respuesta: si, pero tiene que esccribir la razon asi se notifica al amnin porque s ecnacelo 

**Q17.10**: El acceso a cronograma público: ¿incluye dependencias y porcentajes o solo fechas?
- [ ] Respuesta: todo

**Q17.11**: ¿Puede agregar comentarios generales (módulo 22) o solo leer?
- [ ] Respuesta: si s epude agregar comentarios genrales

**Q17.12**: ¿Las solicitudes del cliente generan notificación automática al PM?
- [ ] Respuesta: si pero los pm no pueden aprovarlas solo el admin las aprueva 

---

## 📸 MÓDULO 18: FOTOS DEL SITIO

### **Clarificaciones Generales**

**Q18.1**: ¿Hay resolución máxima para las fotos? ¿Se optimizan automáticamente?
- [ ] Respuesta: no lo necesario para informar y buscar errores o referencia 

**Q18.2**: El campo "ubicación": ¿es texto libre o georreferenciado (GPS)?
- [ ] Respuesta: el gps debe de ser automatico base a la ubicacion del projecto

**Q18.3**: Vincular con muestra de color aprobada: ¿es relación unidireccional o bidireccional?
- [ ] Respuesta: si es relacional una muestra puede ser aprovada, pero tambien se puede ingresar un color que ya se aprovo y no paso por muestras.

**Q18.4**: ¿Hay control de privacidad (fotos solo para cliente vs solo interno)?
- [ ] Respuesta: si

**Q18.5**: Filtrar por fecha: ¿rango completo o día exacto?
- [ ] Respuesta: si 

**Q18.6**: ¿Se permite versionado de fotos o se reemplazan?
- [ ] Respuesta: versionados permitidos

**Q18.7**: ¿Se permite subida de múltiples fotos en lote?
- [ ] Respuesta: si

**Q18.8**: ¿Se etiqueta automáticamente por proyecto?
- [ ] Respuesta: si

**Q18.9**: ¿Se puede eliminar una foto aprobada vinculada a un color?
- [ ] Respuesta: si se puede editar 

**Q18.10**: ¿Se soportan categorías (progreso, detalle, problema)?
- [ ] Respuesta: si

**Q18.11**: ¿Se notifica al cliente cuando se sube una nueva foto?
- [ ] Respuesta: los dayli logs el reporte diario.

**Q18.12**: ¿Se genera miniatura automática para performance?
- [ ] Respuesta: si pero que siempre se pueda hacer zoom si se requiere

**Q18.13**: ¿Se requiere marca de agua (watermark)?
- [ ] Respuesta: no

**Q18.14**: ¿Se puede buscar texto en título/caption?
- [ ] Respuesta: si

**Q18.15**: ¿Se puede restringir descarga para clientes?
- [ ] Respuesta: si

**Q18.16**: ¿Se vincula con reportes de daños (módulo 21)?
- [ ] Respuesta: si

---

## 🎨 MÓDULO 19: MUESTRAS DE COLOR

### **Clarificaciones Generales**

**Q19.1**: Flujo de estados: ¿quién específicamente puede cambiar a "Approved" vs "Rejected" (Admin, PM, Cliente, Designer)?
- [ ] Respuesta: PUEDE CAMBIARLAS EL ADMIN, CLIENTE Y DESIGNER, DUENO 

**Q19.2**: ¿Se puede revertir una muestra "Approved" de vuelta a "Pending"?
- [ ] Respuesta: SI, CUANDO PASA ESTO SE MANDA NOTIFICACION A TODOS LOS INVOLUCRADOS

**Q19.3**: ¿Se pueden agrupar muestras por habitación o ubicación?
- [ ] Respuesta: SI SE PUEDE AGRUPAR POR ESAPCIOS HABITACIONES, Y ASI DE ESA MISMA MANERA SE APROVARA 

**Q19.4**: ¿Se requiere orden secuencial (Muestra #1, #2, #3)?
- [ ] Respuesta: SI DE PREFERENCIA EN MISMO ENUMERACIMENTO DEL CLINETE O INVOICE CON EL CAMBIO DE AGREGAR LETRA M, EJEMPLO KPISM10001, KPISM10002, ECT. DEPENDE DEL CLIENTE NOMBRE Y EL NUMERO DE MUESTRA 

**Q19.5**: ¿Se notifica a Admin cuando se crea o rechaza una muestra?
- [ ] Respuesta: SI Y A TODOS EN ESE PROJECTO CON EXEPCION DEL L EMPLEADO

**Q19.6**: ¿Se guarda quién hizo cada acción y timestamp?
- [ ] Respuesta: SI

**Q19.7**: ¿Se relacionan con tareas tácticas ("Aplicar color X en sala")?
- [ ] Respuesta: SI, SI ALGIEN SELECIONA EN LA TAREA HACE X TAREA EN HABITACION X Y TAMBIEN MARCA EN EL PLANO, LA MARCA EN EL PLANO ES INDEPENIENDTE, PERO EN LA TAREA PUEDE ELEJIRSE LA HUBICAICON SALA, COCINA ECT, Y SE DEBE CARAGR LA INFORMACION DE ESE LUGAR COMO COLOR DE PAREDES, TECHOS ECT.

**Q19.8**: ¿Se soportan múltiples fotos por muestra?
- [ ] Respuesta: SI SE PUEDE SUBRI MULTIPLES FOTOS POR MUESTRA

**Q19.9**: ¿Se exportan las aprobaciones a PDF legal?
- [ ] Respuesta: SI, SE CREA DE ESA MANERA EL REGISTRO QUE SE BNVIA A TODOS LOS INVOLUCRADOS

**Q19.10**: ¿Se puede buscar por código o nombre de color?
- [ ] Respuesta: SI CON LA INFORMACION DEL KPISM10001, O EL NOMBRE DE COLOR Y ME MUESTRA TODAS LAS MUESTRAS DE COLOR, EJEMPLO SW-7006, ESTA EN PROJECTO X Y PROJECTO Y 

**Q19.11**: ¿Hay límite de muestras activas por proyecto?
- [ ] Respuesta: NO

**Q19.12**: El rechazo: ¿requiere motivo obligatorio?
- [ ] Respuesta: SI COMENTARIO, ASI PODEMOS CORRGUIR LA SOIGUIENTE MUESTRA O TYENER MAS INFORMACON

**Q19.13**: ¿La firma digital se almacena como archivo, hash criptográfico o solo timestamp?
- [ ] Respuesta: SI EN ALGO CRIPTOGRAFICO QUE FUNCIONE PARA FINES LEGALES 

---

## 📐 MÓDULO 20: PLANOS Y BLUEPRINTS

### **Clarificaciones Generales**

**Q20.1**: ¿Al subir una nueva versión de un plano, se archiva la versión anterior?
- [ ] Respuesta: SI, SE REMPLAZA LA ANTERIOR, ENTONCES LOS PINES QUEDAN OTRA VEZ DISPONIBLES PARA RECOLOGACION , COMO SI SELECIONARA EL PIN DE LA LISTA Y DIJERA ASIGANAR PIN, ENTONES ESO ME DEJA PONERLO DONDE YO QUIERA 

**Q20.2**: ¿Los pins pueden migrar de una versión de plano a otra?
- [ ] Respuesta: SI SE MIGRAN COMO UNA LISTA DE PINES DISPONIBLES PARA ASIGANCION 

**Q20.3**: ¿Los pins se pueden cerrar cuando se resuelve el issue?
- [ ] Respuesta: SI EN EL CASO DE TUCH UP SE ELIMINAN AUTOMATICMANETE EN CUNATO SE TERMINA EL RETOQUE TOUCH UP, PERO NO CON LA INFOMRACION LOS PINES DE INFORMACION O NOTAS ESAS SEMATIENEN SIEMPRE.

**Q20.4**: ¿Se notifica al PM al crear un pin tipo "Issue"?
- [ ] Respuesta:  SI

**Q20.5**: ¿Se requiere validación de tamaño máximo de archivo de plano?
- [ ] Respuesta: NO

**Q20.6**: ¿Se soporta zoom, capas y rotación de planos?
- [ ] Respuesta: SI

**Q20.7**: ¿Se pueden filtrar pins por tipo y estado?
- [ ] Respuesta: SI

**Q20.8**: El pin multi-punto (path): ¿guarda coordenadas normalizadas (porcentaje del plano)?
- [ ] Respuesta: SEGUN TU REMOENDACION ELIGE LO MAS ADECUADO, TRABAJREOS CON MULTIPLES INSTRUMENTOS, IPAD, COMPUTADORAS, TELEFONOS ECT.

**Q20.9**: ¿Se requiere exportar plano con pins marcados a PDF?
- [ ] Respuesta: SI

**Q20.10**: ¿Los clientes pueden comentar en pins?
- [ ] Respuesta: SI PUEDEN COMENTARLOS

**Q20.11**: ¿Los pins tipo "Issue" crean automáticamente tareas o reportes de daño?
- [ ] Respuesta: si, si e pin es creado desde el formulario de retoque u advertencia, son dos portales o accesos que debemos crear asi ellos desde el inicio pueden definir como a que boton deben de eleguir asi es  mas facil crearlo observaciones y retoques y cuando se crean observaciones y retoques entonces se crea una tarea que se notifica a pm y admin 

**Q20.12**: ¿Se soportan adjuntos en pins (fotos, documentos)?
- [ ] Respuesta: si el pin es un contenedor de informacion

---

## 🔧 MÓDULO 21: REPORTES DE DAÑOS

### **Clarificaciones Generales**

**Q21.1**: Severidad: ¿escala exacta definida? (Low/Medium/High/Critical)
- [ ] Respuesta: si me parece adecuado tener categorias 

**Q21.2**: ¿Quién puede cambiar el estado a "In Progress" o "Resolved"?
- [ ] Respuesta:  pm y adminn

**Q21.3**: ¿Asignar responsable: se asigna usuario específico o rol?
- [ ] Respuesta: a pm y admin 

**Q21.4**: ¿Se crean automáticamente tareas de reparación al reportar daño?
- [ ] Respuesta: si se amnda como prioridad notificacion a admin y pm, 

**Q21.5**: ¿Puede un empleado crear reporte o solo PM/Admin?
- [ ] Respuesta: solo el admion y pm, el empleado puede crera reporte de su progreso de su actividad tarea asiganda, con fotos y selecionar de una bara el procentaje que ha completado

**Q21.6**: ¿Se requiere foto obligatoria?
- [ ] Respuesta: si

**Q21.7**: ¿Se permite cambiar severidad después de creación?
- [ ] Respuesta:  si

**Q21.8**: ¿Se notifica automáticamente al responsable asignado?
- [ ] Respuesta: si

**Q21.9**: ¿Se mide tiempo desde "Reported" → "Resolved"?
- [ ] Respuesta: si, de reportado, revisado asigando, en progreso, resuelto, o en caso que se tarde mucho pendiente

**Q21.10**: ¿Se relaciona con órdenes de cambio si el daño genera trabajo adicional?
- [ ] Respuesta: si, el dano es grave por ejemplo dano de una pared y se requiere pintar , se puede agregar como detro del co un espacio para addicional infomraicon o causa del cambio se puede selcionar un problema o simplemente en el cmabio de orden se puede escribir algo totalemte diferente, es opcional

**Q21.11**: ¿El cliente puede ver reportes de daños?
- [ ] Respuesta: si

**Q21.12**: ¿Se consolida en informe mensual?
- [ ] Respuesta: si

**Q21.13**: ¿Se pueden agrupar daños por ubicación o causa?
- [ ] Respuesta: si, asi podemos en u. futuro identificar patrones 

---

## 💬 MÓDULO 22: COMUNICACIÓN

### **Clarificaciones Generales**

**Q22.1**: "Canal de chat": ¿es único por proyecto o múltiples canales (general, logística, cliente)?
- [ ] Respuesta: si el clinete tiene asigado multiples projectos, puede tener un chat global de esos tres 4 x projectos, pero en cuanto slecione un projecto desde su panel y entre en el projecto ahi tendra el chat de ese projecto no el global

**Q22.2**: Notificaciones: ¿se envían por email + in-app + push?
- [ ] Respuesta: se nevia por ambas 

**Q22.3**: ¿Los comentarios en tareas son parte del sistema de chat o entidades separadas?
- [ ] Respuesta: son separadas el chat se mantiene lo mas limpio posible pero si consideras que puede ser intuitivo y mejor traer o selcionar una tarea y especificar algo ejemplo en el chat del projecto x o chat global se seleciona el incono + y de ahi tiene opciones de agregar photo, agregar, arhivo, agregar u selcionar pin, color, touch up, o tarea, y ase agregar como un @x tarea requiero que sea asi o loprefiero de. esta manera x cosa que quera, y esto automaticmanete copai ese mensaje como nota dentro de ese contenedor y dice quien lo escrinbio.

**Q22.4**: Historial de mensajes: ¿tiempo de retención definido o indefinido?
- [ ] Respuesta: indefininido.

**Q22.5**: ¿Se soportan menciones (@usuario)?
- [ ] Respuesta: si

**Q22.6**: ¿Se pueden archivar canales de chat?
- [ ] Respuesta: si

**Q22.7**: ¿Se permite eliminar mensajes? Si sí, ¿solo el autor o también moderadores?
- [ ] Respuesta: si si el damin ejemplo envio un mensaje incorrecto, el admin puede elimoinarlo

**Q22.8**: ¿Se soportan archivos adjuntos en chat?
- [ ] Respuesta: si

**Q22.9**: ¿Las notificaciones por email son todas o filtradas según preferencias del usuario?
- [ ] Respuesta: preferencia del usuario

**Q22.10**: ¿Se agrupan notificaciones similares para evitar spam?
- [ ] Respuesta: si

**Q22.11**: ¿El cliente puede participar en chat interno o solo en canal cliente?
- [ ] Respuesta: solo de cliente a admin, designer, owner, pero no al staff 

**Q22.12**: ¿Los comentarios en proyectos son distintos del chat?
- [ ] Respuesta: ya mencione algo en la pregunta q22.3

**Q22.13**: ¿Se soporta markdown o formatting en mensajes?
- [ ] Respuesta: si

**Q22.14**: ¿Se indexa el contenido para búsqueda?
- [ ] Respuesta: si

**Q22.15**: ¿Se requiere moderación o bloqueo de usuario?
- [ ] Respuesta: si

---

## 🔢 MÓDULO 23: CÓDIGOS DE COSTO

### **Clarificaciones Generales**

**Q23.1**: Estructura de códigos: ¿jerárquica (01 General / 01-01 Subcategoría)?
- [ ] Respuesta: si jerarjica y genral con subcategorias

**Q23.2**: ¿Se valida que no se asigne un código inexistente a gastos/tiempo?
- [ ] Respuesta: si

**Q23.3**: Asignar código a gastos y tiempo: ¿es obligatorio o opcional?
- [ ] Respuesta: obligatorio y autofill, se relena automaticmanete 

**Q23.4**: ¿Los reportes agrupan costos reales vs plan/presupuesto?
- [ ] Respuesta: si

**Q23.5**: ¿Un código se puede desactivar sin borrar el histórico?
- [ ] Respuesta: si

**Q23.6**: ¿Formato estándar definido (numeración fija)?
- [ ] Respuesta: si

**Q23.7**: ¿Se puede editar un código después de haberse usado?
- [ ] Respuesta: no

**Q23.8**: ¿Se relacionan códigos con líneas de presupuesto (módulo 9)?
- [ ] Respuesta: si, normalemte simepre van con el kpis kp= Kibray Painting=nombre  del a compania, is= ivan stanley=cliente nombre, SR= schocket residence=nombre del projecto I= invoice =actividad, puede ser M= muertra, Es= estimado, ect + numeros en orden despues de 1000.

**Q23.9**: ¿Se maneja fecha de vigencia para códigos?
- [ ] Respuesta: no

**Q23.10**: ¿Se requieren códigos por defecto al instalar sistema?
- [ ] Respuesta: si

**Q23.11**: Tiempo sin código: ¿se marca como "Unassigned"?
- [ ] Respuesta: valida segun la infomacion que te proporciuoe con las otras pregunats referentes.

**Q23.12**: ¿Se validan duplicados por nombre?
- [ ] Respuesta:  si no debe de aver duplicados 

**Q23.13**: ¿Los reportes muestran varianza vs estimado?
- [ ] Respuesta: si

**Q23.14**: ¿Se exportan reportes a CSV?
- [ ] Respuesta: si

**Q23.15**: ¿Se asocian códigos a change orders para análisis específico?
- [ ] Respuesta: si

---

## 📊 MÓDULO 24: DASHBOARDS

### **Clarificaciones Generales**

**Q24.1**: Dashboard Admin: ¿qué KPIs financieros específicos se muestran?
- [ ] Respuesta: todos lso diponibles con la informacion de todo la compania disponible, filtros, para una busqueda con lupa increible desde un panorama general de la compania hasta un detalle minimo de tarea

**Q24.2**: Dashboard PM: ¿muestra riesgo/alertas de presupuesto por proyecto?
- [ ] Respuesta: si

**Q24.3**: Dashboard Superintendent: ¿enfoque en tareas de campo vs cronograma?
- [ ] Respuesta: el superintendent es el encaragdo de el projecto es cuando un cleinte asigan a otra persona que esta en el sitio porque este cliente eta muy ocupado para ver el progreso en sitio asi que asigana a alguien mas en trabajo de cmapo esta persona tiene la smismas funcines del cleinte.

**Q24.4**: Dashboard Employee: ¿solo tareas + horas + plan diario?
- [ ] Respuesta: si, el empleado recive la infomacion necesairo y heramientes de conocieminteo basica que no se sature de un amnera muy simple visualemnte facil de entender, asi su trabajo e smas facil y practico ycreativo

**Q24.5**: Dashboard Client: ¿facturas + progreso + aprobaciones pendientes?
- [ ] Respuesta: si, basicmnete el cleinte y supeintenden pueden tenne rle mismo dashbord, ello manejan el projecto en campo y oficina, hay muy rarars veces que el superintenden solo maneja el cmapo, en lo general siempre esta involucardo al igual que el cliente, pero hay excepciones cuando el cliente tiene multiples projecto sy tiene multiples superintendent, asi que el cleinte tienen un dashboard de incio donde puede slecionar projectoy puede ver mas projectos y ver que pasa con cad aprojecto en shceulle, notas, nformacion, fncnanzas de los invoices, estimados, co, comunicaicon, aprovaciones tareas, ect.

**Q24.6**: Dashboard Designer: ¿colores + planos + feedback?
- [ ] Respuesta: si el disenador puede crear yareas, puede crear colores, puede aproavr colores, puede comentar, puede ver el cronograma, puede ver reportes de progreso, puede ver planos de pin, planos de informaicon, colores, el chat peude tener chat directo con el cleinte, dueno, admin, no con pm o empleados.

**Q24.7**: Dashboard Facturación: ¿aging report + facturas overdue?
- [ ] Respuesta: si es el poanel donde puedo crar facturas, ver facturas, cerrar facturas, todo lo relaiconado con facturas.

**Q24.8**: Dashboard Nómina: ¿total horas por período y estado de revisión?
- [ ] Respuesta: si ejempleo lo que puestar en la nomaina es por semana de lunes a domingo sermana x, semana b de lunes b a nomingo b, van viendose por bloques , no es por dia  es por cada bloque de semana 

**Q24.9**: Dashboard Materiales: ¿solicitudes pendientes y stock bajo?
- [ ] Respuesta:  si, todo lo relacionado con materiales, aqui deve estar cada funciono racionado con materiales.

**Q24.10**: Dashboard Earned Value: ¿métricas CPI/SPI y tendencias históricas?
- [ ] Respuesta: si tdo lo analitico de dinero y costos reales vs todo lo real aqui deve de ser.

**Q24.11**: ¿Se actualiza cada dashboard en tiempo real o batch (cada X minutos)?
- [ ] Respuesta: tiempo real 

**Q24.12**: ¿Los filtros son personalizables por usuario?
- [ ] Respuesta: si el usuario puede selecioanr su filtro 

**Q24.13**: ¿Los widgets son movibles/reordenables?
- [ ] Respuesta: si si es aposible y no causa comflcito si se ria increible ais cada quien puede buscar su mejor sitema de enfoque 

**Q24.14**: ¿Los datos se cachean para mejorar performance?
- [ ] Respuesta: si, iemtras eso no dane la infomacion

**Q24.15**: ¿Se puede exportar cada dashboard a PDF?
- [ ] Respuesta: si solo admin y pm

**Q24.16**: ¿Se guarda la configuración del dashboard per user?
- [ ] Respuesta: si, asi cada vez que entran su entorno esta confirgurado segun su solcitud 

**Q24.17**: ¿Se aplican permisos dinámicos (ocultar widgets según rol)?
- [ ] Respuesta: si segun cada roll tiene los permisos 

---

## 🔒 MÓDULO 25: SEGURIDAD Y PERMISOS

### **Clarificaciones Generales**

**Q25.1**: Rate limiting: ¿niveles por IP, usuario o endpoint?
- [ ] Respuesta: deconosco esto, el usario puede inicar secion de multiples aparatos iempre que no exceda 5

**Q25.2**: ¿La validación AJAX es centralizada (middleware) o manual en cada vista?
- [ ] Respuesta: segun tu remocendaicon con loq ue sabes de nuestra app

**Q25.3**: Sanitización de inputs: ¿librería centralizada (Bleach) o manual?
- [ ] Respuesta: segun tu remoendacion para mejor experiencia y lo que sabes nuestra app

**Q25.4**: Modelo de permisos: ¿Django groups + custom flags?
- [ ] Respuesta: si

**Q25.5**: Control de acceso por proyecto: ¿tabla intermedia usuario-proyecto con roles?
- [ ] Respuesta: si seria increible tener un tabla o algo que me permita filtarra los permisos y usarios de cada projecot en el admin panel 

**Q25.6**: ¿Se auditan accesos fallidos?
- [ ] Respuesta: si

**Q25.7**: ¿Se requiere MFA (2FA) para Admin?
- [ ] Respuesta: claro sera algo increible tenerlo pro seguridad puede ser con una app de autentificaicon  o codigo

**Q25.8**: ¿Expiración de sesión configurada?
- [ ] Respuesta: no

**Q25.9**: ¿Encriptación de datos sensibles (nómina, clientes)?
- [ ] Respuesta: si, lo mejor posible

**Q25.10**: ¿Se registran intentos fallidos de login?
- [ ] Respuesta: si y se reportan 

**Q25.11**: ¿Rate limiting varía por roles?
- [ ] Respuesta: no

**Q25.12**: ¿Permisos granulares por acción (ver/editar/borrar/aprobar)?
- [ ] Respuesta: si segun roles 

**Q25.13**: ¿Los clientes pueden acceder a endpoints AJAX directos?
- [ ] Respuesta: dame tu reomendacion

**Q25.14**: ¿Validación uniforme para cada request (middleware)?
- [ ] Respuesta: si

**Q25.15**: ¿Los logs de seguridad se centralizan?
- [ ] Respuesta: si

**Q25.16**: ¿Desactivación temporal de usuarios (soft lock)?
- [ ] Respuesta: si

---

## ⚙️ MÓDULO 26: AUTOMATIZACIÓN (CELERY TASKS)

### **Clarificaciones Generales**

**Q26.1**: ¿Se usan retries automáticos para tareas fallidas?
- [ ] Respuesta: si

**Q26.2**: ¿Se notifican fallos de tareas críticas?
- [ ] Respuesta: si

**Q26.3**: ¿Se pueden pausar algunas tareas temporalmente?
- [ ] Respuesta: si

**Q26.4**: ¿Los parámetros son configurables vía panel (horarios, frecuencias)?
- [ ] Respuesta: si

**Q26.5**: "Enviar notificaciones pendientes" (task 26.5): ¿qué cola utiliza?
- [ ] Respuesta: notificaicon por app ymail si se rerquiere 

**Q26.6**: "Limpiar notificaciones viejas": ¿se borran o archivan? ¿Criterio de antigüedad?
- [ ] Respuesta: si

**Q26.7**: "Generar nómina semanal": ¿bloquea el período automáticamente?
- [ ] Respuesta: si

**Q26.8**: "Revisar inventario bajo": ¿genera notificación o tarea de reposición?
- [ ] Respuesta: si

**Q26.9**: "Recordatorios de planes diarios": ¿a quién se envían (PM, empleados, ambos)?
- [ ] Respuesta: pm

**Q26.10**: ¿Se firma/registra cada ejecución con timestamp para auditoría?
- [ ] Respuesta: si

**Q26.11**: "Actualizar estados de facturas": ¿lógica exacta (pasar a overdue si fecha_vencimiento < hoy)?
- [ ] Respuesta: si

**Q26.12**: "Alertar planes incompletos": ¿criterio exacto (actividades no completadas > X%)?
- [ ] Respuesta: >50%

---

## 📄 MÓDULO 27: EXPORTACIÓN Y REPORTES

### **Clarificaciones Generales**

**Q27.1**: PDF de factura: ¿branding configurable (logo, colores)?
- [ ] Respuesta: si

**Q27.2**: PDF de proyecto: ¿incluye fotos, colores, CO, earned value?
- [ ] Respuesta: solo para admin no para alguien mas el ev y lo finaciero , los invoices y costos de projecto ejemplo el costo del prjecto en el cleinte se vera reflejado en invoices cobrados para co cobrado, que son los invoices al final de cuenta, para los pm se vera el costo esperado o programado vs los costos reales que gastaraon si estan = o menor 0 esta en verde, si es mayor a 0 rojo,

**Q27.3**: ¿El cronograma se incluye en PDF de proyecto con timeline?
- [ ] Respuesta: si

**Q27.4**: Earned Value CSV: ¿columnas exactas (PV, EV, AC, CV, SV, CPI, SPI, fechas)?
- [ ] Respuesta: si solo admin

**Q27.5**: Reporte gastos: ¿filtros por código de costo, proveedor, proyecto?
- [ ] Respuesta: si

**Q27.6**: Reporte ingresos: ¿filtros por método de pago y estado?
- [ ] Respuesta: si

**Q27.7**: Reporte ganancias: ¿muestra margen por proyecto?
- [ ] Respuesta: si

**Q27.8**: ¿Se programan reportes automáticos (envío por correo)?
- [ ] Respuesta: si cada mes al admin 

**Q27.9**: ¿Se firman digitalmente los PDFs (inmutabilidad)?
- [ ] Respuesta: si

**Q27.10**: ¿Se cachean reportes frecuentes?
- [ ] Respuesta: si

**Q27.11**: ¿El cliente puede descargar algunos reportes (con restricciones)?
- [ ] Respuesta: si solo que el tiene visble en su dashbaord nada de lo interno 

**Q27.12**: ¿Multi-idioma para PDFs (ES/EN)?
- [ ] Respuesta: si 

**Q27.13**: ¿Se soporta exportación masiva de datos para migración externa?
- [ ] Respuesta: si solo admin

**Q27.14**: ¿Control de acceso: quién puede generar cada tipo de reporte?
- [ ] Respuesta: el admin y pm, y cleinte 

**Q27.15**: ¿Formato CSV vs XLSX configurable?
- [ ] Respuesta: si configurable 

**Q27.16**: ¿La generación de reportes grandes es asíncrona (Celery)?
- [ ] Respuesta: si

---

## 🔗 CONEXIONES CRUZADAS CRÍTICAS

### **Preguntas de Integración**

**QI.1**: Tasks ↔ Schedule: ¿Completar tarea actualiza automáticamente el progreso del schedule item?
- [ ] Respuesta: si ejemplo actividad x en x hedulle, ejemplo actividad x = preparacion = a x10 actividades, actividad 1-10, cada. una de esas subactividades o tareas tiene un porcentaje de la tarea x ejemplo tarea x1=10%, x2=20, x3=5%, y asi el total de las actividades debe de ser 100%, asi cuando se terminen las 10 x actividades signidica que se termino esa actividad al 100%, o si se ompetaron 5 tareas 5x=60, enonces actividad x = 50% cpmpleted.

**QI.2**: Daily Plans ↔ Time Tracking: ¿Las horas reales se sincronizan automáticamente con time entries?
- [ ] Respuesta:  no ya que lospanes diarios tinene hipotesis 

**QI.3**: SOPs ↔ Daily Plans ↔ Payroll: ¿La duración de SOP afecta la estimación de costo salarial?
- [ ] Respuesta: no, 

**QI.4**: Materials ↔ Inventory ↔ Expenses: ¿Recibir material genera entrada de inventario Y gasto automáticamente?
- [ ] Respuesta: si, porque significa wue se compro algo con dinero o credito y se agergao algo al projecto, almenos que sea herrameinta, una herrameinta que ya tenemos en el storage que seria mas como traslado de storage a projecto.

**QI.5**: Inventory ↔ Budget: ¿El consumo de inventario descuenta presupuesto interno?
- [ ] Respuesta: si ejmeplo se registro que se compro una cja de tape la caja tiene 12 tapes ejem,plo la caja cueta 120= 10mpor unidad se gastaron 5 tapes entonces se gasto 50 , o de esa amenra para cada cosa y el iva se pude agergar al final, o tambein puede ser que no ya que cuando se agrega un gasto se determina que se gasto en ese prjecto y ya no es necesrio involucrar inventario 

**QI.6**: Change Orders ↔ Budget ↔ Tasks: ¿CO aprobado crea tareas nuevas automáticamente?
- [ ] Respuesta: si tareas que el amdin y pm determina si es una actividad o es una x1, x2 actidad se pude crera una categortia en el scheulle y crear multoples tareas o asi.

**QI.7**: Damage Reports ↔ Tasks: ¿Reporte de daño dispara automáticamente tarea de reparación?
- [ ] Respuesta: si al pm y admin

**QI.8**: Color Samples ↔ Client ↔ Legal: ¿La firma digital se requiere obligatoriamente y en qué formato?
- [ ] Respuesta: que puedan dibular en su telefono ipad o compuntadora y que se segistre nu nombr e ip del dispositivo

**QI.9**: Pins (Blueprints) ↔ Tasks/Damage: ¿Pin de tipo "Issue" crea automáticamente tarea o reporte?
- [ ] Respuesta: si 

**QI.10**: Cost Codes ↔ Payroll/Expenses/Time: ¿El reporte consolida costos por código automáticamente?
- [ ] Respuesta: si

**QI.11**: Earned Value ↔ Schedule ↔ Budget: ¿Cambio de fechas en schedule recalcula PV dinámicamente?
- [ ] Respuesta: si si es posble si 

**QI.12**: Automation ↔ Security: ¿Las tareas automáticas usan permisos para modificar estados?
- [ ] Respuesta: si

**QI.13**: Reports ↔ Dashboards: ¿Los widgets reutilizan lógica de generación de reportes?
- [ ] Respuesta: si

**QI.14**: Notifications ↔ All Modules: ¿Los eventos clave se centralizan (pub/sub pattern)?
- [ ] Respuesta: si

---

## 🚩 RIESGOS Y GAPS DETECTADOS

### **Validaciones Pendientes**

**R.1**: ¿La firma digital (módulos 1.7, 19, 17) está implementada o es feature pendiente?
- [ ] Estado actual: no esta implementada aun necesita crerase 

**R.2**: ¿La relación entre Tareas y Actividades Diarias está clara o genera duplicación de datos?
- [ ] Clarificación: si hay un mecanismo que pueda ser mas claro implementalo solo avisame de ello para aprovarlo para mi esta claro peor piensa que el programa sera usado por mu;ltiples mentes.

**R.3**: ¿Existe política de versionado para SOPs, Planos y Muestras de Color?
- [ ] Clarificación: si

**R.4**: Earned Value: ¿de dónde obtiene datos de cronograma y progreso exactamente?
- [ ] Mapping actual: si, cuanto tinero se piensa ganar en costos relae sy ganancias reales 

**R.5**: Seguridad: ¿el modelo de permisos por acción y por proyecto está documentado?
- [ ] Documentación existente: no esta docuemtado segun yo, si es necesario solicitamelo 

**R.6**: Automatización: ¿qué hace cada tarea Celery exactamente (outputs)?
- [ ] Definición completa: hay muchas cosas, como enviar todas las notificaicon de acciones, cmabios, ediciones, ageragr, remover, tyerminar, empear, correos, infoamcion, mensajes, ect.

**R.7**: Reportes: ¿alcance de datos y permisos de descarga están definidos?
- [ ] Definición: no aun no, la regla hasta el moento es que el cleinte , desenador, dueno , no puede ver finanzas interior ni nada del interio d ela compania en finanzas

**R.8**: Inventario/Materiales/Expenses: ¿el flujo completo está integrado o son módulos independientes?
- [ ] Estado de integración: deberia ser integrado, epro desconozco su estado actual 

---

## ✅ INSTRUCCIONES FINALES

1. **Responde en este mismo archivo** o en un documento separado
2. **Prioriza preguntas críticas** (marcadas con 🔴 en conversación previa)
3. **Agrega ejemplos** cuando ayude a clarificar
4. **Marca cambios necesarios** en la implementación actual
5. **Identifica features faltantes** que bloquean funcionalidad

Cuando completes este cuestionario, actualizaremos `REQUIREMENTS_DOCUMENTATION.md` con todas las clarificaciones y crearemos un plan de acción para implementar features pendientes.

---

**Progreso**: 0/200+ preguntas respondidas
**Fecha inicio**: Nov 19, 2025
**Completado por**: [Tu nombre]
