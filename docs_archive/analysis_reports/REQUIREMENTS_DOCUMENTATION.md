# 📋 DOCUMENTACIÓN COMPLETA DE REQUISITOS - SISTEMA KIBRAY

## 🎯 INFORMACIÓN GENERAL DEL PROYECTO

**Propósito**: Sistema integral de gestión para empresa de construcción que maneja proyectos, empleados, tiempo, finanzas, facturación, estimados, órdenes de cambio, inventario, nómina y más.

**Metodología de documentación**: Revisión función por función (250+ funcionalidades) antes de implementar cambios.

**Estado actual**: Documentación en progreso - Módulos 1-3 completados.

---

## ✅ **MÓDULO 1: GESTIÓN DE PROYECTOS** (10/10 COMPLETO)

### 📌 FUNCIÓN 1.1 - Crear Proyecto

**Flujo 1 - Desde Propuesta:**
```
Propuesta creada → Cliente aprueba estimado → Auto-crear proyecto
- Se arrastra: Cliente, presupuesto estimado, información del estimado
- Estado inicial: "created"
```

**Flujo 2 - Creación Directa:**
```
Para: Touch-ups, trabajos T&M, proyectos sin estimado previo
Admin crea directamente con información mínima
```

**Campos Requeridos:**
- Información del cliente (nombre, contacto)
- Ubicación del proyecto (dirección completa)
- Notas básicas del proyecto

**Campos Opcionales:**
- Presupuesto inicial
- Fechas estimadas
- Link a estimado (si aplica)

**Estados del Proyecto:**
```
1. created - Proyecto recién creado
2. active - Auto-activa cuando se crea primer item del schedule
3. closed - Proyecto finalizado
```

**Validaciones:**
- Nombres únicos de proyecto
- end_date debe ser mayor que start_date
- Cliente debe existir en el sistema

**Mejoras Identificadas:**
- ❌ Falta: Generación automática de número de proyecto (PRJ-001, PRJ-002...)
- ❌ Falta: Notificación al PM cuando es asignado

---

### 📌 FUNCIÓN 1.2 - Editar Proyecto

**Permisos por Rol:**

**Admin (Propietario):**
- Edita información sensible: presupuesto total, estimado vinculado, colores aprobados, cliente
- Cambios inmediatos sin aprobación

**PM (Project Manager):**
- Puede crear: Órdenes de cambio, gastos, órdenes de materiales
- Para cambios principales: Requiere aprobación del admin
- Notificación enviada cuando solicita cambio

**Restricciones en Proyecto Cerrado:**
```
Estado: closed
Permitido: Solo agregar mensajes/comunicación
Bloqueado: Cualquier edición de datos del proyecto
```

**Tracking de Cambios:**
```
Panel de seguimiento:
- Registra todos los cambios realizados
- Quién hizo el cambio
- Fecha y hora
- Qué se modificó
- Se puede compartir con cliente
```

**Mejora Identificada:**
- ✅ Implementar workflow de aprobación PM → Admin

---

### 📌 FUNCIÓN 1.3 - Ver Detalles del Proyecto

**Dashboard por Rol:**

**Admin/PM - Vista Financiera Completa:**
```
Métricas visibles:
- Ganancia total (ingresos - gastos)
- Balance actual
- Gastos vs presupuesto
- Porcentaje usado del presupuesto
- Progreso del proyecto
- Órdenes de cambio
- Todas las transacciones
```

**Foreman - Vista de Campo (FUTURO):**
```
Métricas visibles:
- Presupuestos por categoría (Ventanas: $5k, Puertas: $3k)
- NO ve presupuesto total
- NO ve ganancia
- NO ve detalles financieros internos

Propósito: Guiar el trabajo sin revelar márgenes
```

**Cliente - Vista Externa:**
```
Métricas visibles:
- Pagos realizados
- Presupuesto estimado (venta)
- Órdenes de cambio aprobadas
- Progreso general
- Tareas asignadas (puede crear tareas)

Oculto:
- Presupuesto interno
- Costos reales
- Ganancia
- Desglose de costos de mano de obra
```

**Employee - Vista Operacional:**
```
Información visible:
- Nombre del proyecto
- Dirección (para llegar)
- Tareas asignadas a él
- SOPs relacionadas
- Clock in/out para ese proyecto
- Tiempo trabajado en el proyecto
- Chat/comunicación del proyecto

Oculto:
- Cualquier información financiera
- Presupuestos
- Otros empleados (solo ve su información)
```

---

### 📌 FUNCIÓN 1.4 - Asignar Project Manager

**Configuración de Asignación:**
```
Múltiples PMs por proyecto: ✅ SÍ
  - Ejemplo: PM principal + PM asistente
  - Ambos tienen acceso completo al proyecto

Múltiples proyectos por PM: ✅ SÍ
  - Un PM puede manejar 5, 10, 20+ proyectos simultáneamente
  - Sin límite técnico
```

**Proceso de Asignación:**
```
1. Admin selecciona proyecto
2. Admin asigna uno o más PMs
3. PM obtiene acceso instantáneo
4. Notificación enviada al PM: "Has sido asignado al proyecto [Nombre]"
```

**Remover PM:**
```
Admin puede:
- Remover PM en cualquier momento
- PM pierde acceso inmediatamente
- Historial del PM se mantiene (no se borra)
```

**Historial:**
```
Sistema registra:
- Todos los PMs asignados (histórico)
- Fechas de asignación/remoción
- PM nuevo puede ver trabajo completo de PMs anteriores
```

---

### 📌 FUNCIÓN 1.5 - Estructura de Presupuesto

**Nivel 1 - Presupuesto al Cliente (Venta Total):**
```
Items de venta:
- "Pintar ventanas" → $2,000
- "Pintar puertas" → $5,000
- "Reparar techo" → $3,500

Margen ideal: 30% incluido en precio
Propósito: Lo que ve y paga el cliente
```

**Nivel 2 - Presupuesto Interno (Guía del PM):**
```
Desglose interno (NO visible al cliente):

Labor:
- Horas estimadas × $25 (costo interno)
- Ejemplo: 10 horas × $25 = $250 presupuesto interno
- Vendido al cliente: 10 horas × $50 = $500
- Margen: $250

Materiales:
- Costo real de materiales (sin markup)
- Ejemplo: Pintura $150 (costo real)
- Vendido al cliente: $165 (10% markup)
- Margen: $15

Propósito: Alertar al PM si se está excediendo tiempo/costo
```

**Categorías de Presupuesto:**
```
Divisiones principales:
- Ventanas
- Puertas
- Techos
- Paredes
- Closets
- Exterior
- Siding
- Trim
- Soffit
- Beams
- Metales

Conexión: Cada categoría vinculada a líneas de presupuesto
Tracking: Rendimiento por categoría
```

**Órdenes de Cambio - Impacto en Presupuesto:**
```
Ejemplo CO de $5,000:
1. Cliente aprueba CO → +$5,000 al presupuesto total de venta

2. Desglose interno (PM):
   Labor: 10 horas × $50 = $500 (venta) → $250 presupuesto PM ($25/h interno)
   Materiales: $300 (costo real, sin markup para PM)
   
3. Sistema suma:
   - Presupuesto cliente: +$5,000
   - Presupuesto PM: +$550 ($250 labor + $300 materiales)
```

**Alertas y Comportamiento:**
```
Cuando se excede presupuesto:
- Gráficos se ponen en ROJO
- Notificación al PM y Admin
- Proyecto NO se bloquea (continúa operando)

Razón: Reputación > Presupuesto
"Es mejor terminar el proyecto aunque perdamos un poco, 
que dejar trabajo a medias y perder el cliente"

Propósito de alertas:
- Awareness para optimizar recursos
- Identificar áreas problemáticas
- Mejorar estimados futuros
```

**Mejoras Identificadas:**
- ✅ Sistema de dos niveles ya existe
- ⚠️ Validar que gráficos se pongan rojos al exceder
- ⚠️ Confirmar notificaciones de exceso presupuestal

---

### 📌 FUNCIÓN 1.6 - Fechas del Proyecto

**Creación de Fechas:**
```
PM crea schedules y sugiere fechas:
- Fecha de inicio propuesta
- Fecha de fin estimada
- Hitos intermedios
```

**Aprobación:**
```
Admin revisa:
- Aprueba fechas → Estado: "approved"
- Publica calendario
- Notificación enviada a TODOS los usuarios:
  "El schedule del proyecto [Nombre] está disponible"
```

**Visibilidad:**
```
Antes de aprobación: Solo PM y Admin ven
Después de aprobación: Todos los usuarios asignados pueden ver
```

---

### 📌 FUNCIÓN 1.7 - Gestión de Colores

**Flujo 1 - Cliente/Designer Solicita Color:**
```
1. Cliente o Designer pide color específico o match
2. Admin crea múltiples muestras de color
3. Estado inicial: "En revisión"
4. Cliente/Designer revisa muestras:

   Opción A - Aprobar:
   ├─ Firma digital del cliente/designer (LEGAL)
   ├─ Color guardado al proyecto
   └─ Registro permanente

   Opción B - Rechazar:
   ├─ Firma digital del cliente/designer (LEGAL)
   ├─ Muestra eliminada
   └─ Razón de rechazo registrada

   Opción C - Solicitar Cambios:
   ├─ Admin ajusta color
   ├─ Reenvía para revisión
   └─ Repite proceso
```

**Flujo 2 - Designer Envía Color:**
```
1. Designer crea color con información completa:
   - Nombre del color
   - Código de color
   - Marca
   - Ubicación de aplicación
   - Notas

2. Admin recibe notificación
3. Admin puede:
   - Hacer preguntas/aclaraciones
   - Aprobar → Color guardado
   - Rechazar → Color eliminado
```

**Importancia de Firmas Digitales:**
```
Propósito LEGAL:
- Cliente firmó aprobación de color X
- Evidencia en caso de disputa
- "El cliente aprobó este color el [fecha] a las [hora]"
- Protección legal para la empresa

Rechazos también requieren firma:
- Evidencia de que cliente rechazó opción
- Documentación de decisiones del proyecto
```

**Mejora Crítica Identificada:**
- ❌ FALTA: Sistema de firma digital para aprobaciones de color
- 🔴 PRIORIDAD ALTA - Protección legal

---

### 📌 FUNCIÓN 1.8 - Cálculo de Ganancia

**Fórmula:**
```
Ganancia = Total Ingresos - Total Gastos

Desglose:
Ingresos incluyen:
- Pagos del cliente
- Órdenes de cambio pagadas
- Cualquier ingreso vinculado al proyecto

Gastos incluyen:
- Materiales
- Mano de obra (horas × tarifa)
- Equipos
- Permisos
- Subcontratistas
- Cualquier expense vinculado al proyecto
```

**Visibilidad:**
```
Pueden ver ganancia:
- Admin ✅
- PM ✅

NO pueden ver ganancia:
- Cliente ❌
- Employee ❌
- Designer ❌
- Foreman ❌
```

**Actualización:**
```
Se recalcula automáticamente cuando:
- Se registra nuevo ingreso
- Se registra nuevo gasto
- Se edita/elimina ingreso o gasto
- Se aprueba orden de cambio
```

---

### 📌 FUNCIÓN 1.9 - Presupuesto Restante

**Cálculo:**
```
Presupuesto Restante = Presupuesto Total - Gastos Reales

Ejemplo:
Presupuesto: $50,000
Gastos hasta hoy: $32,000
Restante: $18,000 (36% del presupuesto)
```

**Alertas:**
```
Sistema muestra alertas cuando:
- Restante < 20% del presupuesto → Alerta amarilla
- Restante < 10% → Alerta naranja
- Restante < 0% (excedido) → Alerta roja

Métricas adicionales:
- Porcentaje usado
- Proyección de gasto al ritmo actual
- Comparación con progreso del proyecto
```

**Visibilidad:**
```
Pueden ver:
- Admin: Presupuesto completo (venta + interno)
- PM: Presupuesto completo (venta + interno)
- Foreman: Solo categorías individuales (futuro)
- Cliente: Solo presupuesto de venta
- Employee: Nada
```

---

### 📌 FUNCIÓN 1.10 - Dashboard del Proyecto

**Propósito:**
```
Panel centralizado con acceso rápido a todas las funciones del proyecto
según el rol del usuario
```

**Funcionalidad por Rol:**
```
Admin:
- Acceso a TODO
- Métricas financieras completas
- Edición sin restricciones

PM:
- Acceso operacional completo
- Métricas financieras completas
- Algunas ediciones requieren aprobación

Foreman:
- Acceso a operaciones de campo
- Presupuestos por categoría
- Sin acceso financiero

Employee:
- Solo información de sus tareas
- Clock in/out
- Ver SOPs y comunicación

Cliente:
- Vista externa
- Progreso y pagos
- Sin información interna
```

**Métricas Centralizadas:**
```
- Status del proyecto
- Progreso general
- Alertas activas
- Tareas pendientes
- Próximos hitos
- Acceso rápido a módulos
```

---

## ✅ **MÓDULO 2: GESTIÓN DE EMPLEADOS** (8/8 COMPLETO)

### 📌 FUNCIÓN 2.1 - Registrar Empleado

**Flujo PM Registra Empleado:**
```
1. PM crea empleado en el sistema
2. Estado automático: "Pendiente aprobación"
3. Admin recibe notificación
4. Admin revisa información:
   
   Opción A - Aprobar:
   ├─ Admin crea usuario + contraseña
   ├─ Asigna rol (Employee, Foreman)
   ├─ Empleado recibe credenciales
   └─ Empleado puede hacer login

   Opción B - Rechazar:
   └─ Registro eliminado o marcado como rechazado
```

**Flujo Admin Registra Directamente:**
```
1. Admin crea empleado
2. Admin crea usuario en mismo paso
3. Sin aprobación necesaria
4. Acceso inmediato
```

**Campos Requeridos:**
```
- Nombre completo
- Email
- SSN (Social Security Number)
- Tarifa por hora ($25, $30, etc.)
- Contacto de emergencia
```

**Campos Opcionales:**
```
- Dirección
- Teléfono
- Notas
- Documentos (W9, ID, etc.)
```

**Gestión de Estado:**
```
Toggle Activo/Inactivo:
- Activo: Empleado puede trabajar, clock in/out, ver información
- Inactivo: REMUEVE TODO ACCESO
  ├─ No puede hacer login
  ├─ No aparece en asignaciones
  ├─ Mantiene historial (no se borra)
  └─ Se puede reactivar después
```

**Sin Límite:**
```
- Cantidad de empleados: Ilimitada
- Propósito: Escalar según necesidades de la empresa
```

**Mejora Identificada:**
- ✅ Workflow de aprobación PM → Admin implementar

---

### 📌 FUNCIÓN 2.2 - Editar Empleado

**Permisos de Edición:**

**PM edita:**
```
1. PM hace cambios a información del empleado
2. Sistema marca edición como "Pendiente aprobación"
3. Admin recibe notificación
4. Admin aprueba → Cambios aplicados
5. Admin rechaza → Cambios descartados
```

**Admin edita:**
```
1. Admin hace cambios
2. Aplicación inmediata (sin aprobación)
3. Cambios registrados en historial
```

**Campos Editables:**
```
SSN: ✅ Editable (no es permanente como employee_key)
- Razón: Errores en captura inicial
- Requiere aprobación admin siempre

Otros campos:
- Nombre
- Email
- Teléfono
- Dirección
- Tarifa (ver función 2.3)
- Contacto de emergencia
```

**Mejora CRÍTICA Identificada:**
```
❌ FALTA: Employee Key System

Propuesta:
- Campo: employee_key (EMP-001, EMP-002, EMP-003...)
- Generación: Automática al crear empleado
- Inmutable: NUNCA cambia (incluso si empleado sale y regresa)
- Propósito: Identificador único permanente

Razones:
1. SSN es sensible (no usar como ID principal)
2. Nombres pueden cambiar
3. Necesario para reportes históricos
4. Estándar en sistemas enterprise

Ejemplo de uso:
- Nómina histórica
- Reportes de rendimiento
- Auditorías
- Referencias cruzadas entre módulos
```

---

### 📌 FUNCIÓN 2.3 - Tarifa por Hora

**Configuración de Tarifa:**
```
Una tarifa por empleado: ✅ SÍ
- NO varía por proyecto
- Aplica a todos los proyectos donde trabaje
- Simplifica nómina

Ejemplo:
Juan Pérez: $25/hora
- Trabaja en Proyecto A → $25/hora
- Trabaja en Proyecto B → $25/hora
- Trabaja en Proyecto C → $25/hora
```

**Cambios de Tarifa:**
```
Siempre requieren aprobación de Admin:

PM solicita aumento:
1. PM propone nueva tarifa + razón
2. Admin recibe notificación
3. Admin aprueba → Tarifa actualizada
4. Admin rechaza → Tarifa permanece igual

Admin cambia:
- Directo, sin aprobación adicional
```

**Aumentos Temporales:**
```
Escenario: "Esta semana +$1 por buen desempeño"

Implementación:
1. Admin aumenta tarifa de $25 → $26
2. Sistema registra en historial
3. Nómina de esa semana calcula con $26
4. Siguiente semana: Admin puede regresar a $25

Auto-update en nómina:
- Payroll lee tarifa actual al momento de calcular
- No requiere ajustes manuales
```

**Historial de Cambios:**
```
Sistema registra:
- Fecha del cambio
- Tarifa anterior
- Tarifa nueva
- Quién hizo el cambio
- Razón del cambio

Ejemplo de historial:
| Fecha      | De  | A   | Por     | Razón                    |
|------------|-----|-----|---------|--------------------------|
| 2024-01-15 | $23 | $25 | Admin   | Aumento anual            |
| 2024-06-10 | $25 | $26 | Admin   | Bonus temporal semana    |
| 2024-06-17 | $26 | $25 | Admin   | Fin de bonus temporal    |
| 2024-10-01 | $25 | $27 | PM/Admin| Promoción a Lead Painter |
```

**Impacto en Time Entries:**
```
NO afecta entradas pasadas:
- Time entry del 1 de mayo con $25 → Se mantiene en $25
- Cambio de tarifa el 15 de mayo a $27 → Solo afecta entries DESPUÉS del 15
- Razón: Preservar exactitud histórica de costos
```

**Validación:**
```
Regla crítica:
- Tarifa interna NUNCA debe ser >= tarifa de venta

Ejemplo:
- Tarifa interna empleado: $25/h ✅
- Tarifa de venta al cliente: $50/h ✅
- Margen: $25/h (50%)

Validación en sistema:
IF tarifa_interna >= tarifa_venta:
  → ERROR: "Tarifa interna debe ser menor que tarifa de venta"
  → Bloquear guardado
```

---

### 📌 FUNCIÓN 2.4 - Posición/Rol del Empleado

**Jerarquía de Posiciones:**
```
1. Admin (Owner)
   ├─ Acceso: TODO el sistema
   ├─ Finanzas: Completo
   ├─ Aprobaciones: Todas
   └─ Edición: Sin restricciones

2. PM (Project Manager)
   ├─ Acceso: Proyectos asignados
   ├─ Finanzas: Ve todo, edita con aprobación
   ├─ Gestión: Empleados, materiales, schedules
   └─ Confianza: Alto nivel

3. Foreman (Supervisor de Campo)
   ├─ Acceso: Operaciones de campo
   ├─ Finanzas: NINGUNA (ni presupuesto total)
   ├─ Ve: Presupuestos por categoría (guía de trabajo)
   ├─ Gestión: Asignaciones diarias de empleados
   └─ Temporal: Puede ser promovido a PM

4. Employee (Trabajador)
   ├─ Acceso: Solo su información
   ├─ Funciones: Clock in/out, ver tareas, chat
   ├─ Finanzas: NINGUNA
   └─ Ve: Proyecto asignado, dirección, SOPs
```

**Trades (Oficios):**
```
Especialidades:
- Carpintero (Carpenter)
- Electricista (Electrician)
- Plomero (Plumber)
- Pintor (Painter)
- Albañil (Mason)
- Ayudante (Helper/Laborer)
- Instalador de Pisos (Flooring Installer)
- Techador (Roofer)
- HVAC Technician
- Soldador (Welder)
```

**Rol como Barrera de Seguridad:**
```
Posición define:
- Qué puede VER
- Qué puede EDITAR
- Qué puede APROBAR
- Qué NOTIFICACIONES recibe

Ejemplo - Foreman:
- ✅ Ve: "Presupuesto Ventanas: $5,000"
- ❌ NO ve: "Presupuesto total: $50,000"
- ❌ NO ve: "Ganancia: $15,000"
- ✅ Ve: "Horas trabajadas por equipo"
- ❌ NO ve: "Costo de nómina"

Razón: Información necesaria para el trabajo SIN revelar márgenes
```

**Promociones:**
```
Foreman → PM:
1. Admin cambia rol
2. Acceso financiero se activa automáticamente
3. Puede ver proyectos completos
4. Recibe notificaciones de PM
```

---

### 📌 FUNCIÓN 2.5 - Activar/Desactivar Empleados

**Ya documentado en Función 2.1**

---

### 📌 FUNCIÓN 2.6 - Historial de Trabajo (Vista del Empleado)

**Vista Semanal:**
```
Información que ve el empleado:

Por semana:
├─ Proyecto(s) trabajado(s)
├─ Horas por día:
│  ├─ Lunes: 8:00 AM - 5:00 PM (8.5h)
│  ├─ Martes: 7:30 AM - 4:30 PM (8.5h)
│  ├─ Miércoles: 8:00 AM - 12:00 PM (4h)
│  └─ ...
├─ Total de horas semanales
├─ Pago esperado = Horas × Tarifa
└─ Estado de pago: Pagado / Pendiente
```

**Lógica de Deducción de Almuerzo:**
```
Regla actualizada:
IF horas_trabajadas >= 5 AND trabajó_después_de_12pm:
  → Deducir 30 minutos

Ejemplos:

Caso 1: 8:00 AM - 12:00 PM (4 horas)
- Horas: 4h
- Pasó las 12 PM: NO
- Deducción: NO
- Horas pagadas: 4h ✅

Caso 2: 8:00 AM - 1:00 PM (5 horas)
- Horas: 5h
- Pasó las 12 PM: SÍ
- Trabajó durante almuerzo: Posible
- Deducción: SÍ
- Horas pagadas: 4.5h ✅

Caso 3: 1:00 PM - 6:00 PM (5 horas)
- Horas: 5h
- Pasó las 12 PM: SÍ (empezó después)
- Deducción: SÍ
- Horas pagadas: 4.5h ✅

Caso 4: 8:00 AM - 5:00 PM (9 horas)
- Horas: 9h
- Pasó las 12 PM: SÍ
- Deducción: SÍ (30 min)
- Horas pagadas: 8.5h ✅
```

**Razón de la Lógica:**
```
Objetivo: Deducir almuerzo solo en jornadas reales de trabajo

≥ 5 horas: Jornada suficientemente larga para ameritar almuerzo
Y trabajó pasado 12 PM: Indica que trabajó durante horario de almuerzo típico

Evita deducciones incorrectas:
- 4 horas en la mañana → No deducir (trabajo corto)
- 8 horas continuas → Deducir (jornada completa)
```

**Mejora Identificada:**
- ✅ Refinamiento de lógica de almuerzo (≥5h AND >12PM)
- ⚠️ Implementar en TimeEntry.save() method

---

### 📌 FUNCIÓN 2.7 - Vincular Empleado con Usuario

**Proceso:**
```
Después de aprobar empleado (ver 2.1):

1. Admin crea usuario:
   ├─ Username (email o custom)
   ├─ Password (temporal, cambiar en primer login)
   ├─ Vincula con registro de Employee
   └─ Asigna permisos según rol

2. Sistema envía credenciales:
   ├─ Email con username y password
   ├─ Link al sistema
   └─ Instrucciones de primer login

3. Empleado hace primer login:
   ├─ Cambia password (forzoso)
   ├─ Acepta términos (si aplica)
   └─ Accede a su dashboard
```

**Vinculación Técnica:**
```
Modelo:
- Employee (registro de empleado)
- User (autenticación Django)
- Profile (extensión con rol y preferencias)

Relación:
Employee.user → User
User.profile → Profile
```

---

### 📌 FUNCIÓN 2.8 - Documentos del Empleado

**Tipos de Documentos:**
```
Documentos comunes:
- W9 (Tax form)
- Formularios gubernamentales
- Copia de ID/Licencia
- Certificaciones (si aplica)
- Contratos firmados
```

**Gestión:**
```
Quién puede subir:
- PM: ✅ (requiere aprobación para ciertos docs)
- Admin: ✅ (sin restricciones)

Enfoque minimalista:
- Solo documentos esenciales
- Sin archivo excesivo de papeles
- Fácil acceso cuando se necesita
```

**Almacenamiento:**
```
- Archivos en servidor seguro
- Acceso restringido (solo Admin/PM)
- Vinculados al registro del empleado
- Se mantienen aunque empleado esté inactivo
```

---

## ✅ **MÓDULO 3: TIME TRACKING (REGISTRO DE TIEMPO)** (10/10 COMPLETO)

### 📌 FUNCIÓN 3.1 - Registro de Entrada de Tiempo (Clock In/Out)

**Prerequisitos:**
```
REQUERIMIENTO CRÍTICO:
- PM debe asignar empleado a proyecto
- Asignación puede ser:
  ├─ Día anterior (planificación)
  └─ Mañana del mismo día

Sin asignación:
- Botón muestra: "No estás asignado a un proyecto"
- Clock in BLOQUEADO
```

**Flujo de Clock In:**
```
1. Empleado abre app
2. Sistema detecta:
   - ¿Empleado asignado a proyecto hoy? → Verificar
   
3. Si asignado:
   ├─ App auto-detecta proyecto asignado
   ├─ Muestra: "Proyecto: Villa Moderna"
   ├─ Botón: "Clock In" habilitado
   └─ Click → Registra hora actual + proyecto

4. Si NO asignado:
   ├─ Muestra: "No estás asignado a un proyecto"
   ├─ Botón: "Clock In" deshabilitado
   └─ Mensaje: "Contacta a tu supervisor"
```

**Trabajo en Múltiples Proyectos:**
```
Escenario: Empleado puede trabajar varios proyectos mismo día

Ejemplo:
8:00 AM - 12:00 PM → Proyecto A (Villa Moderna)
12:00 PM - 5:00 PM → Proyecto B (Casa Residencial)

Proceso:
1. Clock in Proyecto A (8:00 AM)
2. Trabajando en A...
3. Mediodía: Click "Cambiar de proyecto"
4. Selecciona Proyecto B
5. Tiempo NO se detiene, solo cambia destino
6. Time entry de A se cierra (8:00-12:00)
7. Time entry de B se abre (12:00-...)
8. Clock out final cierra entry de B
```

**Cambio a Orden de Cambio (CO):**
```
Escenario especial (tu pregunta actual):

Empleado trabajando en Proyecto X:
1. PM le pide trabajar en CO dentro de Proyecto X
2. CO ya fue asignado correctamente por PM
3. Empleado en app:
   ├─ Click "Cambiar de proyecto"
   ├─ Ve opciones:
   │  ├─ Proyecto X (principal)
   │  └─ CO-001 Proyecto X (orden de cambio)
   ├─ Selecciona: "CO-001 Proyecto X"
   └─ Tiempo cambia a CO

4. Empleado trabaja en CO...
5. Termina antes de check out
6. Click "Cambiar de proyecto" nuevamente
7. Regresa a "Proyecto X" (principal)
8. Continúa trabajando hasta clock out

Resultado:
- Entry 1: Proyecto X (8:00-10:00) = 2h
- Entry 2: CO-001 Proyecto X (10:00-11:30) = 1.5h
- Entry 3: Proyecto X (11:30-5:00) = 5.5h
- Total del día: 9h (con deducción de almuerzo = 8.5h)
```

**Flujo de Clock Out:**
```
1. Empleado click "Clock Out"
2. Sistema registra hora actual
3. Calcula horas automáticamente
4. Aplica deducción de almuerzo (si aplica)
5. Time entry marcado como completo
```

**Restricción de Horario:**
```
Límite: 10:00 PM

Si empleado NO hace clock out antes de 10 PM:
1. 10:00 PM → Sistema detecta
2. Envía notificaciones:
   ├─ Al empleado: "Registra tu salida o haz check out"
   └─ Al PM: "Empleado [Nombre] no ha hecho clock out"
3. Empleado debe:
   ├─ Hacer clock out inmediatamente, O
   └─ Enviar solicitud de corrección (ver 3.2)

Razón del límite:
- Evitar olvidos de todo el día
- Mantener datos limpios
- Detectar problemas temprano
```

**Mejoras Identificadas:**
- ✅ Validación de asignación antes de clock in
- ✅ Sistema de cambio de proyecto sin detener tiempo
- ✅ Notificaciones automáticas a las 10 PM
- ⚠️ Validación de ubicación (empleado cerca del proyecto) - FUTURO

---

### 📌 FUNCIÓN 3.2 - Calcular Horas Trabajadas Automáticamente

**Cálculo Base:**
```
Horas = Clock Out Time - Clock In Time

Ejemplo:
Clock In: 8:00 AM
Clock Out: 5:00 PM
Horas brutas: 9 horas
```

**Con Deducción de Almuerzo:**
```
Ver función 3.3 y 2.6 para lógica completa

Fórmula final:
IF horas >= 5 AND trabajó_después_de_12pm:
  horas_pagadas = horas_brutas - 0.5
ELSE:
  horas_pagadas = horas_brutas
```

**Actualización Automática:**
```
Trigger: TimeEntry.save()
1. Calcula horas
2. Aplica deducción si necesario
3. Guarda en campo hours_worked
4. Calcula costo (hours × employee.hourly_rate)
```

---

### 📌 FUNCIÓN 3.3 - Deducción Automática de Almuerzo

**Ya completamente documentado en Función 2.6**

Resumen:
- IF horas >= 5 AND pasó 12:00 PM → Deducir 30 min
- Automático en TimeEntry.save()
- Visible en historial del empleado

---

### 📌 FUNCIÓN 3.4 - Asignar Tiempo a Proyecto Específico

**Ya documentado en Función 3.1**

Puntos clave:
- PM asigna empleado a proyecto
- Auto-detección en clock in
- Sin asignación = no puede clock in

---

### 📌 FUNCIÓN 3.5 - Asignar Tiempo a Orden de Cambio

**Completamente documentado en Función 3.1 - Cambio a CO**

Resumen:
```
Flujo:
1. PM asigna CO al empleado (prerequisito)
2. Empleado ve CO en lista de "proyectos"
3. Empleado hace switch de Proyecto → CO
4. Tiempo se registra en CO
5. Puede regresar a proyecto principal cuando termine
6. Sin límite de switches

Asignación:
- PM asigna CO correctamente desde dashboard
- Empleado NO asigna manualmente
- CO aparece como opción solo si está asignado
```

---

### 📌 FUNCIÓN 3.6 - Agregar Notas a la Entrada

**Uso de Notas:**
```
Caso normal (clock in diario):
- Empleado NO agrega notas
- Simplemente hace clock in/out
- Sistema registra tiempo automáticamente

Caso especial (request de modificación):
- Empleado olvidó clock out
- Empleado se equivocó de hora
- Empleado tuvo problema técnico
- En estos casos: Envía "solicitud de corrección"
```

**Solicitud de Corrección (Ver Función 3.10 completa):**
```
Empleado escribe:
"Entré a las 7:30 AM y salí a las 4:00 PM.
Razón: Olvidé hacer clock out porque tuve emergencia familiar"

PM revisa → Aprueba
Admin notificado → Aprueba
Sistema aplica corrección
```

**Notas Administrativas:**
```
PM o Admin pueden agregar notas:
- "Empleado trabajó tiempo extra aprobado"
- "Día festivo - tarifa 1.5x"
- "Training day"

Propósito:
- Contexto para payroll
- Documentación de excepciones
- Auditoría
```

---

### 📌 FUNCIÓN 3.7 - Calcular Costo de Mano de Obra

**Cálculo Automático:**
```
Por Time Entry:
Costo = Hours Worked × Employee Hourly Rate

Ejemplo:
- Empleado: Juan Pérez
- Tarifa: $25/hora
- Horas trabajadas: 8.5h (después de deducción almuerzo)
- Costo: 8.5 × $25 = $212.50
```

**Agregación por Proyecto:**
```
Costo Total de Labor del Proyecto =
  SUM(todas las time entries del proyecto)

Ejemplo Proyecto Villa Moderna:
- Juan: 40h × $25 = $1,000
- María: 35h × $27 = $945
- Pedro: 30h × $23 = $690
- Total Labor: $2,635
```

**Uso en Presupuesto:**
```
Comparación:
- Presupuesto Labor (interno): $3,000
- Labor Real: $2,635
- Restante: $365 ✅
- Porcentaje usado: 87.8%

Si excede:
- Gráfico en ROJO
- Alerta al PM
- Proyecto continúa (no se bloquea)
```

**Actualización:**
```
Tiempo real:
- Cada vez que empleado hace clock out
- Cada vez que se aprueba corrección
- Dashboard se actualiza inmediatamente
```

---

### 📌 FUNCIÓN 3.8 - Ver Entradas por Empleado

**Permisos de Vista:**
```
PM puede ver:
- ✅ Horas de TODOS los empleados
- ✅ Todos los proyectos
- ✅ Time entries completos
- ✅ Puede filtrar por empleado

Admin puede ver:
- ✅ TODO (igual que PM)
- ✅ Sin restricciones

Empleado puede ver:
- ✅ Solo SUS propias horas
- ❌ NO ve otros empleados
- ✅ Ve sus proyectos trabajados
```

**Vista del Empleado:**
```
Pantalla "Mis Horas":
- Semana actual
- Semanas anteriores
- Por proyecto
- Total de horas
- Pago esperado
- Estado de pago
```

**Vista PM/Admin:**
```
Pantalla "Time Entries por Empleado":

Filtros disponibles:
├─ Por empleado (dropdown)
├─ Por rango de fechas
│  ├─ Esta semana
│  ├─ Semana pasada
│  ├─ Este mes
│  └─ Rango personalizado
├─ Por proyecto
└─ Por estado
   ├─ Aprobado
   ├─ Pendiente corrección
   └─ Todos

Vista de tabla:
| Empleado | Proyecto | Fecha | Entrada | Salida | Horas | Costo |
|----------|----------|-------|---------|--------|-------|-------|
| Juan P.  | Villa M. | 11/10 | 8:00 AM | 5:00PM | 8.5h  | $212  |
| María G. | Casa Res.| 11/10 | 7:30 AM | 4:00PM | 8.0h  | $216  |
```

**Edición:**
```
Solo Admin puede editar directamente:
- Click en time entry
- Modificar horas
- Cambio inmediato

PM quiere editar:
1. PM solicita cambio
2. Notificación a Admin
3. Admin aprueba → Cambio aplicado
```

---

### 📌 FUNCIÓN 3.9 - Ver Entradas por Proyecto

**Dashboard del Proyecto - Time Tracking:**
```
Vista disponible para PM/Admin:

Todas las entradas del proyecto:
- Ordenadas por fecha (más reciente primero)
- Agrupadas por empleado (opcional)
- Agrupadas por semana (opcional)

Métricas visibles:
├─ Total horas del proyecto
├─ Total costo de labor
├─ Horas esta semana
├─ Horas vs presupuesto labor
└─ Empleados activos
```

**Filtros Disponibles:**
```
1. Por Fechas:
   ├─ Hoy
   ├─ Esta semana
   ├─ Este mes
   ├─ Rango personalizado (de/hasta)
   └─ Todo el proyecto

2. Por Empleados:
   ├─ Todos los empleados
   ├─ Empleado específico (dropdown)
   └─ Solo empleados activos

3. Por Estado:
   ├─ Aprobados
   ├─ Pendientes de corrección
   ├─ Con alertas (ej: >10PM)
   └─ Todos

4. Por CO (Orden de Cambio):
   ├─ Solo proyecto principal
   ├─ Solo CO específico
   └─ Todos (proyecto + COs)
```

**Tabla de Entradas:**
```
| Fecha  | Empleado | Proyecto/CO | Entrada | Salida  | Horas | Costo | Estado  | Acciones |
|--------|----------|-------------|---------|---------|-------|-------|---------|----------|
| 11/10  | Juan P.  | Villa M.    | 8:00 AM | 5:00 PM | 8.5h  | $212  | ✅      | Ver/Edit |
| 11/10  | Juan P.  | CO-001      | 10:00 AM| 11:30 AM| 1.5h  | $37   | ✅      | Ver/Edit |
| 11/10  | María G. | Villa M.    | 7:30 AM | 4:00 PM | 8.0h  | $216  | ⚠️      | Ver/Edit |

Estados:
✅ Aprobado
⚠️ Pendiente corrección
🔴 Alerta (no clock out)
```

**Exportar:**
```
Opciones de export:
- CSV (para Excel)
- PDF (reporte)
- Filtros se mantienen en export
```

**Mejora Identificada:**
- ✅ Filtros múltiples combinables
- ✅ Vista clara del tiempo por CO vs proyecto principal
- ⚠️ Implementar interface de filtros en template

---

### 📌 FUNCIÓN 3.10 - Editar/Corregir Entradas Existentes

**Solicitud de Corrección por Empleado:**
```
Escenarios comunes:
1. Olvidó hacer clock out
2. Entró antes/salió después de lo registrado
3. Falla técnica de la app
4. Trabajó sin señal (no pudo clock in)

Proceso:
1. Empleado va a "Mis Horas"
2. Selecciona entrada a corregir
3. Click "Solicitar corrección"
4. Formulario:
   ├─ Hora de entrada correcta
   ├─ Hora de salida correcta
   └─ Razón (texto libre):
      "Entré a las 7:00 AM y salí a las 6:00 PM.
       Olvidé hacer clock out porque tuve que salir
       rápidamente por emergencia familiar."
5. Submit
```

**Cadena de Aprobación:**
```
Aprobación Dual (PM → Admin):

Paso 1 - PM:
├─ Recibe notificación
├─ Revisa solicitud
├─ Verifica con el empleado si necesario
└─ Decisión:
   ├─ Aprobar → Pasa a Admin
   └─ Rechazar → Empleado notificado

Paso 2 - Admin:
├─ Recibe notificación (solo si PM aprobó)
├─ Revisión final
└─ Decisión:
   ├─ Aprobar → Cambio aplicado
   └─ Rechazar → Vuelve a estado original

Resultado:
- Si ambos aprueban: Time entry actualizado
- Si cualquiera rechaza: Permanece original
```

**Edición Directa (Solo Admin):**
```
Admin puede:
1. Ir a time entry
2. Click "Editar"
3. Modificar:
   ├─ Fecha
   ├─ Hora entrada
   ├─ Hora salida
   ├─ Proyecto/CO
   ├─ Empleado (si error de asignación)
   └─ Notas
4. Save → Aplicación inmediata

Registro:
- Sistema registra quién editó
- Fecha de edición
- Valores anteriores (historial)
```

**PM Quiere Editar:**
```
Proceso:
1. PM identifica error en time entry
2. PM solicita corrección a Admin (no puede editar directo)
3. Admin recibe notificación
4. Admin revisa
5. Admin aprueba → PM notificado
6. Cambio aplicado
```

**Historial de Cambios:**
```
Cada time entry mantiene log:

Ejemplo:
Original:
- Creado: 11/10/2024 8:00 AM por Juan Pérez (auto)
- Horas: 8:00 AM - 5:00 PM (8.5h)

Corrección 1:
- Solicitado: 11/11/2024 por Juan Pérez
- Razón: "Olvidé clock out"
- Aprobado por PM: María González 11/11 10:30 AM
- Aprobado por Admin: Carlos Admin 11/11 2:00 PM
- Cambio: 8:00 AM - 6:00 PM (9.5h)

Edición Admin:
- Editado: 11/12/2024 por Carlos Admin
- Razón: "Corrección de proyecto"
- Cambio: Proyecto A → CO-001
```

**Restricciones:**
```
No se puede editar:
- Time entries de nómina ya pagada (locked)
- Entries de hace más de X días (configurable)
- Entries en disputa legal

Se puede editar con aprobación:
- Cualquier entry reciente
- Entries de nómina pendiente
```

**Mejoras Identificadas:**
- ✅ Sistema de doble aprobación (PM → Admin)
- ✅ Historial completo de cambios
- ✅ Razones obligatorias para correcciones
- ⚠️ Lock de entries después de payroll processed
- ⚠️ Notificaciones automáticas en cada paso

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULOS 1-3**

### Módulo 1 - Proyectos:
1. ❌ Sistema de número de proyecto automático (PRJ-001...)
2. ❌ Notificaciones de asignación de PM
3. 🔴 **CRÍTICO**: Sistema de firma digital para colores (legal)
4. ⚠️ Workflow de aprobación PM → Admin para cambios sensibles

### Módulo 2 - Empleados:
1. 🔴 **CRÍTICO**: Employee Key system (EMP-001) - identificador inmutable
2. ✅ Workflow de aprobación PM → Admin (employee registration)
3. ✅ Historial de cambios de tarifa
4. ✅ Refinamiento de lógica de almuerzo (≥5h AND >12PM)

### Módulo 3 - Time Tracking:
1. ✅ Validación de asignación antes de clock in
2. ✅ Sistema de cambio de proyecto/CO sin detener tiempo
3. ✅ Límite de 10:00 PM con notificaciones automáticas
4. ✅ Sistema de correcciones con doble aprobación (PM → Admin)
5. ⚠️ **FUTURO**: Validación de ubicación (GPS - empleado cerca del proyecto)
6. ⚠️ Lock de time entries después de payroll processed
7. ✅ Filtros avanzados en vistas de time entries
8. ✅ Historial completo de cambios en cada entry

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)

**Total documentado: 28/250+ funciones (11%)**

**Pendientes:**
- ⏳ Módulo 4: Gastos (10 funciones)
- ⏳ Módulo 5: Ingresos (10 funciones)
- ⏳ Módulo 6: Facturación (14 funciones) - CRÍTICO
- ⏳ Módulo 7: Estimados (10 funciones)
- ⏳ Módulo 8: Órdenes de Cambio (11 funciones)
- ⏳ Módulo 9: Presupuesto/Earned Value (14 funciones) - CRÍTICO
- ⏳ Módulos 10-27: 170+ funciones

---

## 🔄 **PRÓXIMOS PASOS**

**Continuar documentación sistemática:**
1. Módulo 4 - Gastos (10 funciones)
2. Módulo 5 - Ingresos (10 funciones)
3. Módulo 6 - Facturación (14 funciones)
4. Módulo 7 - Estimados (10 funciones)
5. Módulo 8 - Change Orders (11 funciones)

**Después de completar documentación:**
- Implementar mejoras identificadas
- Crear migraciones necesarias
- Actualizar views y forms
- Testing completo
- Deployment

---

## ✅ **MÓDULO 4: GESTIÓN FINANCIERA - GASTOS** (10/10 COMPLETO)

### 🏗️ **ESTRUCTURA FINANCIERA DE LA EMPRESA**

**Concepto Crítico - Dos Niveles de Gastos:**

```
NIVEL 1 - GASTOS DEL PROYECTO (Direct Costs):
├─ Materiales del proyecto
├─ Labor del proyecto (horas trabajadas)
└─ Estos SE COBRAN al cliente

NIVEL 2 - GASTOS GENERALES DE LA EMPRESA (Overhead):
├─ Maquinaria (compra, reparación)
├─ Vehículos (compra, mantenimiento)
├─ Seguros
├─ Software
├─ Oficina (renta, utilities)
├─ Equipos
├─ Rentals
└─ Estos SE DEDUCEN del fondo general de la compañía
```

**Flujo Financiero:**
```
Por Proyecto:
1. Cliente paga → Ingresos del proyecto
2. Se compra material + se paga labor → Gastos del proyecto
3. Ganancia del proyecto = Ingresos - (Material + Labor)
4. Ganancia del proyecto → Va al FONDO GENERAL de la compañía

Fondo General (Company-Wide):
1. Suma de todas las ganancias de proyectos
2. De este fondo se deducen gastos generales:
   - Maquinaria
   - Vehículos
   - Seguros
   - Software
   - Oficina
   - Equipos
   - etc.

Resultado final:
Ganancia Neta Empresa = Fondo General - Gastos Generales
```

**Visibilidad:**
```
Admin ve:
- ✅ Gastos de cada proyecto (material + labor)
- ✅ Ganancia por proyecto
- ✅ Fondo general de la compañía
- ✅ Gastos generales (overhead)
- ✅ Ganancia neta de la empresa

PM ve:
- ✅ Gastos de SUS proyectos (material + labor)
- ✅ Ganancia de SUS proyectos
- ❌ NO ve fondo general
- ❌ NO ve gastos generales de la empresa
- ❌ NO ve ganancia neta de la empresa

Razón: Información sensible de nivel empresa solo para Owner/Admin
```

---

### 📌 FUNCIÓN 4.1 - Registrar Nuevo Gasto

**Creación de Gastos:**

**PM crea gasto:**
```
Proceso:
1. PM va al proyecto
2. Click "Agregar gasto"
3. Completa formulario:
   ├─ Categoría (Material, Labor, etc.)
   ├─ Monto
   ├─ Descripción
   ├─ Fecha del gasto
   ├─ Upload recibo (opcional pero recomendado)
   └─ Proyecto (auto-asignado al proyecto actual)
4. Submit

Aprobación: ❌ NO REQUIERE
- Gasto se registra inmediatamente
- Se suma al total de gastos del proyecto
- Afecta presupuesto instantáneamente

Razón: "Es lo que se gastó y es ello"
```

**Admin crea gasto:**
```
Dos tipos:

Tipo 1 - Gasto de Proyecto:
- Igual que PM
- Sin aprobación necesaria
- Afecta proyecto específico

Tipo 2 - Gasto General de Empresa:
- Categorías: Oficina, Maquinaria, Seguros, Software, etc.
- NO asignado a proyecto
- Va a "Gastos Generales"
- Solo Admin puede crear estos
- Se deducen del fondo general
```

**Campos Requeridos:**
```
- Monto ($)
- Categoría
- Descripción
- Fecha
- Proyecto (si es gasto de proyecto)
```

**Campos Opcionales:**
```
- Recibo/factura (upload)
- Notas adicionales
- Proveedor/Vendor
- Método de pago
```

**Mejora Identificada:**
- ✅ Separación clara entre gastos de proyecto vs gastos generales
- ⚠️ Campo nuevo: expense_type (PROJECT / GENERAL)

---

### 📌 FUNCIÓN 4.2 - Categorizar Gasto

**Categorías de Gastos de PROYECTO:**
```
Principales:
├─ Materiales
│  ├─ Pintura
│  ├─ Madera
│  ├─ Hardware
│  ├─ Drywall
│  └─ Otros materiales
├─ Labor (horas trabajadas - auto-calculado)
├─ Subcontratistas (si se contratan)
└─ Permisos (permits específicos del proyecto)

Nota: Labor normalmente se calcula automático de Time Entries,
      pero puede haber gastos de labor externos (subcontratistas)
```

**Categorías de Gastos GENERALES (Solo Admin):**
```
├─ Oficina
│  ├─ Renta
│  ├─ Utilities (luz, agua, internet)
│  └─ Suministros de oficina
├─ Maquinaria
│  ├─ Compra de equipos
│  └─ Reparaciones
├─ Vehículos
│  ├─ Compra
│  ├─ Mantenimiento
│  ├─ Gasolina
│  └─ Seguros de vehículos
├─ Seguros (empresa)
│  ├─ Liability insurance
│  ├─ Workers compensation
│  └─ Otros seguros
├─ Software
│  ├─ Suscripciones
│  └─ Licencias
├─ Rentals (equipos alquilados)
└─ Comida (empresa - reuniones, eventos)

Nota: Estos NO se asignan a proyectos específicos
```

**Categorías Personalizadas:**
```
PM o Admin pueden crear nuevas categorías:
- Si el proyecto es único y necesita categoría especial
- Ejemplo: "Demolición especial", "Equipo especializado"
- Nueva categoría se agrega a opciones disponibles
- Útil para tracking específico
```

**Agrupación en Reportes:**
```
Cuando se ven gastos por categoría:
- Se agrupan todos los gastos de esa categoría
- Ejemplo: Ver todos los gastos de "Pintura"
  ├─ Pintura exterior - $500
  ├─ Pintura interior - $300
  ├─ Primers - $150
  └─ Total Pintura: $950
```

---

### 📌 FUNCIÓN 4.3 - Asignar Gasto a Proyecto

**Asignación Automática:**
```
Cuando PM está en dashboard del proyecto:
1. Click "Agregar gasto"
2. Proyecto auto-asignado (campo pre-llenado)
3. PM solo completa detalles del gasto
4. Submit → Gasto vinculado a ese proyecto

No puede cambiar proyecto en ese momento
(previene errores de asignación)
```

**Asignación Manual (Admin):**
```
Admin puede:
1. Crear gasto sin estar en proyecto específico
2. Dropdown para seleccionar proyecto
3. Opciones:
   ├─ Proyecto específico (Villa Moderna, Casa Residencial, etc.)
   ├─ "Gasto General" (no asignado a proyecto)
   └─ Múltiples proyectos (NO - ver abajo)

Split entre proyectos: ❌ NO
- 1 gasto = 1 proyecto (o gasto general)
- Si un gasto aplica a varios proyectos:
  → Dividir manualmente en varios gastos
  → Ejemplo: Compré $1000 de pintura
    ├─ $600 para Proyecto A (crear gasto)
    └─ $400 para Proyecto B (crear gasto separado)
```

**Reasignación:**
```
Si se asignó a proyecto incorrecto:

Admin puede:
1. Editar gasto
2. Cambiar proyecto
3. Aplicación inmediata

PM quiere cambiar:
1. PM solicita cambio
2. Admin aprueba
3. Cambio aplicado

Razón: Prevenir movimiento accidental de gastos
        que afecten presupuestos de múltiples proyectos
```

---

### 📌 FUNCIÓN 4.4 - Cargar Recibo/Factura del Gasto

**Tipos de Archivo Permitidos:**
```
Formatos aceptados:
├─ Fotos (JPG, PNG, HEIC)
├─ PDF
└─ Otros formatos de imagen

Validación de calidad:
- NO se requiere alta resolución
- Solo legible para auditoría
- "Mientras se vea y pueda funcionar para auditoría, se queda"

Propósito:
- Documentación para auditorías
- Respaldo en caso de disputa con proveedor
- IRS/Tax compliance
```

**Tamaño de Archivo:**
```
Límite flexible:
- No hay límite estricto de MB
- Validación: ¿Se puede abrir y leer?
- Si es muy pesado: Sistema puede comprimir automáticamente
- Prioridad: Funcionalidad > Tamaño

Ejemplo:
- Foto de iPhone 5MB → ✅ OK
- PDF escaneado 2MB → ✅ OK
- Foto borrosa 500KB → ❌ Rechazar (no legible)
```

**Múltiples Recibos por Gasto:**
```
Permitido: ✅ SÍ

Escenario 1: Compra en múltiples tiendas
- Home Depot: $500 (recibo 1)
- Lowe's: $300 (recibo 2)
- Total gasto: $800
- Upload: 2 recibos

Escenario 2: Factura + comprobante de pago
- Factura del proveedor (recibo 1)
- Comprobante de transferencia (recibo 2)

Sistema:
- Permitir agregar múltiples archivos
- Ver galería de recibos por gasto
- Descargar individual o todos (ZIP)
```

**Recibo Faltante:**
```
No es obligatorio en creación:
- PM puede crear gasto sin recibo
- Se marca como "Recibo pendiente"
- PM puede subir recibo después
- Alerta si gasto >$X sin recibo (configurable)

Razón:
- Emergencias (compra rápida en campo)
- Recibo físico llega después
- PM actualiza cuando tiene el recibo
```

**Mejora Identificada:**
- ⚠️ Compresión automática de imágenes grandes
- ⚠️ Galería de recibos (múltiples por gasto)
- ⚠️ Alerta "Recibo pendiente" para gastos grandes

---

### 📌 FUNCIÓN 4.5 - Asignar Gasto a Orden de Cambio

**Concepto Crítico:**
```
Cuando gasto se asigna a CO:
- Gasto se MUEVE del proyecto principal al CO
- Se cobra directamente al cliente (parte del CO)
- Sirve para tracking: ¿El CO está dentro de presupuesto?

Propósito:
1. Transparencia con cliente (mostrar costos del CO)
2. Budget tracking del CO específico
3. Ganancia/pérdida por CO individual
```

**Proceso de Asignación:**
```
Durante creación de gasto:
1. PM selecciona proyecto
2. Si el proyecto tiene COs activos:
   └─ Dropdown adicional: "Asignar a Change Order"
      ├─ Opción: "Proyecto principal" (default)
      └─ Opciones: CO-001, CO-002, CO-003...
3. PM selecciona CO apropiado
4. Gasto se asigna a ese CO

Después de creación:
1. Admin puede editar gasto
2. Cambiar de proyecto principal → CO
3. Cambiar de un CO → otro CO
4. Cambiar de CO → proyecto principal
```

**Tracking de CO:**
```
Vista del Change Order:

CO-001: Agregar habitación extra
Presupuesto CO: $15,000
Gastos actuales:
├─ Materiales: $8,000
├─ Labor: $4,500
├─ Permisos: $500
└─ Total gastado: $13,000

Restante: $2,000 (13% del presupuesto)
Estado: ✅ Dentro de presupuesto

Ganancia final del CO:
- Cliente pagó: $15,000
- Gastos reales: $13,000
- Ganancia: $2,000
```

**Preferencia - COs como Items Separados:**
```
Razón del tracking separado:
"Es preferible que cada cambio de orden sea un item separado
y después ese sea un item que sume a ganancias o pérdidas
según sean los gastos o entradas del CO"

Beneficios:
1. Ver rendimiento por CO
2. Identificar COs problemáticos (pérdida)
3. Identificar COs rentables (alta ganancia)
4. Mejorar estimados futuros de COs
5. Reportes por tipo de CO

Ejemplo de análisis:
| CO     | Tipo              | Presupuesto | Gastado | Ganancia | Margen |
|--------|-------------------|-------------|---------|----------|--------|
| CO-001 | Agregar habitación| $15,000     | $13,000 | $2,000   | 13%    |
| CO-002 | Cambio de pisos   | $5,000      | $5,500  | -$500    | -10%   |
| CO-003 | Pintura extra     | $3,000      | $2,000  | $1,000   | 33%    |

Total COs: Ganancia $2,500 (promedio 12% margen)
```

**Impacto en Presupuesto del Proyecto:**
```
Gastos de CO NO afectan presupuesto principal:
- Proyecto Villa Moderna: Presupuesto $50,000
- CO-001 agregado: +$15,000
- Presupuestos separados:
  ├─ Proyecto principal: $50,000 (tracking independiente)
  └─ CO-001: $15,000 (tracking independiente)

Dashboard muestra:
- Presupuesto proyecto: $50,000 (sin COs)
- Presupuesto total con COs: $65,000
- Opción toggle: Ver con/sin COs
```

---

### 📌 FUNCIÓN 4.6 - Asignar Código de Costo

**Naturaleza de Cost Codes:**
```
No hay muchos definidos (actualmente):
"Ya que cada proyecto es único"

En el futuro:
"Posiblemente tengamos más datos para analizar"

Enfoque actual:
- Minimalista
- Solo códigos esenciales
- Agregar según necesidad
```

**Cost Codes Básicos (Ejemplos):**
```
Estructura típica de construcción:

División 00 - General
├─ 00.1 - Permisos y fees
├─ 00.2 - Inspecciones
└─ 00.3 - Seguros del proyecto

División 01 - Site Work
├─ 01.1 - Demolición
├─ 01.2 - Excavación
└─ 01.3 - Preparación del sitio

División 02 - Estructura
├─ 02.1 - Concreto
├─ 02.2 - Framing
└─ 02.3 - Steel work

División 03 - Exterior
├─ 03.1 - Siding
├─ 03.2 - Roofing
├─ 03.3 - Windows
└─ 03.4 - Doors

División 04 - Interior
├─ 04.1 - Drywall
├─ 04.2 - Pintura
├─ 04.3 - Flooring
├─ 04.4 - Trim & Molding
└─ 04.5 - Closets

División 05 - MEP
├─ 05.1 - Eléctrico
├─ 05.2 - Plomería
└─ 05.3 - HVAC

División 06 - Finishes
├─ 06.1 - Countertops
├─ 06.2 - Cabinets
└─ 06.3 - Fixtures
```

**Creación de Cost Codes:**
```
PM puede crear custom:
- Si proyecto necesita código específico
- Ejemplo: "Piscina" (no en lista estándar)
- Se agrega a opciones disponibles

Admin puede crear:
- Códigos company-wide
- Estandarizar para todos los proyectos

Opcional en gastos:
- No es obligatorio asignar cost code
- Útil para análisis posterior
- Reportes: "Cuánto gastamos en Drywall en todos los proyectos"
```

**Análisis Futuro:**
```
Cuando tengamos más datos:
1. Reportes por cost code
2. Comparar proyectos similares
3. Mejorar estimados
4. Identificar áreas de alto costo
5. Optimizar procesos

Ejemplo de análisis futuro:
"En los últimos 10 proyectos, 
Drywall (04.1) promedio 15% del presupuesto total
Si nuevo proyecto estima 10%, revisar estimado"
```

**Mejora Identificada:**
- ⚠️ Sistema flexible de cost codes (predefinidos + custom)
- ⚠️ Reportes por cost code (futuro)

---

### 📌 FUNCIÓN 4.7 - Ver Resumen de Gastos por Proyecto

**Dashboard de Gastos del Proyecto:**
```
Vista principal para PM/Admin:

Métricas generales:
├─ Total gastado: $32,450
├─ Presupuesto: $50,000
├─ Restante: $17,550 (35%)
├─ Proyección al ritmo actual: $48,900
└─ Estado: ✅ Dentro de presupuesto
```

**Agrupación por Categoría:**
```
Ver gastos agrupados:

Materiales: $18,500
├─ Pintura: $4,200
├─ Madera: $8,300
├─ Hardware: $2,800
├─ Drywall: $3,200
└─ ...

Labor: $12,000
├─ Auto-calculado de time entries
├─ Horas totales: 480h
└─ Costo promedio: $25/h

Subcontratistas: $1,500
├─ Electricista: $800
└─ Plomero: $700

Permisos: $450
└─ Building permit

Total: $32,450
```

**Filtros Disponibles:**
```
1. Por Categoría:
   ├─ Todas las categorías
   ├─ Materiales
   ├─ Labor
   ├─ Subcontratistas
   └─ Específica (Pintura, Madera, etc.)

2. Por Rango de Fechas:
   ├─ Esta semana
   ├─ Este mes
   ├─ Rango personalizado
   └─ Todo el proyecto

3. Por Empleado/Usuario (quién lo registró):
   ├─ Todos
   ├─ PM específico
   └─ Admin

4. Por Change Order:
   ├─ Solo proyecto principal
   ├─ Solo CO específico (CO-001, CO-002...)
   ├─ Todos los COs
   └─ Todo (proyecto + COs)

5. Por Estado de Recibo:
   ├─ Con recibo
   ├─ Sin recibo (pendiente)
   └─ Todos
```

**Tabla Detallada:**
```
| Fecha  | Categoría    | Descripción           | Monto   | Por     | CO    | Recibo |
|--------|--------------|----------------------|---------|---------|-------|--------|
| 11/10  | Materiales   | Pintura exterior     | $500    | PM Juan | -     | ✅     |
| 11/10  | Labor        | Time entries (10h)   | $250    | Auto    | -     | N/A    |
| 11/09  | Materiales   | Madera para deck     | $1,200  | Admin   | CO-001| ✅     |
| 11/08  | Subcontr.    | Electricista         | $800    | PM Juan | -     | ⚠️     |
```

**Exportar:**
```
Opciones:
- CSV (Excel)
- PDF (reporte formateado)
- Filtros se mantienen en export
- Útil para cliente, auditoría, análisis
```

---

### 📌 FUNCIÓN 4.8 - Ver Gastos por Categoría

**Ya documentado en Función 4.7**

Adicional - Vista Consolidada:
```
Ver todas las categorías con totales:

Dashboard → Gastos por Categoría:

| Categoría        | # Gastos | Total    | % del Total | vs Presupuesto |
|------------------|----------|----------|-------------|----------------|
| Materiales       | 45       | $18,500  | 57%         | ✅ 85% usado   |
| Labor            | 120      | $12,000  | 37%         | ✅ 75% usado   |
| Subcontratistas  | 2        | $1,500   | 5%          | ✅ 50% usado   |
| Permisos         | 1        | $450     | 1%          | ✅ 100% usado  |
| **TOTAL**        | 168      | $32,450  | 100%        | ✅ 65% usado   |

Click en categoría → Ver desglose detallado
```

---

### 📌 FUNCIÓN 4.9 - Ver Gastos por Fecha

**Ya documentado en Función 4.7 - Filtros por fecha**

Adicional - Vista Cronológica:
```
Gráfico de gastos en el tiempo:

Timeline view:
- Eje X: Fechas
- Eje Y: Monto gastado
- Línea acumulativa mostrando total gastado
- Útil para ver ritmo de gasto

Ejemplo:
Semana 1: $5,000 (inicio)
Semana 2: $8,000 (total: $13,000)
Semana 3: $12,000 (total: $25,000)
Semana 4: $7,450 (total: $32,450)

Proyección:
"Al ritmo actual, terminaremos en presupuesto"
```

---

### 📌 FUNCIÓN 4.10 - Calcular Total de Gastos del Proyecto

**Cálculo Automático:**
```
Total Gastos Proyecto = 
  SUM(todos los gastos asignados al proyecto)
  + Labor (auto-calculado de time entries)
  + Gastos de COs (si se incluyen en vista)

Ejemplo:
Materiales: $18,500
Labor: $12,000
Subcontratistas: $1,500
Permisos: $450
-------------------
Total: $32,450

COs (separado):
CO-001: $13,000
CO-002: $5,500
-------------------
Total COs: $18,500

Gran Total (Proyecto + COs): $50,950
```

**Actualización en Tiempo Real:**
```
Se recalcula cuando:
- Se crea nuevo gasto
- Se edita gasto existente
- Se elimina gasto
- Empleado hace clock out (labor)
- Se asigna/remueve gasto de CO

Dashboard muestra total actualizado instantáneamente
```

**Comparación con Presupuesto:**
```
Métricas clave:

Presupuesto original: $50,000
Gastado: $32,450
Restante: $17,550
Porcentaje usado: 65%
Proyección final: $48,900
Estado: ✅ Dentro de presupuesto

Alertas (ver función siguiente):
- Verde: >20% restante
- Amarillo: 10-20% restante
- Naranja: 5-10% restante
- Rojo: <5% restante
```

**Alertas de Presupuesto:**
```
Sistema genera alerta cuando:
Presupuesto restante ≤ 8%

Ejemplo:
Presupuesto: $50,000
Gastado: $46,000
Restante: $4,000 (8%)
→ ALERTA: "Proyecto cerca del límite presupuestal"

Notificación enviada a:
- PM del proyecto
- Admin

Mensaje:
"⚠️ Proyecto Villa Moderna:
Presupuesto restante: $4,000 (8%)
Revisar gastos y ajustar plan"

Propósito:
- Tiempo para optimizar
- Evitar exceder presupuesto
- Tomar decisiones informadas
- Comunicar con cliente si es necesario
```

**Mejora Identificada:**
- ✅ Sistema de alertas cuando restante ≤ 8%
- ✅ Notificaciones automáticas PM + Admin
- ⚠️ Proyección de gasto final (machine learning futuro)

---

### 📌 FUNCIÓN 4.11 - Edición de Gastos

**Permisos de Edición:**

**Admin edita:**
```
1. Admin puede editar cualquier gasto
2. Cambios:
   ├─ Monto
   ├─ Categoría
   ├─ Descripción
   ├─ Fecha
   ├─ Proyecto asignado
   ├─ CO asignado
   └─ Recibo
3. Aplicación inmediata (sin aprobación)
4. Historial de cambios registrado
```

**PM edita:**
```
Flujo de aprobación:

1. PM identifica error en gasto
2. PM edita campos:
   ├─ Puede cambiar: Descripción, notas, recibo
   ├─ Cambios sensibles: Monto, categoría, proyecto
3. Si cambio sensible:
   └─ Estado: "Pendiente aprobación"
   └─ Admin notificado
4. Admin revisa:
   ├─ Aprueba → Cambio aplicado
   └─ Rechaza → Gasto permanece original
5. PM notificado del resultado
```

**Qué se Puede Editar:**
```
Campos editables:
├─ Monto ✅ (requiere aprobación si PM)
├─ Categoría ✅ (requiere aprobación si PM)
├─ Descripción ✅ (directo)
├─ Fecha ✅ (requiere aprobación si PM)
├─ Proyecto ✅ (requiere aprobación si PM)
├─ CO asignado ✅ (requiere aprobación si PM)
├─ Recibo ✅ (directo - agregar/cambiar)
└─ Notas ✅ (directo)

Razón de aprobación para cambios sensibles:
- Prevenir manipulación de presupuestos
- Mantener integridad financiera
- Auditoría y compliance
```

**Historial de Cambios:**
```
Registro de ediciones:

Gasto #1234 - Pintura exterior
─────────────────────────────
Original (11/10/2024 - PM Juan):
- Monto: $500
- Categoría: Materiales
- Proyecto: Villa Moderna

Edición 1 (11/12/2024 - PM Juan → Aprobado por Admin 11/12):
- Cambio: Monto $500 → $550
- Razón: "Recibo correcto muestra $550"

Edición 2 (11/15/2024 - Admin):
- Cambio: Categoría: Materiales → Pintura
- Razón: "Categorización más específica"
```

**Restricciones:**
```
No se puede editar:
- Gastos de proyectos cerrados (locked)
- Gastos en auditoría legal
- Labor auto-generado de time entries (editar time entry en su lugar)

Se puede editar con aprobación:
- Gastos recientes
- Gastos de proyectos activos
```

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 4**

### Nuevas Mejoras:
1. ⚠️ Campo `expense_type` (PROJECT / GENERAL) para separar gastos de proyecto vs empresa
2. ⚠️ Compresión automática de imágenes grandes
3. ⚠️ Galería de múltiples recibos por gasto
4. ⚠️ Alerta "Recibo pendiente" para gastos grandes
5. ✅ Sistema de alertas cuando presupuesto restante ≤ 8%
6. ✅ Notificaciones automáticas a PM + Admin
7. ⚠️ Sistema flexible de cost codes (predefinidos + custom)
8. ✅ Workflow de aprobación PM → Admin para ediciones sensibles
9. ✅ Historial completo de cambios en gastos
10. ⚠️ Proyección de gasto final (machine learning - futuro)

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)

**Total documentado: 38/250+ funciones (15%)**

**Pendientes:**
- ⏳ Módulo 5: Ingresos (10 funciones)
- ⏳ Módulo 6: Facturación (14 funciones) - CRÍTICO
- ⏳ Módulo 7: Estimados (10 funciones)
- ⏳ Módulo 8: Órdenes de Cambio (11 funciones)
- ⏳ Módulo 9: Presupuesto/Earned Value (14 funciones) - CRÍTICO
- ⏳ Módulos 10-27: 170+ funciones

---

## ✅ **MÓDULO 5: GESTIÓN FINANCIERA - INGRESOS** (10/10 COMPLETO)

### 📌 FUNCIÓN 5.1 - Registrar Nuevo Ingreso

**Permisos de Registro:**
```
Solo Admin puede registrar ingresos:
- PM: ❌ NO puede registrar
- Admin: ✅ Puede registrar

Razón:
- Control financiero centralizado
- Verificación de pagos recibidos
- Evitar duplicados o errores
- Compliance y auditoría
```

**Proceso de Registro:**
```
1. Cliente realiza pago (transferencia, cheque, tarjeta)
2. Admin verifica que pago se recibió
3. Admin va a sistema
4. Click "Registrar ingreso"
5. Formulario:
   ├─ Monto recibido
   ├─ Proyecto (dropdown)
   ├─ Método de pago
   ├─ Fecha de pago
   ├─ Factura asociada (si aplica)
   ├─ Descripción/Notas (opcional)
   └─ Comprobante (opcional - foto/screenshot)
6. Submit
7. Sistema:
   ├─ Registra ingreso
   ├─ Si hay factura: Actualiza estado de factura
   └─ Actualiza balance del proyecto
```

**Sin Aprobación:**
```
Admin registra → Aplicación inmediata
- No requiere segunda aprobación
- Admin es la máxima autoridad financiera
- Cambios se reflejan instantáneamente en:
  ├─ Balance del proyecto
  ├─ Ganancia calculada
  ├─ Dashboard financiero
  └─ Reportes
```

---

### 📌 FUNCIÓN 5.2 - Asignar Ingreso a Proyecto

**Tipos de Ingresos:**

**Tipo 1 - Ingresos de Proyecto (Más Común):**
```
Asignación obligatoria:
- Todo ingreso normalmente tiene un proyecto
- Cliente paga por trabajo específico
- Dropdown muestra todos los proyectos activos
- Selección requerida

Ejemplos:
- Pago inicial de Villa Moderna: $15,000 (30% del total)
- Pago de progress de Casa Residencial: $10,000
- Pago final de Remodelación Cocina: $8,500
- Pago de CO-001: $3,000
```

**Tipo 2 - Ingresos Generales/Inversión (Raro):**
```
Sin proyecto asignado:
- Inversión a la empresa
- Préstamo bancario
- Capital del owner
- Otros ingresos no relacionados a proyecto específico

Selección:
- Dropdown incluye opción: "Ingreso General (sin proyecto)"
- Requiere descripción detallada
- No afecta balance de ningún proyecto
- Va directo al fondo general de la empresa
```

**Impacto en el Proyecto:**
```
Cuando se asigna a proyecto:

Antes del ingreso:
- Presupuesto: $50,000
- Gastos: $32,000
- Ingresos: $25,000
- Balance: -$7,000 (cliente debe)

Registrar ingreso de $10,000:
- Ingresos: $35,000
- Balance: $3,000 (superávit)
- Ganancia: $3,000

Dashboard se actualiza automáticamente
```

---

### 📌 FUNCIÓN 5.3 - Seleccionar Método de Pago

**Métodos de Pago Disponibles:**
```
Métodos actuales:
├─ Transferencia bancaria (Wire Transfer)
│  └─ Más común para pagos grandes
├─ Cheque (Check)
│  └─ Tradicional, menos frecuente
├─ Zelle
│  └─ Rápido, conveniente
└─ Tarjeta de Crédito/Débito
   └─ Posible en el futuro

Notas:
- "No hemos recibido pago de otra manera"
- Sistema flexible para agregar nuevos métodos
```

**Propósito del Tracking:**
```
"Método de pago es más para información de la empresa
así en futuro veremos mejor"

Análisis futuro:
1. Preferencias de clientes
   - ¿Mayoría paga con transferencia o Zelle?
   
2. Cash flow timing
   - Transferencias: 1-2 días
   - Cheques: 3-5 días
   - Zelle: Instantáneo
   
3. Fees y costos
   - Tarjeta: 2-3% fee
   - Transferencia: $X fee fijo
   - Zelle: Gratis
   
4. Reportes de taxes
   - Categorización para contabilidad
   - IRS compliance
   
5. Patrones de negocio
   - ¿Proyectos grandes = transferencia?
   - ¿Pagos pequeños = Zelle?
```

**Dropdown en Formulario:**
```
Método de Pago: [Seleccionar]
├─ Transferencia Bancaria
├─ Cheque
├─ Zelle
├─ Tarjeta de Crédito
└─ Otro (especificar)

Campo requerido: ✅ SÍ
- Importante para tracking
- Útil para reconciliación bancaria
```

---

### 📌 FUNCIÓN 5.4 - Vincular Ingreso con Factura

**Naturaleza del Vínculo:**
```
NO todos los pagos tienen factura:

Con factura (mayoría):
- Pagos de trabajos facturados
- Cliente recibe invoice formal
- Pago se vincula a invoice específico

Sin factura:
- Depósitos iniciales (antes de empezar proyecto)
- Inversiones
- Anticipos
- Pagos informales de proyectos pequeños

"No todos los pagos normalmente tienen factura,
al menos que fuera inversión"
```

**Proceso de Vinculación:**
```
Cuando hay factura:

1. Admin registra ingreso
2. Sistema muestra dropdown:
   "Factura asociada: [Seleccionar]"
   
3. Opciones en dropdown:
   ├─ Invoice #001 - Villa Moderna - $50,000 (Sent)
   ├─ Invoice #002 - Casa Residencial - $30,000 (Sent)
   ├─ Invoice #003 - CO-001 - $5,000 (Viewed)
   └─ Ninguna (pago sin factura)

4. Admin selecciona factura correcta
5. Admin ingresa monto pagado
6. Submit
```

**Actualización de Estado de Factura:**
```
Sistema automático cuando se registra pago:

Escenario 1 - Pago Completo:
- Invoice total: $50,000
- Pago recibido: $50,000
- Sistema:
  ├─ Crea registro de pago
  ├─ Vincula pago con invoice
  ├─ Estado de invoice: "Sent" → "Paid"
  └─ Fecha de pago registrada

Escenario 2 - Pago Parcial:
- Invoice total: $50,000
- Pago recibido: $15,000 (30% inicial)
- Sistema:
  ├─ Crea registro de pago
  ├─ Vincula pago con invoice
  ├─ Estado de invoice: "Sent" → "Partial"
  ├─ Balance pendiente: $35,000
  └─ Permite registrar más pagos después

Escenario 3 - Múltiples Pagos Parciales:
- Invoice total: $50,000
- Pago 1: $15,000 (30%) → Estado: "Partial"
- Pago 2: $20,000 (40%) → Estado: "Partial" (70% pagado)
- Pago 3: $15,000 (30%) → Estado: "Paid" (100% pagado)
```

**Registro de Pago:**
```
Sistema crea PaymentRecord:

Información registrada:
├─ Invoice vinculado (si aplica)
├─ Proyecto
├─ Monto
├─ Fecha de pago
├─ Método de pago
├─ Comprobante (si se subió)
├─ Notas
└─ Creado por: Admin

Vista en invoice:
Invoice #001 - Villa Moderna
Total: $50,000
Pagos recibidos:
├─ 10/15/2024 - $15,000 (Transferencia) - Depósito inicial
├─ 11/01/2024 - $20,000 (Zelle) - Pago de progreso
└─ 11/10/2024 - $15,000 (Transferencia) - Pago final
Total pagado: $50,000 ✅
Balance: $0
```

---

### 📌 FUNCIÓN 5.5 - Agregar Descripción/Notas

**Tipos de Notas:**
```
Información adicional si es que hay:

Ejemplos comunes:
- "Pago inicial 30% del proyecto"
- "Pago final después de inspección"
- "Pago de CO-001: Agregar habitación"
- "Depósito antes de comenzar trabajo"
- "Cliente pagó con cheque #4532"
- "Transferencia desde cuenta empresarial"
- "Pago atrasado - intereses incluidos"
- "Descuento aplicado por referencia"

Notas para inversiones:
- "Inversión del propietario para capital de trabajo"
- "Préstamo bancario - Chase Business Line"
- "Capital inicial para nuevo proyecto"
```

**Uso de las Notas:**
```
Propósito:
1. Contexto adicional
2. Clarificación para contabilidad
3. Recordatorios futuros
4. Auditoría
5. Comunicación con contador

Campo:
- Texto libre (textarea)
- Opcional
- Sin límite de caracteres (razonable)
- Se muestra en historial de pagos
```

**Depósito Inicial (30%):**
```
Flujo específico:

Caso 1 - Con depósito inicial:
"Hay un pago incluso para el depósito antes de comenzar 
el proyecto. Que normalmente es el 30% del proyecto al inicio,
esto en algunos proyectos"

Proceso:
1. Proyecto estimado: $50,000
2. Cliente acuerda dar 30% inicial
3. Cliente transfiere: $15,000
4. Admin registra ingreso:
   ├─ Monto: $15,000
   ├─ Proyecto: Villa Moderna
   ├─ Descripción: "Depósito inicial 30% del proyecto"
   ├─ Sin factura (todavía)
   └─ O vinculado a Invoice #001 (si ya se creó)

Caso 2 - Sin depósito inicial:
"La mayoría iniciamos con nuestros fondos"

Proceso:
1. Proyecto inicia sin pago inicial
2. Empresa pone capital de trabajo
3. Cliente paga cuando hay progreso o al final
4. Más riesgo, pero más flexible para cliente
```

---

### 📌 FUNCIÓN 5.6 - Cargar Comprobante de Pago

**Política de Comprobantes:**
```
No es obligatorio pero recomendado:
"No subo comprobantes de pago pero puedo subir una foto,
o un screenshot así mantendremos mejor el record"

Beneficio:
- Mejor tracking
- Evidencia de pago
- Reconciliación bancaria más fácil
- Auditoría
- Disputas con cliente
```

**Tipos de Comprobantes Permitidos:**
```
Formatos aceptados:
├─ Fotos (JPG, PNG, HEIC)
│  └─ Foto de cheque
├─ Screenshots (PNG, JPG)
│  ├─ Screenshot de Zelle
│  ├─ Screenshot de transferencia bancaria
│  └─ Confirmación de pago online
├─ PDF
│  ├─ Confirmación de wire transfer
│  └─ Recibo del banco
└─ Otros formatos de imagen
```

**Proceso de Upload:**
```
Al registrar ingreso:

1. Formulario tiene campo: "Comprobante de Pago (opcional)"
2. Admin puede:
   ├─ Arrastrar archivo
   ├─ Click para seleccionar
   └─ Tomar foto desde móvil (si usa app)
3. Vista previa se muestra
4. Submit guarda comprobante con el ingreso

Después de registrar:
1. Admin puede agregar comprobante después
2. Editar ingreso
3. Upload comprobante
4. Guardar
```

**Ejemplos de Comprobantes:**
```
Transferencia Bancaria:
- Screenshot de confirmación
- Número de referencia visible
- Monto visible
- Fecha visible

Zelle:
- Screenshot de app
- Nombre del destinatario
- Monto enviado
- Fecha y hora

Cheque:
- Foto del cheque (frente)
- Número de cheque visible
- Monto y fecha legibles
- Firma del cliente visible

Tarjeta:
- Recibo de terminal
- Últimos 4 dígitos de tarjeta
- Monto aprobado
- Código de autorización
```

**Visualización:**
```
En historial de ingresos:

| Fecha  | Proyecto | Monto    | Método       | Comprobante |
|--------|----------|----------|--------------|-------------|
| 11/10  | Villa M. | $15,000  | Transferencia| 📎 Ver      |
| 11/05  | Casa Res.| $10,000  | Zelle        | 📎 Ver      |
| 11/01  | CO-001   | $3,000   | Cheque       | ⚠️ Pendiente|

Click "Ver" → Abre modal con imagen/PDF del comprobante
```

**Mejora Identificada:**
- ⚠️ Sistema de upload de comprobantes (similar a receipts de expenses)
- ⚠️ Vista previa de comprobantes
- ⚠️ Alerta si ingreso >$X sin comprobante

---

### 📌 FUNCIÓN 5.7 - Ver Historial de Ingresos

**Vista General:**
```
Dashboard de Ingresos:

Todos los ingresos registrados:
- Ordenados por fecha (más reciente primero)
- Vista de tabla completa
- Métricas agregadas
```

**Filtros Disponibles:**
```
1. Por Mes:
   ├─ Este mes
   ├─ Mes pasado
   ├─ Últimos 3 meses
   ├─ Últimos 6 meses
   ├─ Este año
   └─ Mes específico (selector)

2. Por Proyecto:
   ├─ Todos los proyectos
   ├─ Proyecto específico (dropdown)
   └─ Solo ingresos generales (sin proyecto)

3. Por Método de Pago:
   ├─ Todos los métodos
   ├─ Transferencia
   ├─ Cheque
   ├─ Zelle
   └─ Tarjeta

4. Por Estado de Factura:
   ├─ Con factura
   ├─ Sin factura
   ├─ Facturas pagadas completamente
   └─ Facturas con balance pendiente

5. Por Rango de Monto:
   ├─ Todos
   ├─ > $10,000
   ├─ $5,000 - $10,000
   ├─ < $5,000
   └─ Rango personalizado

6. Con/Sin Comprobante:
   ├─ Todos
   ├─ Con comprobante
   └─ Sin comprobante (pendiente)
```

**Tabla de Historial:**
```
| Fecha  | Proyecto       | Cliente    | Monto    | Método       | Factura | Comprobante | Notas           |
|--------|----------------|------------|----------|--------------|---------|-------------|-----------------|
| 11/10  | Villa Moderna  | Juan Pérez | $15,000  | Transferencia| #001    | ✅          | Pago inicial 30%|
| 11/05  | Casa Resid.    | María G.   | $10,000  | Zelle        | -       | ✅          | Depósito        |
| 11/01  | CO-001 Villa   | Juan Pérez | $3,000   | Cheque       | #005    | ⚠️          | Pago CO aprobado|
| 10/28  | Inversión      | -          | $20,000  | Transferencia| -       | ✅          | Capital trabajo |
```

**Métricas Visibles:**
```
Resumen del período filtrado:

Total de ingresos: $145,000
Número de pagos: 15
Promedio por pago: $9,666
Ingreso más grande: $25,000
Ingreso más pequeño: $1,500

Por método:
├─ Transferencia: $95,000 (65%)
├─ Zelle: $35,000 (24%)
├─ Cheque: $12,000 (8%)
└─ Tarjeta: $3,000 (2%)

Por proyecto:
├─ Villa Moderna: $50,000
├─ Casa Residencial: $45,000
├─ Remodelación: $30,000
└─ Ingresos generales: $20,000
```

**Exportar:**
```
Opciones:
- CSV (Excel)
- PDF (reporte formateado)
- Filtros se mantienen en export
- Útil para contabilidad, taxes, análisis
```

---

### 📌 FUNCIÓN 5.8 - Calcular Total de Ingresos por Proyecto

**Cálculo Completo:**
```
Incluye TODO tipo de pagos:

Total Ingresos Proyecto = 
  Pagos completos
  + Pagos parciales
  + Depósitos iniciales
  + Pagos de Change Orders
  + Cualquier ingreso vinculado al proyecto

Ejemplo - Villa Moderna:
├─ Depósito inicial (30%): $15,000
├─ Pago de progreso (40%): $20,000
├─ Pago final (30%): $15,000
├─ CO-001: $3,000
└─ Total: $53,000
```

**Comparación con Presupuesto:**
```
Dashboard del proyecto:

Presupuesto Total: $50,000
COs agregados: +$3,000
Gran Total: $53,000

Ingresos Recibidos: $53,000
Balance: $0 ✅

Estados posibles:
├─ Balance positivo: Cliente debe dinero
├─ Balance $0: Proyecto pagado completamente
└─ Balance negativo: Sobrepago (crédito para cliente)
```

**Actualización en Tiempo Real:**
```
Se recalcula automáticamente cuando:
- Se registra nuevo ingreso
- Se edita ingreso existente
- Se elimina ingreso
- Se vincula ingreso a proyecto

Dashboard muestra total actualizado instantáneamente
```

---

### 📌 FUNCIÓN 5.9 - Ver Ingresos por Método de Pago

**Vista por Método:**
```
Dashboard → Ingresos por Método de Pago:

Resumen:
| Método        | # Pagos | Total      | % del Total | Promedio  |
|---------------|---------|------------|-------------|-----------|
| Transferencia | 45      | $285,000   | 57%         | $6,333    |
| Zelle         | 38      | $142,000   | 28%         | $3,736    |
| Cheque        | 12      | $58,000    | 12%         | $4,833    |
| Tarjeta       | 5       | $15,000    | 3%          | $3,000    |
| **TOTAL**     | 100     | $500,000   | 100%        | $5,000    |
```

**Análisis Útil:**
```
Insights que se pueden obtener:

1. Preferencias de Clientes:
   - Mayoría usa transferencia para pagos grandes
   - Zelle para pagos medianos/rápidos
   - Cheques en declive
   
2. Cash Flow Timing:
   - Transferencias: 1-2 días → Planificar liquidez
   - Zelle: Instantáneo → Mejor para emergencias
   - Cheques: 3-5 días → Menos preferible
   
3. Fees y Costos:
   - Tarjeta 3% fee → Evitar si posible
   - Zelle gratis → Promover con clientes
   - Transferencias: Fee fijo → OK para pagos grandes
   
4. Reportes de Taxes:
   - Categorización por método
   - Compliance con IRS
   - Auditoría más fácil

5. Patrones de Negocio:
   "Así en futuro veremos mejor"
   - ¿Proyectos residenciales = Zelle?
   - ¿Proyectos comerciales = Transferencia?
   - ¿Pagos pequeños = Zelle?
   - ¿Pagos grandes = Wire transfer?
```

**Filtros Combinados:**
```
Ver ingresos por método Y por período:

Noviembre 2024 - Transferencias:
- 8 pagos
- Total: $95,000
- Proyectos: Villa Moderna ($50k), Casa Res. ($45k)
- Promedio: $11,875 por pago
```

---

### 📌 FUNCIÓN 5.10 - Dashboard de Ingresos

**Métricas Importantes:**
```
"Si todo lo que mencionas en el dashboard de ingresos es importante
así podemos planear el budget mensual algo que no sé cómo hacer aún
pero lo he escuchado para ver cuánto es seguro invertir así puedo
saber cuándo pedir anticipos"

Panel de Control Financiero:

1. Total Recibido (Overall):
   ├─ Este mes: $45,000
   ├─ Mes pasado: $38,000
   ├─ Este año: $485,000
   └─ Todo el tiempo: $1,250,000

2. Pendiente por Cobrar:
   ├─ Facturas enviadas pendientes: $125,000
   ├─ Facturas vencidas: $12,000 ⚠️
   ├─ Balance de facturas parciales: $38,000
   └─ Total pendiente: $175,000

3. Ingresos del Mes (Desglose):
   ├─ Semana 1: $8,000
   ├─ Semana 2: $15,000
   ├─ Semana 3: $12,000
   ├─ Semana 4: $10,000
   └─ Total: $45,000

4. Proyección de Ingresos:
   ├─ Basado en facturas pendientes
   ├─ Basado en promedio mensual
   ├─ Proyección este mes: $52,000
   └─ Proyección próximos 3 meses: $165,000
```

**Planning de Budget Mensual:**
```
Herramienta de Planificación:

Cash Flow Proyectado:
┌─────────────────────────────────────────┐
│ NOVIEMBRE 2024                          │
├─────────────────────────────────────────┤
│ Ingresos Esperados:                     │
│ ├─ Facturas pendientes: $85,000         │
│ ├─ Proyectos en curso: $45,000          │
│ └─ Total esperado: $130,000             │
│                                          │
│ Gastos Proyectados:                     │
│ ├─ Nómina: $35,000                      │
│ ├─ Materiales: $40,000                  │
│ ├─ Gastos generales: $15,000            │
│ └─ Total gastos: $90,000                │
│                                          │
│ Balance Proyectado: +$40,000 ✅         │
└─────────────────────────────────────────┘

Alertas:
├─ ✅ Cash flow positivo
├─ ⚠️ Facturas vencidas: $12,000
└─ 💡 Seguro invertir: ~$25,000
```

**Cuándo Pedir Anticipos:**
```
Indicadores para solicitar depósitos:

Alerta VERDE (Pedir anticipos):
├─ Cash flow proyectado positivo
├─ Proyectos nuevos sin depósito
├─ Gastos de materiales altos próximos
└─ Acción: "Es seguro iniciar proyecto, pedir 30%"

Alerta AMARILLA (Revisar):
├─ Cash flow ajustado (<20% margen)
├─ Múltiples facturas pendientes
├─ Gastos grandes próximos
└─ Acción: "Contactar clientes, acelerar pagos"

Alerta ROJA (Requiere anticipos):
├─ Cash flow negativo proyectado
├─ Facturas vencidas acumuladas
├─ Gastos superan ingresos
└─ Acción: "NO iniciar sin 30-50% anticipo"

Ejemplo práctico:
"Nuevo proyecto estimado: $60,000
Materiales iniciales: $20,000
Cash disponible: $15,000
→ Pedir 30% anticipo ($18,000) para cubrir inicio"
```

**Gráficos Visuales:**
```
1. Ingresos vs Gastos (Mensual):
   - Línea de ingresos
   - Línea de gastos
   - Área de ganancia (diferencia)
   
2. Ingresos por Proyecto:
   - Pie chart mostrando distribución
   - Identificar proyectos más rentables
   
3. Timeline de Ingresos:
   - Vista mensual de ingresos
   - Tendencia (creciendo/decreciendo)
   - Estacionalidad del negocio
   
4. Pendiente por Cobrar:
   - Facturas por edad
   - 0-30 días, 31-60 días, 60+ días
   - Priorizar cobranza
```

**Alertas Automáticas:**
```
Sistema notifica cuando:
├─ Facturas vencidas >15 días
├─ Cash flow proyectado negativo
├─ Ingresos del mes <promedio
├─ Pendiente por cobrar >$X
└─ Cliente con múltiples pagos atrasados
```

**Mejora CRÍTICA Identificada:**
```
🔴 PRIORIDAD ALTA: Cash Flow Management Tool

Funcionalidad necesaria:
1. Proyección de ingresos basada en:
   ├─ Facturas pendientes
   ├─ Proyectos en curso
   ├─ Promedio histórico
   └─ Estacionalidad

2. Proyección de gastos basada en:
   ├─ Nómina fija
   ├─ Gastos generales recurrentes
   ├─ Materiales de proyectos activos
   └─ Compromisos futuros

3. Indicador de "Seguro para invertir":
   Formula:
   Cash_Disponible = Ingresos_Proyectados - Gastos_Proyectados
   
   IF Cash_Disponible > (Gastos_Mensuales * 1.5):
     → VERDE: "Seguro invertir hasta $X"
   ELIF Cash_Disponible > Gastos_Mensuales:
     → AMARILLO: "Pedir anticipos para nuevos proyectos"
   ELSE:
     → ROJO: "Requiere 50% anticipo mínimo"

4. Recomendaciones automáticas:
   - "Solicitar pago a Cliente X (factura vencida 20 días)"
   - "Cash flow positivo, seguro iniciar Proyecto Y"
   - "Pedir 30% anticipo para cubrir materiales"
   - "Contactar clientes con balance pendiente"
```

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 5**

### Nuevas Mejoras:
1. ⚠️ Sistema de upload de comprobantes de pago (fotos/screenshots)
2. ⚠️ Vista previa de comprobantes
3. ⚠️ Alerta si ingreso >$X sin comprobante
4. 🔴 **CRÍTICO**: Cash Flow Management Tool
   - Proyección de ingresos vs gastos
   - Indicador "Seguro para invertir"
   - Alertas de cuándo pedir anticipos
   - Recomendaciones automáticas
5. ⚠️ Gráficos visuales de ingresos (Chart.js)
6. ⚠️ Timeline de cash flow (pasado y proyectado)
7. ✅ Alerta de facturas vencidas >15 días
8. ✅ Tracking de método de pago para análisis futuro
9. ⚠️ Reporte de aging de cuentas por cobrar

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)

**Total documentado: 48/250+ funciones (19%)**

**Pendientes:**
- ⏳ Módulo 6: Facturación (14 funciones) - CRÍTICO
- ⏳ Módulo 7: Estimados (10 funciones)
- ⏳ Módulo 8: Órdenes de Cambio (11 funciones)
- ⏳ Módulo 9: Presupuesto/Earned Value (14 funciones) - CRÍTICO
- ⏳ Módulos 10-27: 170+ funciones

---

## ✅ **MÓDULO 6: FACTURACIÓN (INVOICING)** (14/14 COMPLETO)

### 🔢 **SISTEMA DE NUMERACIÓN DE FACTURAS**

**Estructura del Código:**
```
Formato completo: KP[ESTIMATE#][INITIALS][INVOICE#]

Componentes:
├─ KP = Prefijo empresa (Kibray Painting)
├─ Estimate Number = Número del estimado (1000, 1001, 1002...)
├─ Client Initials = Primeras letras del nombre del cliente
└─ Invoice Number = Número secuencial de factura (01, 02, 03...)

Ejemplo completo:
Cliente: Ivan Stanley
Estimado: KP1000 (primer estimado de la empresa)
Primera factura: KP10001IS01
Segunda factura: KP10001IS02 (si hay facturación por etapas)
```

**Evolución de Numeración:**
```
Estimado 1 (Ivan Stanley):
├─ Código estimado: KP1000
├─ Número interno: 1 (primer estimado creado)
├─ Iniciales: IS (Ivan Stanley)
└─ Facturas:
   ├─ KP10001IS01 (primera factura)
   ├─ KP10001IS02 (segunda factura si aplica)
   └─ KP10001IS03 (tercera factura si aplica)

Estimado 2 (María González):
├─ Código estimado: KP1001
├─ Número interno: 2 (segundo estimado)
├─ Iniciales: MG (María González)
└─ Facturas:
   ├─ KP10011MG01 (primera factura)
   └─ KP10011MG02 (segunda factura si aplica)

Estimado 3 (John Smith):
├─ Código estimado: KP1002
├─ Número interno: 3
├─ Iniciales: JS
└─ Facturas:
   └─ KP10021JS01
```

**Lógica de Generación Automática:**
```python
# Pseudocódigo del sistema

def generate_invoice_number(estimate, client_name):
    # 1. Obtener código del estimado
    estimate_code = estimate.code  # "KP1000"
    estimate_number = estimate.internal_number  # 1
    
    # 2. Extraer iniciales del cliente
    names = client_name.split()
    initials = ''.join([name[0].upper() for name in names[:2]])
    # "Ivan Stanley" -> "IS"
    # "María González" -> "MG"
    # "John Smith" -> "JS"
    
    # 3. Contar facturas existentes para este estimado
    invoice_count = Invoice.objects.filter(estimate=estimate).count()
    next_invoice_number = invoice_count + 1
    
    # 4. Construir código completo
    invoice_code = f"{estimate_code}{estimate_number}{initials}{next_invoice_number:02d}"
    # KP1000 + 1 + IS + 01 = "KP10001IS01"
    
    return invoice_code
```

---

### 📌 FUNCIÓN 6.1 - Crear Nueva Factura

**Permisos de Creación:**
```
Solo Admin puede crear facturas:
- PM: ❌ NO puede crear
- Admin: ✅ Puede crear

Razón:
- Control financiero estricto
- Verificación de términos con cliente
- Aprobación de montos finales
- Compliance y auditoría
```

**Ubicación:**
```
"Hay un espacio especial para crear facturas 
en la parte de finanzas"

Navegación:
Dashboard Admin → Finanzas → Invoicing → Nueva Factura

O desde el proyecto:
Proyecto → Finanzas → Crear Invoice
```

**Flujo de Creación:**
```
1. Admin selecciona proyecto
2. Sistema verifica si hay estimado aprobado
3. Opciones de creación:

   Opción A - Desde Estimado Aprobado (Más común):
   ├─ Sistema carga líneas del estimado aprobado
   ├─ Todas las categorías y montos pre-llenados
   ├─ Admin puede:
   │  ├─ Agregar Change Orders (positivos o negativos)
   │  ├─ Ajustar cantidades si necesario
   │  └─ Agregar líneas extra (con CO recomendado)
   └─ Sistema calcula total automático

   Opción B - Factura Manual (Sin estimado):
   ├─ Para touch-ups, T&M work
   ├─ Admin agrega líneas manualmente
   ├─ Describe servicios
   └─ Establece precios

4. Admin completa información:
   ├─ Fecha de emisión (hoy por default)
   ├─ Fecha de vencimiento (30 días típico)
   ├─ Términos de pago
   └─ Notas especiales

5. Guardar como Draft o Enviar directamente
```

**Cargar desde Estimado:**
```
Sistema inteligente:

1. Detecta estimado aprobado del proyecto
2. Pregunta: "¿Cargar líneas del estimado KP1000?"
3. Si acepta:
   └─ Carga automáticamente:
      ├─ Todas las categorías (Ventanas, Puertas, etc.)
      ├─ Descripciones completas
      ├─ Cantidades
      ├─ Precios unitarios
      ├─ Subtotales
      └─ Total

Ejemplo cargado:
┌──────────────────────────────────────────────┐
│ Invoice KP10001IS01                          │
├──────────────────────────────────────────────┤
│ Líneas (desde Estimado KP1000):              │
│ 1. Pintar ventanas exteriores     $2,000    │
│ 2. Pintar puertas principales      $5,000    │
│ 3. Reparar y pintar techo          $8,000    │
│ 4. Labor (80 horas)               $4,000    │
│                                              │
│ Subtotal:                        $19,000    │
└──────────────────────────────────────────────┘
```

**Agregar Change Orders:**
```
Durante creación de invoice:

1. Admin ve botón: "+ Agregar Change Order"
2. Sistema muestra COs aprobados del proyecto:
   ├─ CO-001: Agregar habitación (+$15,000) ✅ Aprobado
   ├─ CO-002: Eliminar trabajo ($-2,000) ✅ Aprobado
   └─ CO-003: Cambio de pisos (+$3,000) ⏳ Pendiente

3. Admin selecciona COs aprobados
4. Sistema agrega como líneas separadas:

┌──────────────────────────────────────────────┐
│ Invoice KP10001IS01                          │
├──────────────────────────────────────────────┤
│ Trabajo Original (Estimado):                 │
│ 1. Pintar ventanas exteriores     $2,000    │
│ 2. Pintar puertas principales      $5,000    │
│ 3. Reparar y pintar techo          $8,000    │
│ Subtotal Original:               $15,000    │
│                                              │
│ Change Orders Aprobados:                     │
│ CO-001: Agregar habitación       $15,000    │
│ CO-002: Crédito trabajo eliminado ($2,000)  │
│                                              │
│ TOTAL:                           $28,000    │
└──────────────────────────────────────────────┘
```

**Change Orders Negativos:**
```
Escenario: Cliente decidió NO hacer cierto trabajo

CO-002: Eliminar pintura de garage
- Monto: -$2,000 (negativo)
- En factura aparece como crédito
- Reduce total final

Razón:
- Transparencia con cliente
- Muestra ajuste claramente
- Documentación del cambio
```

**Items Extra (Mejor con CO):**
```
"Compré algo extra, lo mejor sería primero pasarlo por CO
así esto no lo afecta"

Proceso recomendado:
1. Admin identifica: "Compré pintura extra $500"
2. Crear CO-004: "Pintura adicional no en estimado"
3. Cliente aprueba CO-004
4. Agregar CO-004 a factura

Ventajas:
- Cliente aprueba antes de facturar
- Transparencia total
- Documentación clara
- Sin sorpresas en factura

Alternativa (no recomendada):
- Agregar directo a factura
- Cliente puede cuestionar
- Potencial conflicto
```

**Aprobación de Change Orders:**
```
"Yo Admin y el cliente podemos aprobar los COs"

Proceso de aprobación:

Opción 1 - Admin aprueba:
├─ CO creado por PM
├─ Admin revisa y aprueba
├─ Cliente notificado (opcional)
└─ CO listo para facturar

Opción 2 - Cliente aprueba:
├─ CO enviado al cliente
├─ Cliente revisa y aprueba (firma digital)
├─ Admin notificado
└─ CO listo para facturar

Mejores prácticas:
- COs >$X requieren aprobación de cliente
- COs pequeños: Admin aprueba directo
- Siempre documentar aprobación
```

---

### 📌 FUNCIÓN 6.2 - Generar Número de Factura Automático

**Ya documentado arriba en Sistema de Numeración**

Resumen técnico:
```
Generación automática al crear invoice:

1. Trigger: Admin click "Crear Factura"
2. Sistema obtiene:
   ├─ Estimado asociado al proyecto
   ├─ Código del estimado (KP1000)
   ├─ Número interno del estimado (1)
   ├─ Nombre del cliente
   └─ Facturas existentes de este estimado

3. Algoritmo:
   ├─ Extract initials from client name
   ├─ Count existing invoices for this estimate
   ├─ Increment invoice number
   └─ Build: KP + estimate_code + estimate_number + initials + invoice_number

4. Resultado: KP10001IS01
5. Campo pre-llenado (admin puede editar si error)
6. Validación: No duplicados permitidos
```

**Casos Especiales:**
```
Cliente con un solo nombre:
- Cliente: "Madonna"
- Iniciales: MA (tomar primeras dos letras)
- Invoice: KP10001MA01

Cliente con nombre compuesto:
- Cliente: "Juan Carlos Pérez"
- Iniciales: JP (primera del nombre + primera del apellido)
- Invoice: KP10001JP01

Cliente empresa:
- Cliente: "ABC Construction LLC"
- Iniciales: AC (primeras letras de primeras dos palabras)
- Invoice: KP10001AC01
```

---

### 📌 FUNCIÓN 6.3 - Agregar Líneas de Factura

**Origen de las Líneas:**

**1. Desde Presupuesto/Estimado (Automático):**
```
"Normalmente los trasladamos del presupuesto estimado,
el estimado que aprobaron, de ahí cargamos todo"

Al seleccionar "Cargar desde Estimado":
- Sistema copia TODAS las líneas
- Descripción, cantidad, precio unitario, total
- Admin puede editar si necesario
- Ahorra tiempo y evita errores
```

**2. Change Orders (Semi-automático):**
```
"También podemos agregar los COs, que pueden ser 
positivos o negativos según sea el caso"

Sistema muestra COs aprobados:
- Click para agregar a factura
- Se agregan como líneas separadas
- Monto positivo o negativo según CO
- Documentación clara para cliente
```

**3. Manual (Si es necesario):**
```
Admin puede agregar líneas manualmente:

Campos por línea:
├─ Descripción (texto libre)
├─ Cantidad (número)
├─ Precio unitario ($)
├─ Total (auto-calculado)
└─ Notas (opcional)

Ejemplo:
Descripción: "Pintura exterior - ventanas"
Cantidad: 10
Precio unitario: $200
Total: $2,000 (auto-calculado)
```

**Interface de Líneas:**
```
Vista de creación:

┌────────────────────────────────────────────────────────┐
│ Líneas de Factura                    [+ Agregar Línea] │
├────────────────────────────────────────────────────────┤
│ # │ Descripción            │ Cant │ P.Unit │ Total     │
├───┼────────────────────────┼──────┼────────┼───────────┤
│ 1 │ Pintar ventanas ext.   │  10  │ $200   │ $2,000    │
│ 2 │ Pintar puertas princ.  │   5  │ $1,000 │ $5,000    │
│ 3 │ Reparar techo          │   1  │ $8,000 │ $8,000    │
│ 4 │ CO-001: Hab. adicional │   1  │ $15,000│ $15,000   │
│ 5 │ CO-002: Crédito garage │   1  │-$2,000 │ -$2,000   │
├───┴────────────────────────┴──────┴────────┴───────────┤
│                              Subtotal:      $28,000    │
│                              Tax (0%):      $0         │
│                              TOTAL:         $28,000    │
└────────────────────────────────────────────────────────┘

[Guardar como Draft] [Enviar al Cliente]
```

**Edición de Líneas:**
```
Admin puede:
├─ Editar descripción (clarificar para cliente)
├─ Ajustar cantidades (si cambió scope)
├─ Modificar precios (si hubo negociación)
├─ Eliminar líneas (si ya no aplican)
├─ Reordenar líneas (drag and drop)
└─ Agregar notas por línea
```

---

### 📌 FUNCIÓN 6.4 - Calcular Subtotal y Total Automáticamente

**Cálculo Automático:**
```
Sistema calcula en tiempo real:

Por cada línea:
Total_Línea = Cantidad × Precio_Unitario

Subtotal = SUM(todas las líneas)

Tax: "No solo el total de la factura"
→ Sin tax por ahora (0%)
→ Sistema preparado para agregar % tax si necesario

Total = Subtotal + Tax
```

**Actualización en Tiempo Real:**
```
Al editar cualquier campo:
- Cantidad cambia → Total línea se actualiza
- Precio unitario cambia → Total línea se actualiza
- Se agrega línea → Subtotal se actualiza
- Se elimina línea → Subtotal se actualiza
- Todo sin recargar página (JavaScript)

Dashboard preview:
Admin ve total actualizándose mientras edita
```

**Sin Taxes (Actualmente):**
```
Configuración actual:
- Tax rate: 0%
- Total = Subtotal

Preparado para futuro:
IF tax_required:
  tax_amount = subtotal * tax_rate
  total = subtotal + tax_amount
ELSE:
  total = subtotal

Razón: Mayoría de trabajos de construcción 
       residencial no requieren sales tax
```

---

### 📌 FUNCIÓN 6.5 - Establecer Fecha de Vencimiento

**Términos de Pago:**
```
"Normalmente después de un mes de enviar la factura"

Default: 30 días desde fecha de emisión

Al crear factura:
├─ Fecha de emisión: [Hoy] (auto-fill)
├─ Términos de pago: [Net 30] (dropdown)
│  ├─ Net 15 (15 días)
│  ├─ Net 30 (30 días) ← Default
│  ├─ Net 60 (60 días)
│  ├─ Due on Receipt (inmediato)
│  └─ Custom (admin especifica)
└─ Fecha de vencimiento: [Auto-calculada]

Ejemplo:
Fecha emisión: Nov 10, 2024
Términos: Net 30
Vencimiento: Dec 10, 2024 (auto-calculado)
```

**Cálculo Automático:**
```
due_date = issue_date + payment_terms_days

Validación:
- Vencimiento no puede ser antes de emisión
- Warning si vencimiento >90 días
- Admin puede override si necesario
```

**Visible en Factura:**
```
PDF muestra claramente:

┌────────────────────────────────┐
│ Invoice KP10001IS01            │
├────────────────────────────────┤
│ Fecha de Emisión: Nov 10, 2024│
│ Fecha de Vencimiento: Dec 10, 2024 │
│ Términos: Net 30               │
└────────────────────────────────┘
```

---

### 📌 FUNCIÓN 6.6 - Cambiar Estado de Factura

**Estados Disponibles:**
```
Draft (Borrador):
"Es cuando inicie una factura pero no la he dado completado,
se guarda en borrador"
├─ Factura en proceso de creación
├─ No visible para cliente
├─ Admin puede seguir editando
└─ No afecta reportes financieros

Sent (Enviado):
"Enviado"
├─ Factura enviada al cliente
├─ Email con PDF enviado
├─ Fecha de envío registrada
├─ Inicia contador de vencimiento
└─ Cliente puede verla

Viewed (Visto):
├─ Cliente abrió el email
├─ Cliente vio el PDF
├─ Tracking automático
└─ Admin sabe que cliente recibió

Approved (Aprobado):
├─ Cliente aprueba factura (opcional)
├─ Puede requerir firma digital
└─ Indica conformidad con monto

Partial (Pago Parcial):
├─ Cliente pagó parte del total
├─ Automático al registrar pago parcial
├─ Muestra balance pendiente
└─ Permite registrar más pagos

Paid (Pagado):
"Cuando ya se registró el último pago ya aparece paid"
├─ Factura pagada completamente
├─ Automático al registrar último pago
├─ Balance = $0
└─ Proyecto completado (financieramente)

Overdue (Vencido):
"Si ha pasado más tiempo del permitido"
├─ Automático después de fecha vencimiento
├─ Requiere acción (recordatorio)
├─ Flag en dashboard
└─ Prioridad de cobranza

Cancelled (Cancelado):
├─ Factura anulada
├─ No se cobrará
├─ Razón documentada
└─ No afecta finanzas del proyecto
```

**Transiciones de Estado:**
```
Flujo normal:
Draft → Sent → Viewed → Partial → Paid

Flujo sin pagos parciales:
Draft → Sent → Viewed → Paid

Flujo con retraso:
Draft → Sent → Viewed → Overdue → Paid

Cancelación:
Draft → Cancelled
Sent → Cancelled (con razón documentada)
```

**Cambios Automáticos:**
```
Sistema cambia estado automáticamente:

1. Draft → Sent:
   - Cuando admin click "Enviar al Cliente"
   - Email enviado automáticamente

2. Sent → Viewed:
   - Cuando cliente abre email (tracking)
   - Cuando cliente abre PDF

3. Sent/Viewed → Partial:
   - Cuando se registra pago < total
   - Balance pendiente calculado

4. Partial → Paid:
   - Cuando último pago completa total
   - Balance = $0

5. Sent/Viewed → Overdue:
   - Tarea Celery diaria (6:00 AM)
   - Verifica: due_date < today AND status != Paid
   - Automático, sin intervención
```

**Cambios Manuales (Admin):**
```
Admin puede cambiar manualmente:
- Draft → Sent (si envió por otro medio)
- Sent → Cancelled (si hubo error)
- Overdue → Paid (si recibió pago)
- Cualquier estado → Cancelled

Requiere razón/nota para auditoría
```

**Con Change Orders Después de Pagar:**
```
"Al menos que se cree un CO, el CO aparecerá según su estado
pero todo el resto pagado"

Escenario:
1. Invoice original: $50,000 → Paid ✅
2. Cliente solicita trabajo adicional
3. Se crea CO-005: +$5,000
4. Nueva factura KP10001IS02:
   ├─ CO-005: $5,000
   └─ Estado: Sent (nueva factura)

Factura original permanece Paid
Nueva factura tiene su propio ciclo de estados
```

---

### 📌 FUNCIÓN 6.7 - Enviar Factura al Cliente

**Sistema de Envío por Email:**
```
"Me gustaría enviar la factura a su email directamente,
con las mejores prácticas de seguridad para que no vaya a spam,
y que pueda ver si la recibió y vio el correo"

Proceso automático:
1. Admin completa factura
2. Click "Enviar al Cliente"
3. Sistema:
   ├─ Genera PDF profesional
   ├─ Crea email con template
   ├─ Agrega tracking pixel (ver si abrió)
   ├─ Incluye link seguro para ver online
   ├─ Adjunta PDF
   └─ Envía via servicio de email transaccional
```

**Mejores Prácticas Anti-Spam:**
```
Configuración técnica necesaria:

1. SPF Record (Sender Policy Framework):
   - Autoriza servidor para enviar emails
   - TXT record en DNS
   - Previene spoofing

2. DKIM (DomainKeys Identified Mail):
   - Firma digital en emails
   - Verifica autenticidad
   - Reducción de spam score

3. DMARC (Domain-based Message Authentication):
   - Política de autenticación
   - Reportes de emails rechazados
   - Protección de dominio

4. Servicio de Email Transaccional:
   Opciones recomendadas:
   ├─ SendGrid (popular, confiable)
   ├─ Mailgun (developer-friendly)
   ├─ Amazon SES (económico, escalable)
   └─ Postmark (especializado en transaccional)

5. Template Profesional:
   - HTML bien formateado
   - Sin palabras spam ("gratis", "urgente")
   - Relación texto/imagen balanceada
   - Link de unsubscribe (aunque no aplique)

6. Reputación del Dominio:
   - Warm-up del dominio (enviar gradualmente)
   - Monitorear bounce rate
   - Lista limpia de contactos
```

**Template del Email:**
```html
Subject: Invoice KP10001IS01 - Villa Moderna Project

Estimado [Client Name],

Adjunto encontrará la factura #KP10001IS01 por el proyecto 
Villa Moderna.

Detalles de la factura:
- Número: KP10001IS01
- Fecha de emisión: November 10, 2024
- Fecha de vencimiento: December 10, 2024
- Monto total: $28,000.00

Puede ver y descargar la factura en línea:
[Ver Factura Online - Link Seguro]

Formas de pago:
- Transferencia bancaria: [Detalles de cuenta]
- Zelle: [Email/Teléfono]
- Cheque a nombre de: Kibray Construction

Si tiene alguna pregunta, no dude en contactarnos.

Gracias por su confianza,
Kibray Construction Team

---
Este es un email automático. Por favor no responda a este correo.
Para consultas, contacte: admin@kibray.com
```

**Tracking de Apertura:**
```
Tracking pixel (imagen 1x1):
<img src="https://kibray.com/track/invoice/[ID]/open" width="1" height="1">

Cuando cliente abre email:
1. Browser carga imagen
2. Servidor registra evento
3. Sistema actualiza estado: Sent → Viewed
4. Admin ve notificación: "Cliente vio factura KP10001IS01"

Click tracking:
Link: https://kibray.com/invoice/[SECURE_TOKEN]
- Registra click
- Muestra cuántas veces abrió
- Timestamp de cada vista
```

**Link Seguro para Ver Online:**
```
Generación de token:
- Token único por factura
- No guessable (UUID o similar)
- Expira después de X días (configurable)
- No requiere login del cliente

URL: https://kibray.com/invoice/view/a7f3c2b1-4e8d-9f2a-1b3c-5d6e7f8g9h0i

Cliente hace click:
├─ Ve factura formateada en browser
├─ Puede descargar PDF
├─ Puede imprimir
├─ Ve información de pago
└─ Sistema registra vista
```

**Dashboard de Envíos:**
```
Admin puede ver:

| Factura      | Enviado    | Visto     | Veces | Último Vista |
|--------------|------------|-----------|-------|--------------|
| KP10001IS01  | Nov 10 10am| Nov 10 2pm| 3     | Nov 11 9am   |
| KP10001MG01  | Nov 9 3pm  | -         | 0     | No visto     |
| KP10021JS01  | Nov 8 1pm  | Nov 8 5pm | 1     | Nov 8 5pm    |

Indicadores:
├─ ✅ Visto (verde)
├─ ⏳ Enviado pero no visto (amarillo)
└─ ⚠️ No visto después de 3 días (rojo)
```

**Mejora CRÍTICA Identificada:**
```
🔴 PRIORIDAD ALTA: Email System Setup

Implementar:
1. Servicio de email transaccional (SendGrid/Mailgun)
2. SPF, DKIM, DMARC records
3. Template HTML profesional
4. Tracking de apertura y clicks
5. Link seguro con token
6. Dashboard de envío/visualización
7. Notificaciones a admin cuando cliente ve factura
```

---

### 📌 FUNCIÓN 6.8 - Registrar Pagos Parciales

**Ya documentado en Función 5.4 (Vincular Ingreso con Factura)**

Resumen del flujo:
```
1. Cliente paga parte del total
2. Admin registra ingreso:
   ├─ Monto: $15,000 (de $50,000 total)
   ├─ Vincula con Invoice KP10001IS01
   └─ Sistema actualiza automático

3. Sistema calcula:
   ├─ Total factura: $50,000
   ├─ Pagado: $15,000
   ├─ Balance: $35,000
   └─ Porcentaje: 30% pagado

4. Estado cambia: Sent → Partial
5. Factura muestra balance pendiente
```

**Vista en la Factura:**
```
┌─────────────────────────────────────┐
│ Invoice KP10001IS01                 │
├─────────────────────────────────────┤
│ Total: $50,000.00                   │
│                                     │
│ Pagos Recibidos:                    │
│ Nov 10, 2024 - $15,000 (Wire)       │
│ Nov 25, 2024 - $20,000 (Zelle)      │
│ Total Pagado: $35,000 (70%)         │
│                                     │
│ BALANCE PENDIENTE: $15,000          │
│ Vencimiento: Dec 10, 2024           │
└─────────────────────────────────────┘
```

---

### 📌 FUNCIÓN 6.9 - Registrar Pago Completo

**Automatización:**
```
"Cuando ya se registró el último pago ya aparece paid"

Sistema automático:
1. Admin registra último pago
2. Sistema verifica:
   IF Total_Pagado >= Total_Invoice:
     estado = "Paid"
     balance = 0
     fecha_pago_completo = today
   
3. Notificación a Admin:
   "✅ Factura KP10001IS01 pagada completamente"
   
4. Dashboard se actualiza
```

**Sin Intervención Manual:**
```
Admin NO necesita:
- Cambiar estado manualmente
- Marcar como pagada
- Cerrar factura

Todo automático al registrar último pago
```

---

### 📌 FUNCIÓN 6.10 - Generar PDF de Factura

**Contenido del PDF:**
```
"El PDF debe de incluir:
- Información de la empresa
- Información del cliente
- Número de factura
- Fecha de vencimiento
- Fecha de entrega"

Template profesional incluye:

┌───────────────────────────────────────────────────┐
│ KIBRAY CONSTRUCTION                               │
│ [Logo]                                            │
│ Address, Phone, Email, Website                    │
│ License #: [Construction License]                 │
├───────────────────────────────────────────────────┤
│                    INVOICE                        │
├───────────────────────────────────────────────────┤
│ Invoice #: KP10001IS01                            │
│ Fecha de Emisión: November 10, 2024              │
│ Fecha de Vencimiento: December 10, 2024          │
│ Términos de Pago: Net 30                         │
├───────────────────────────────────────────────────┤
│ BILL TO:                                          │
│ Ivan Stanley                                      │
│ [Client Address]                                  │
│ [Client Phone]                                    │
│ [Client Email]                                    │
├───────────────────────────────────────────────────┤
│ PROJECT:                                          │
│ Villa Moderna - Residencia Ejecutiva             │
│ [Project Address]                                 │
│ Estimado: KP1000                                  │
├───────────────────────────────────────────────────┤
│ DESCRIPTION          QTY    RATE      AMOUNT      │
├───────────────────────────────────────────────────┤
│ Pintar ventanas      10     $200      $2,000      │
│ Pintar puertas       5      $1,000    $5,000      │
│ Reparar techo        1      $8,000    $8,000      │
│ CO-001: Hab. extra   1      $15,000   $15,000     │
│ CO-002: Crédito      1      -$2,000   -$2,000     │
├───────────────────────────────────────────────────┤
│                          SUBTOTAL:    $28,000     │
│                          TAX (0%):    $0          │
│                          TOTAL:       $28,000     │
├───────────────────────────────────────────────────┤
│ PAGOS RECIBIDOS:                                  │
│ Nov 10 - Wire Transfer           $15,000          │
│                                                   │
│ BALANCE PENDIENTE:               $13,000          │
├───────────────────────────────────────────────────┤
│ FORMAS DE PAGO:                                   │
│ Transferencia Bancaria:                           │
│   Bank: [Bank Name]                               │
│   Account: [Account Number]                       │
│   Routing: [Routing Number]                       │
│                                                   │
│ Zelle: payments@kibray.com                        │
│                                                   │
│ Cheque a nombre de: Kibray Construction LLC      │
├───────────────────────────────────────────────────┤
│ TÉRMINOS Y CONDICIONES:                           │
│ - Pago vence en 30 días desde fecha de emisión   │
│ - Trabajos garantizados por 1 año                │
│ - Intereses de 1.5% mensual en pagos atrasados   │
├───────────────────────────────────────────────────┤
│ Si tiene preguntas sobre esta factura:            │
│ Contacte: admin@kibray.com | (555) 123-4567      │
│                                                   │
│ Gracias por su negocio!                           │
└───────────────────────────────────────────────────┘
```

**Generación Automática:**
```
Librería: WeasyPrint, ReportLab, o xhtml2pdf

Trigger:
- Al enviar factura (adjunto en email)
- Al hacer click "Descargar PDF"
- Al cliente ver factura online

Almacenamiento:
- PDF guardado en servidor
- Path: /media/invoices/2024/11/KP10001IS01.pdf
- Accesible via link seguro
```

**Personalización Futura:**
```
Sistema preparado para:
- Cambiar logo
- Cambiar colores corporativos
- Ajustar layout
- Agregar footer personalizado
- Múltiples idiomas (español/inglés)
```

---

### 📌 FUNCIÓN 6.11 - Ver Historial de Facturas

**Filtros Disponibles:**
```
"El filtro de las facturas debe de ser por:
- Proyecto
- Fechas
- Estados"

Interface de filtros:

┌─────────────────────────────────────────┐
│ Filtros                                 │
├─────────────────────────────────────────┤
│ Proyecto: [Todos ▼]                     │
│ ├─ Todos los proyectos                  │
│ ├─ Villa Moderna                        │
│ ├─ Casa Residencial                     │
│ └─ ...                                  │
│                                         │
│ Rango de Fechas:                        │
│ Desde: [Nov 1, 2024]                    │
│ Hasta: [Nov 30, 2024]                   │
│ Quick: [Este Mes] [Este Año] [Todo]    │
│                                         │
│ Estado: [Todos ▼]                       │
│ ├─ ☑ Draft                              │
│ ├─ ☑ Sent                               │
│ ├─ ☑ Viewed                             │
│ ├─ ☑ Partial                            │
│ ├─ ☑ Paid                               │
│ ├─ ☑ Overdue                            │
│ └─ ☐ Cancelled                          │
│                                         │
│ Cliente: [Todos ▼]                      │
│                                         │
│ [Aplicar Filtros] [Limpiar]            │
└─────────────────────────────────────────┘
```

**Vista de Tabla:**
```
| Factura      | Proyecto    | Cliente | Fecha     | Vence     | Total    | Pagado   | Balance  | Estado   |
|--------------|-------------|---------|-----------|-----------|----------|----------|----------|----------|
| KP10001IS01  | Villa Mod.  | I.Stan. | Nov 10    | Dec 10    | $28,000  | $15,000  | $13,000  | Partial  |
| KP10011MG01  | Casa Res.   | M.Gonz. | Nov 5     | Dec 5     | $45,000  | $45,000  | $0       | Paid ✅  |
| KP10021JS01  | Remodel.    | J.Smith | Oct 20    | Nov 20    | $12,000  | $5,000   | $7,000   | Overdue⚠️|

Acciones por factura:
├─ 👁️ Ver detalles
├─ 📄 Descargar PDF
├─ ✉️ Reenviar email
├─ 💰 Registrar pago
└─ ✏️ Editar (solo si Draft)
```

**Métricas del Período:**
```
Resumen filtrado:

Total de facturas: 45
Total facturado: $485,000
Total cobrado: $352,000
Pendiente: $133,000

Por estado:
├─ Paid: 28 facturas ($352,000)
├─ Partial: 12 facturas ($98,000 pendiente)
├─ Overdue: 5 facturas ($35,000 pendiente) ⚠️
└─ Sent: 10 facturas ($125,000 pendiente)
```

---

### 📌 FUNCIÓN 6.12 - Dashboard de Facturas Pendientes

**Prioridades en Dashboard:**
```
"Dashboard de pendientes:
- Facturas vencidas
- Próximas a vencer"

Vista optimizada para acción:

┌────────────────────────────────────────────────┐
│ 🔴 FACTURAS VENCIDAS (5)        Total: $35,000 │
├────────────────────────────────────────────────┤
│ KP10021JS01 │ Vencida 22 días │ $12,000 │ 🔔   │
│ KP09981AB02 │ Vencida 15 días │ $8,500  │ 🔔   │
│ KP10031CD01 │ Vencida 8 días  │ $7,000  │ 🔔   │
│ KP09971EF01 │ Vencida 5 días  │ $5,000  │      │
│ KP10041GH01 │ Vencida 2 días  │ $2,500  │      │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ ⚠️ PRÓXIMAS A VENCER (8)        Total: $98,000 │
├────────────────────────────────────────────────┤
│ KP10051IJ01 │ Vence en 2 días │ $25,000 │      │
│ KP10061KL01 │ Vence en 5 días │ $18,000 │      │
│ KP10071MN01 │ Vence en 8 días │ $15,000 │      │
│ ... 5 más                                      │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ ✅ PAGOS PARCIALES (12)        Pend: $133,000  │
├────────────────────────────────────────────────┤
│ KP10001IS01 │ 53% pagado      │ $13,000 pend.  │
│ KP09991OP01 │ 40% pagado      │ $18,000 pend.  │
│ ... 10 más                                     │
└────────────────────────────────────────────────┘

Acciones rápidas:
├─ 🔔 Enviar recordatorio
├─ 💰 Registrar pago
├─ 📄 Ver factura
└─ 📞 Llamar cliente
```

**Alertas Visuales:**
```
Códigos de color:

🔴 Rojo - Overdue:
├─ Vencidas >7 días
├─ Requiere acción inmediata
└─ Prioridad máxima

⚠️ Amarillo - Próximas a vencer:
├─ Vencen en <7 días
├─ Considerar recordatorio proactivo
└─ Monitorear de cerca

🟡 Naranja - Pagos parciales:
├─ Seguimiento de balance
├─ Contactar para segundo pago
└─ Programar próxima fecha

✅ Verde - Paid:
├─ No requiere acción
└─ Solo para referencia
```

---

### 📌 FUNCIÓN 6.13 - Alertas de Facturas Vencidas

**Sistema de Recordatorios:**
```
"Cuando el invoice ya se venció aparece en la lista de pendientes
y de ahí tendrá un botón de recordatorio donde se escribe un correo
al cliente con el número de factura y se vuelve a agregar la factura,
esto primero debe de ser hecho por el admin, el admin decide si
enviar un recordatorio"

Proceso MANUAL (Admin controla):

1. Factura aparece en lista de vencidas
2. Admin revisa situación
3. Admin decide si enviar recordatorio
4. Admin click botón "🔔 Enviar Recordatorio"
5. Sistema muestra template de email
6. Admin puede:
   ├─ Editar mensaje
   ├─ Agregar nota personal
   └─ Cambiar tono (amigable vs formal)
7. Admin click "Enviar"
8. Sistema:
   ├─ Envía email al cliente
   ├─ Adjunta factura nuevamente (PDF)
   ├─ Registra envío de recordatorio
   └─ Marca fecha de último recordatorio
```

**Template de Recordatorio:**
```html
Subject: Recordatorio - Factura KP10021JS01 Vencida

Estimado [Client Name],

Le escribimos para recordarle amablemente que la factura 
#KP10021JS01 tiene un balance pendiente.

Detalles:
- Número de factura: KP10021JS01
- Proyecto: Remodelación Cocina
- Monto total: $12,000
- Pagado: $0
- Balance pendiente: $12,000
- Fecha de vencimiento: October 20, 2024
- Días vencida: 22 días

Adjunto encontrará la factura nuevamente para su referencia.

[Ver Factura Online - Link Seguro]

Formas de pago:
[Detalles de pago]

Si ya realizó el pago, por favor ignore este mensaje y 
acepte nuestras disculpas.

Si tiene alguna pregunta o necesita hacer arreglos de pago,
no dude en contactarnos.

Gracias por su atención,
Kibray Construction

[Contacto]
```

**Control del Admin:**
```
Razones para control manual:

1. Contexto del cliente:
   - Cliente confiable con historial bueno
   - Situación temporal conocida
   - Acuerdo especial de pago

2. Relación comercial:
   - No automatizar para mantener toque personal
   - Evitar molestar buenos clientes
   - Timing apropiado

3. Múltiples recordatorios:
   - Primer recordatorio: 7 días después de vencer
   - Segundo: 14 días después
   - Tercero: 30 días después
   - Admin decide cuándo cada uno

4. Escalación:
   - Primer recordatorio: Amigable
   - Segundo: Más formal
   - Tercero: Mencionar acciones (intereses, colecciones)
```

**Registro de Recordatorios:**
```
Sistema guarda historial:

Factura KP10021JS01:
├─ Enviada: Oct 20, 2024
├─ Vencimiento: Nov 20, 2024
├─ Recordatorio 1: Nov 27 (7 días después)
├─ Recordatorio 2: Dec 4 (14 días después)
└─ Recordatorio 3: Dec 18 (28 días después)

Vista en factura:
"Recordatorios enviados: 3
Último: December 18, 2024"
```

**Sin Automatización (Por Diseño):**
```
NO automático porque:
- Admin conoce la situación
- Relaciones comerciales delicadas
- Flexibilidad en timing
- Toque personal necesario
- Evitar spam

Admin tiene control total de cuándo y cómo contactar
```

---

### 📌 FUNCIÓN 6.14 - Invoice Builder (Interfaz Avanzada)

**Concepto del Builder:**
```
"Me gustaría crear una interfaz avanzada, para poder 
sincronizar todo con los budgets, estimados aprobados, COs,
pero en un entorno muy fácil de manejar pero muy avanzado,
todo lo necesario y posible a faltar que esté ahí de preferencia
que nunca falte nada, mejor que sobre algo que no se use a que 
falte algo"

Filosofía: "Better to have it and not use it, than need it and not have it"
```

**Interface Completa - Todo en Un Lugar:**
```
┌─────────────────────────────────────────────────────────┐
│ 📄 INVOICE BUILDER - KP10001IS01                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ┌─── PROJECT INFO ─────────┐  ┌─── PREVIEW ─────────┐ │
│ │ Proyecto: Villa Moderna   │  │ [Live PDF Preview]  │ │
│ │ Cliente: Ivan Stanley     │  │                     │ │
│ │ Estimado: KP1000          │  │ Updates in          │ │
│ │ Budget: $50,000           │  │ real-time as        │ │
│ │ Gastado: $32,000 (64%)    │  │ you edit            │ │
│ └───────────────────────────┘  │                     │ │
│                                │                     │ │
│ ┌─── LOAD FROM ─────────────┐  │                     │ │
│ │ [Load Estimate KP1000]    │  │                     │ │
│ │ [Load Budget Lines]       │  │                     │ │
│ │ [Load Time Entries]       │  │                     │ │
│ │ [Load Material Expenses]  │  └─────────────────────┘ │
│ └───────────────────────────┘                          │
│                                                         │
│ ┌─── INVOICE LINES ──────────────────────────────────┐ │
│ │ # │ Source    │ Description        │ Qty │ Rate  │ │
│ │ 1 │ Estimate  │ Pintar ventanas    │ 10  │ $200  │ │
│ │ 2 │ Estimate  │ Pintar puertas     │ 5   │ $1,000│ │
│ │ 3 │ Budget    │ Labor (80h)        │ 80  │ $50   │ │
│ │ 4 │ CO-001    │ Habitación extra   │ 1   │$15,000│ │
│ │   │ [+ Add Line] [+ Add CO] [+ Add from Budget]   │ │
│ └───────────────────────────────────────────────────────┘│
│                                                         │
│ ┌─── CHANGE ORDERS ──────────────────────────────────┐ │
│ │ Available COs:                                      │ │
│ │ ☑ CO-001: Agregar habitación (+$15,000) Approved   │ │
│ │ ☑ CO-002: Eliminar garage (-$2,000) Approved       │ │
│ │ ☐ CO-003: Cambio pisos (+$3,000) Pending          │ │
│ │                                                     │ │
│ │ [Add Selected COs to Invoice]                      │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─── SMART CALCULATIONS ─────────────────────────────┐ │
│ │ Estimate Total:        $15,000                      │ │
│ │ Labor (Time Entries):  $4,000  (80h × $50)         │ │
│ │ Materials (Expenses):  $8,000                       │ │
│ │ COs Approved:          +$13,000 (CO-001, CO-002)   │ │
│ │ ─────────────────────────────────────────────────  │ │
│ │ Subtotal:              $40,000                      │ │
│ │ Tax (0%):              $0                           │ │
│ │ TOTAL:                 $40,000                      │ │
│ │                                                     │ │
│ │ Project Budget:        $50,000                      │ │
│ │ This Invoice:          $40,000                      │ │
│ │ Remaining to Invoice:  $10,000                      │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─── PAYMENT TERMS ──────────────────────────────────┐ │
│ │ Issue Date: [Nov 12, 2024]                          │ │
│ │ Terms: [Net 30 ▼]                                   │ │
│ │ Due Date: [Dec 12, 2024] (auto-calculated)          │ │
│ │ Delivery Date: [Nov 10, 2024]                       │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─── TEMPLATES ──────────────────────────────────────┐ │
│ │ Style: [Standard Template ▼]                        │ │
│ │ ├─ Standard (default)                               │ │
│ │ ├─ Detailed (with breakdown)                        │ │
│ │ ├─ Simple (minimal)                                 │ │
│ │ └─ Custom...                                        │ │
│ │                                                     │ │
│ │ [Preview All Styles]                                │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Save as Draft] [Preview PDF] [Send to Client] [❌]   │
└─────────────────────────────────────────────────────────┘
```

**Características Avanzadas:**

**1. Sincronización con Budget:**
```
Builder detecta automáticamente:
├─ Líneas del presupuesto aprobado
├─ Gastos reales vs presupuesto
├─ Variaciones (+/-)
└─ Sugiere qué facturar

Ejemplo:
Presupuesto: Pintar 10 ventanas - $2,000
Real: Se pintaron 12 ventanas
Builder sugiere: Agregar CO por 2 ventanas extra (+$400)
```

**2. Integración con Time Entries:**
```
Builder calcula labor automáticamente:
├─ Lee todas las time entries del proyecto
├─ Agrupa por categoría de trabajo
├─ Calcula: horas × tarifa de venta
└─ Genera línea de factura

Ejemplo:
Time Entries:
- Pintura: 60h × $50/h = $3,000
- Carpintería: 20h × $60/h = $1,200
Total Labor: $4,200

Builder ofrece agregar como línea separada o incluir en items
```

**3. Integración con Expenses:**
```
Builder lee gastos de materiales:
├─ Suma materiales por categoría
├─ Aplica markup configurado (10%, 15%, etc.)
├─ Sugiere líneas de factura

Ejemplo:
Expenses:
- Pintura: $2,000 (costo) × 1.15 = $2,300 (venta)
- Madera: $3,000 × 1.15 = $3,450
Builder ofrece agregar como líneas itemizadas
```

**4. Smart Change Order Integration:**
```
Builder muestra COs:
├─ Filtrados por estado (solo Approved)
├─ Positivos y negativos
├─ Con descripción completa
├─ Checkbox para seleccionar múltiples
└─ Agregar con un click

Validación:
- Solo COs aprobados disponibles
- COs ya facturados marcados
- Alert si intenta facturar CO pendiente
```

**5. Live Preview:**
```
Preview en tiempo real:
├─ PDF se genera mientras editas
├─ Ve exactamente cómo se verá
├─ Cambios instantáneos
├─ Zoom in/out
└─ Download preview

Tecnología: PDF.js o similar para render in-browser
```

**6. Template System:**
```
"En general este creador creará todas las facturas con el
mismo estilo hasta que se decida cambiar algo"

Templates disponibles:
├─ Standard Template (default para todas)
├─ Detailed Template (con breakdown completo)
├─ Simple Template (minimalista)
└─ Custom Templates (admin puede crear)

Al cambiar template:
- Todas las nuevas facturas usan nuevo estilo
- Facturas existentes mantienen su estilo original
- Preview muestra todos los estilos disponibles
```

**7. Validation & Warnings:**
```
Builder valida en tiempo real:

⚠️ Warnings:
├─ "Esta línea excede presupuesto de categoría"
├─ "Total factura > Budget proyecto"
├─ "CO no aprobado por cliente aún"
├─ "Labor facturado > Labor real trabajado"
└─ "Materiales sin markup aplicado"

✅ Confirmaciones:
├─ "Todos los gastos del proyecto incluidos"
├─ "Budget tracking: 80% facturado"
├─ "Remaining to invoice: $10,000"
```

**8. Keyboard Shortcuts:**
```
Para eficiencia:
├─ Ctrl+S: Save as draft
├─ Ctrl+P: Preview PDF
├─ Ctrl+Enter: Send to client
├─ Ctrl+L: Load from estimate
├─ Ctrl+N: New line
└─ Esc: Cancel/Close
```

**9. Auto-Save:**
```
Builder guarda automáticamente:
- Cada 30 segundos
- Al cambiar de tab
- Al preview
- Estado guardado en Draft
- Nunca perder trabajo
```

**10. Comparison View:**
```
Vista comparativa útil:

┌─────────────────────────────────────────┐
│ BUDGET vs INVOICE COMPARISON            │
├─────────────────────────────────────────┤
│ Item          │ Budget │ Invoice │ Diff │
├───────────────┼────────┼─────────┼──────┤
│ Ventanas      │ $2,000 │ $2,000  │  0%  │
│ Puertas       │ $5,000 │ $5,000  │  0%  │
│ Labor         │ $4,000 │ $4,500  │ +12% │
│ Materiales    │ $8,000 │ $7,500  │ -6%  │
│ COs           │ $0     │ $13,000 │  -   │
├───────────────┼────────┼─────────┼──────┤
│ TOTAL         │$19,000 │ $32,000 │ +68% │
└─────────────────────────────────────────┘

Ayuda a identificar discrepancias
```

**Mejoras CRÍTICAS Identificadas:**
```
🔴 PRIORIDAD MÁXIMA: Invoice Builder Interface

Componentes a implementar:
1. Drag-and-drop line editor
2. Real-time PDF preview (PDF.js)
3. Smart loading from estimate/budget/time/expenses
4. CO integration with approval status
5. Live calculations and validations
6. Template system with switcher
7. Comparison view (budget vs invoice)
8. Auto-save every 30s
9. Keyboard shortcuts
10. Responsive design (desktop first)

Tecnologías sugeridas:
- Frontend: Vue.js o React (para interactividad)
- PDF Generation: WeasyPrint (backend) + PDF.js (preview)
- Drag-drop: SortableJS
- Live updates: WebSockets o polling
- State management: Vuex/Redux
```

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 6**

### Mejoras CRÍTICAS:
1. 🔴 **Sistema de Email Transaccional**
   - SendGrid/Mailgun integration
   - SPF, DKIM, DMARC setup
   - Template profesional HTML
   - Tracking de apertura y clicks
   - Link seguro con token único

2. 🔴 **Invoice Builder - Interfaz Avanzada**
   - Load from estimate/budget/time/expenses
   - Live PDF preview
   - Smart CO integration
   - Real-time validation
   - Template system
   - Auto-save
   - Comparison views

3. 🔴 **Sistema de Numeración Automática**
   - Algoritmo: KP[ESTIMATE#][INITIALS][INVOICE#]
   - Generación automática
   - Validación de unicidad

### Mejoras Importantes:
4. ⚠️ Dashboard de facturas con priorización
5. ⚠️ Sistema de recordatorios manual (control del admin)
6. ⚠️ Template profesional de PDF
7. ⚠️ Tracking de views y engagement
8. ⚠️ Multi-template system para futuro
9. ✅ Estados automáticos basados en pagos
10. ✅ Celery task para marcar overdue

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO

**Total documentado: 62/250+ funciones (25%)**

**Pendientes:**
- ⏳ Módulo 7: Estimados (10 funciones)
- ⏳ Módulo 8: Órdenes de Cambio (11 funciones)
- ⏳ Módulo 9: Presupuesto/Earned Value (14 funciones) - CRÍTICO
- ⏳ Módulos 10-27: 160+ funciones

---

## ✅ **MÓDULO 7: ESTIMADOS (ESTIMATES)** (10/10 COMPLETO)

### 🔄 **FLUJO DE CREACIÓN - ORDEN CORRECTO**

**Secuencia Obligatoria:**
```
1. PRIMERO: Crear Cliente
   └─ Información completa del cliente necesaria

2. SEGUNDO: Crear Estimado (Opcional)
   └─ Vinculado al cliente
   └─ Puede hacerse antes o después de proyecto

3. TERCERO: Crear Proyecto
   Opción A: Desde estimado aprobado (auto-create)
   Opción B: Directo sin estimado (touch-ups, T&M)
```

**Importancia del Orden:**
```
"Primero se crea el cliente, ya una vez creado el cliente
se puede crear el estimado, así que la información del
cliente es necesaria primero antes de crear estimado"

Razón:
- Estimado necesita info del cliente para PDF
- Cliente puede tener múltiples estimados
- Tracking por cliente
```

---

### 📌 FUNCIÓN 7.1 - Crear Nuevo Estimado

**Permisos de Creación:**
```
Solo Admin puede crear estimados:
- PM: ❌ NO puede crear
- Admin: ✅ Puede crear

Razón:
- Decisión comercial estratégica
- Pricing y márgenes sensibles
- Presentación profesional al cliente
- Control de propuestas enviadas
```

**Timing de Creación:**
```
Puede crear antes de proyecto: ✅ SÍ
"Puede crear antes de crear un proyecto, pero también
se puede crear después del proyecto"

Escenario 1 - Antes del Proyecto (Más Común):
├─ Cliente solicita cotización
├─ Admin crea estimado
├─ Admin envía al cliente
├─ Cliente aprueba
└─ Sistema auto-crea proyecto desde estimado

Escenario 2 - Después del Proyecto (Raro):
├─ Proyecto urgente iniciado sin estimado formal
├─ Durante el trabajo, cliente pide estimado oficial
├─ Admin crea estimado para documentación
└─ Vincula con proyecto existente

Escenario 3 - Sin Estimado (Touch-ups):
├─ Trabajo pequeño/rápido
├─ No requiere estimado formal
└─ Proyecto directo sin estimado
```

**Proceso de Creación:**
```
1. Admin verifica que cliente existe
2. Admin va a: Dashboard → Estimados → Nuevo Estimado
3. Selecciona cliente (dropdown de clientes existentes)
4. Sistema auto-genera código: KP1000, KP1001, etc.
5. Admin agrega líneas del estimado (manual)
6. Admin agrega link de Takeoff/Marked Plans
7. Admin completa información adicional
8. Guardar como Draft o Enviar
```

**Prerequisito - Cliente Debe Existir:**
```
Si cliente no existe:
1. Sistema muestra: "Cliente no encontrado"
2. Link: "Crear nuevo cliente primero"
3. Admin crea cliente:
   ├─ Nombre completo
   ├─ Dirección del proyecto
   ├─ Email
   ├─ Teléfono
   └─ Notas
4. Regresar a crear estimado
5. Cliente ahora disponible en dropdown
```

---

### 📌 FUNCIÓN 7.2 - Generar Código de Estimado Automático

**Sistema de Numeración:**
```
Formato: KP + Número Secuencial

Secuencia:
- Primer estimado: KP1000
- Segundo estimado: KP1001
- Tercer estimado: KP1002
- ...
- Estimado 100: KP1099
- Estimado 101: KP1100

"Siempre será KP y el resto como se explicó"
```

**Generación Automática:**
```
Al crear nuevo estimado:

1. Sistema consulta último estimado creado
2. Extrae número (ej: 1000 del KP1000)
3. Incrementa en 1 (1000 + 1 = 1001)
4. Construye nuevo código: KP1001
5. Valida que no exista (unicidad)
6. Asigna al nuevo estimado

Pseudocódigo:
```python
def generate_estimate_code():
    last_estimate = Estimate.objects.order_by('-internal_number').first()
    
    if last_estimate:
        next_number = last_estimate.internal_number + 1
    else:
        next_number = 1  # Primer estimado
    
    # Formato: KP + número empezando en 1000
    code = f"KP{1000 + next_number - 1}"
    
    return code, next_number

# Primer estimado: KP1000 (internal_number = 1)
# Segundo: KP1001 (internal_number = 2)
# Tercero: KP1002 (internal_number = 3)
```
```

**Validación:**
```
Sistema verifica:
├─ Código único (no duplicados)
├─ Formato correcto (KP + números)
├─ Secuencia correcta (sin saltos)
└─ Campo read-only (admin no puede editar manualmente)

Si hay conflicto:
- Sistema encuentra siguiente número disponible
- Log de warning para admin
- Continúa con secuencia correcta
```

---

### 📌 FUNCIÓN 7.3 - Agregar Líneas de Estimado

**Entrada Manual:**
```
"Se agregan las líneas manualmente"

Admin agrega cada línea con:
├─ Item (nombre del trabajo)
├─ Descripción (detalles del trabajo)
├─ Precio (monto total por ese item)
└─ Notas (opcional)

Proceso externo:
"Hago los estimados con AI fuera de la app
y ya solo lo traslado ahí para el control y seguimiento"
```

**Campos por Línea:**
```
Formulario de línea:

┌────────────────────────────────────────────────┐
│ Agregar Línea de Estimado                      │
├────────────────────────────────────────────────┤
│ Item: [Pintura de ventanas exteriores        ]│
│                                                │
│ Descripción (opcional):                        │
│ [Preparación de superficie, primer,           │
│  2 capas de pintura exterior premium,         │
│  incluye marcos y rejas]                      │
│                                                │
│ Precio: [$2,000.00                           ]│
│                                                │
│ Notas (opcional):                              │
│ [Cliente solicitó color específico            │
│  Benjamin Moore - Swiss Coffee]               │
│                                                │
│ [+ Agregar Línea] [Cancelar]                  │
└────────────────────────────────────────────────┘
```

**Interface de Lista:**
```
Vista de edición del estimado:

┌──────────────────────────────────────────────────────────┐
│ Estimado KP1000 - Ivan Stanley                           │
├──────────────────────────────────────────────────────────┤
│ # │ Item                    │ Precio    │ Acciones       │
├───┼─────────────────────────┼───────────┼────────────────┤
│ 1 │ Pintura ventanas ext.   │ $2,000    │ ✏️ Editar 🗑️   │
│ 2 │ Pintura puertas princ.  │ $5,000    │ ✏️ Editar 🗑️   │
│ 3 │ Reparar y pintar techo  │ $8,000    │ ✏️ Editar 🗑️   │
│ 4 │ Pintura interior        │ $12,000   │ ✏️ Editar 🗑️   │
├───┴─────────────────────────┴───────────┴────────────────┤
│ [+ Agregar Nueva Línea]                                  │
│                                                          │
│ TOTAL DEL ESTIMADO:                          $27,000    │
└──────────────────────────────────────────────────────────┘
```

**No es Suma Simple:**
```
"No es una línea simple de sumas"

Admin usa AI/herramientas externas:
1. Analiza planos y scope de trabajo
2. Usa AI para calcular materiales y labor
3. Aplica markups y contingencias
4. Calcula pricing estratégico
5. Obtiene precio final por item
6. Traslada a sistema para control

Sistema solo almacena resultado final:
- No calcula precios automáticamente
- Admin ingresa precio ya calculado
- Sistema suma para obtener total
- Control y seguimiento del estimado
```

**Notas Opcionales:**
```
Uso de notas:
├─ Especificaciones técnicas
├─ Colores o materiales solicitados
├─ Condiciones especiales
├─ Timeframes estimados
└─ Cualquier aclaración importante

Visibilidad:
- Notas pueden aparecer en PDF (configurable)
- Útil para comunicación con cliente
- Documentación interna
```

**Edición de Líneas:**
```
Admin puede:
├─ Editar cualquier línea (mientras estado = Draft)
├─ Reordenar líneas (drag and drop)
├─ Eliminar líneas
├─ Duplicar líneas (copiar para editar)
└─ Expandir/colapsar descripciones largas

Restricción:
Si estimado ya fue enviado/aprobado:
- Solo lectura
- No se puede editar
- Crear nuevo estimado si necesita cambios
```

---

### 📌 FUNCIÓN 7.4 - Vincular con Proyecto

**Momento de Vinculación:**
```
Dos escenarios:

Escenario A - Auto-vinculación (Más común):
1. Estimado creado: KP1000
2. Estado: Draft
3. Admin envía a cliente
4. Cliente aprueba estimado
5. Admin marca estado: Approved
6. Sistema pregunta: "¿Crear proyecto desde este estimado?"
7. Admin acepta
8. Sistema auto-crea proyecto:
   ├─ Nombre del proyecto: [Cliente sugiere o admin decide]
   ├─ Cliente: [Auto-asignado del estimado]
   ├─ Presupuesto: [Total del estimado]
   ├─ Estimado vinculado: KP1000
   └─ Estado: Created

Escenario B - Vinculación Manual (Raro):
1. Proyecto creado primero (urgencia)
2. Estimado creado después (documentación)
3. Admin vincula manualmente:
   └─ Proyecto → Campo: "Estimado relacionado"
   └─ Selecciona KP1000 del dropdown
4. Vinculación establecida
```

**Beneficios de Vinculación:**
```
Cuando estimado está vinculado:
├─ Proyecto conoce presupuesto original
├─ Invoice Builder puede cargar líneas del estimado
├─ Tracking: Estimado → Proyecto → Factura
├─ Comparación: Estimado vs Real
└─ Historial completo documentado

Vista en proyecto:
"Proyecto creado desde Estimado KP1000
Ver estimado original [link]"
```

**Estimados Sin Proyecto:**
```
Pueden existir estimados no vinculados:
├─ Cliente solicitó cotización pero no aceptó
├─ Estimado en proceso de negociación
├─ Cliente aún no decide
└─ Estimado rechazado

Estados de estos estimados:
- Sent (enviado, esperando respuesta)
- Rejected (cliente rechazó)
- Draft (aún trabajando en él)
```

---

### 📌 FUNCIÓN 7.5 - Calcular Total del Estimado

**Cálculo del Total:**
```
Total = SUM(precio de todas las líneas)

Ejemplo:
Línea 1: $2,000
Línea 2: $5,000
Línea 3: $8,000
Línea 4: $12,000
─────────────────
TOTAL: $27,000
```

**Sin Cálculos Complejos en Sistema:**
```
Sistema NO calcula:
❌ Markup automático
❌ Contingencias
❌ Profit margins
❌ Labor rates × hours
❌ Material costs + markup

Admin ya hizo todos los cálculos externamente:
"Hago los estimados con AI fuera de la app
y ya solo lo traslado ahí"

Sistema solo:
✅ Almacena precios finales
✅ Suma el total
✅ Formatea para presentación
✅ Control y seguimiento
```

**Actualización Automática:**
```
Total se recalcula cuando:
- Se agrega nueva línea
- Se edita precio de línea
- Se elimina línea
- Cualquier cambio en líneas

Update en tiempo real:
- JavaScript actualiza sin recargar
- Admin ve total mientras edita
```

---

### 📌 FUNCIÓN 7.6 - Cambiar Estado del Estimado

**Estados Disponibles:**
```
Draft (Borrador):
├─ Estimado en creación
├─ Admin aún trabajando en él
├─ No visible para cliente
├─ Editable sin restricciones
└─ No afecta reportes

Sent (Enviado):
├─ Estimado enviado al cliente
├─ Email con PDF enviado
├─ Esperando respuesta del cliente
├─ Ya no editable (sin versioning)
└─ Tracking de visualización

Approved (Aprobado):
├─ Cliente acepta el estimado
├─ Admin marca como aprobado
├─ Trigger para crear proyecto
├─ Locked (no editable)
└─ Base para facturación

Rejected (Rechazado):
├─ Cliente rechaza el estimado
├─ No se convertirá en proyecto
├─ Documentado para referencia
├─ Posible crear nuevo estimado revisado
└─ Análisis de por qué se rechazó
```

**Transiciones de Estado:**
```
Flujo normal:
Draft → Sent → Approved → [Auto-create Project]

Flujo con rechazo:
Draft → Sent → Rejected

Vuelta a trabajo:
Sent → Draft (si cliente pide cambios)
└─ Admin puede editar
└─ Re-enviar cuando esté listo
```

**Cambio de Estado:**
```
Manual (Admin controla):

Draft → Sent:
- Admin click "Enviar al Cliente"
- Sistema genera PDF
- Envía email
- Cambia estado automáticamente

Sent → Approved:
- Admin recibe confirmación del cliente
- Admin marca como "Approved"
- Sistema pregunta si crear proyecto

Sent → Rejected:
- Cliente informa que no acepta
- Admin marca como "Rejected"
- Admin agrega razón (opcional)

Sent → Draft:
- Cliente pide cambios
- Admin click "Volver a Draft"
- Puede editar y re-enviar
```

**Cliente NO Aprueba en Sistema:**
```
Actualmente:
- Cliente recibe PDF por email
- Cliente responde por email/teléfono
- Admin marca estado manualmente

Futuro (mejora posible):
- Cliente puede aprobar online
- Firma digital
- Auto-cambio de estado
- Notificación a admin
```

---

### 📌 FUNCIÓN 7.7 - Convertir Estimado en Factura

**Ya Documentado en Módulo 6 (Invoice Builder)**

Resumen del flujo:
```
1. Estimado aprobado: KP1000
2. Proyecto creado desde estimado
3. Trabajo completado (o por etapas)
4. Admin crea factura
5. Invoice Builder ofrece:
   "Cargar líneas de Estimado KP1000"
6. Admin acepta
7. Todas las líneas del estimado se copian
8. Admin puede agregar COs
9. Admin envía factura al cliente
```

**Facturación por Etapas/Milestones:**
```
"El estimado puede generar múltiples facturas"

Escenario - Proyecto grande facturado por etapas:

Estimado KP1000: $50,000 total
├─ Fase 1: Preparación y demo
├─ Fase 2: Estructura y framing
├─ Fase 3: MEP (electrical, plumbing)
├─ Fase 4: Finishes
└─ Fase 5: Final y cleanup

Facturación:
├─ Invoice KP10001IS01: $10,000 (Fase 1) - 20%
├─ Invoice KP10001IS02: $15,000 (Fase 2) - 30%
├─ Invoice KP10001IS03: $10,000 (Fase 3) - 20%
├─ Invoice KP10001IS04: $12,000 (Fase 4) - 24%
└─ Invoice KP10001IS05: $3,000 (Fase 5) - 6%

Total facturado: $50,000 ✅
```

**Ventajas de Múltiples Facturas:**
```
1. Cash flow más constante
2. Cliente paga por progreso
3. Menor riesgo financiero
4. Tracking de milestones
5. Flexibilidad en pagos
```

---

### 📌 FUNCIÓN 7.8 - Ver Historial de Estimados

**Organización por Secciones:**
```
"Los estimados tiene su sección de estimados:
- Los que se han creado
- Los enviados
- Los aprobados
- Los rechazados"

Dashboard de Estimados:

┌─────────────────────────────────────────────────┐
│ 📊 DASHBOARD DE ESTIMADOS                       │
├─────────────────────────────────────────────────┤
│ Tabs:                                           │
│ [Todos] [Draft] [Enviados] [Aprobados] [Rechazados]│
└─────────────────────────────────────────────────┘

Tab "Enviados" - Requieren Acción:
┌─────────────────────────────────────────────────┐
│ KP1005 │ María González  │ $35,000 │ 5 días    │
│ KP1003 │ John Smith      │ $28,000 │ 12 días   │
│ KP1001 │ Ana Pérez       │ $15,000 │ 20 días   │
├─────────────────────────────────────────────────┤
│ 3 estimados esperando respuesta                 │
└─────────────────────────────────────────────────┘

Tab "Aprobados" - Para Crear Proyectos:
┌─────────────────────────────────────────────────┐
│ KP1004 │ Carlos Ruiz     │ $45,000 │ ✅ Proyecto│
│ KP1002 │ Laura Méndez    │ $32,000 │ ⏳ Pendiente│
├─────────────────────────────────────────────────┤
│ 2 aprobados - 1 proyecto creado                 │
└─────────────────────────────────────────────────┘

Tab "Rechazados" - Análisis:
┌─────────────────────────────────────────────────┐
│ KP1000 │ Ivan Stanley    │ $55,000 │ Muy caro  │
│ KP0999 │ Pedro López     │ $18,000 │ Timeline  │
├─────────────────────────────────────────────────┤
│ 2 rechazados - revisar pricing                  │
└─────────────────────────────────────────────────┘
```

**Filtros Adicionales:**
```
Además de tabs por estado:

Por Cliente:
├─ Dropdown de todos los clientes
└─ Ver estimados de cliente específico

Por Fecha:
├─ Este mes
├─ Últimos 3 meses
├─ Este año
└─ Rango personalizado

Por Monto:
├─ < $10,000
├─ $10,000 - $30,000
├─ $30,000 - $50,000
├─ > $50,000

Por Conversión:
├─ Convertidos a proyecto
├─ No convertidos aún
└─ Todos
```

**Métricas del Dashboard:**
```
Resumen general:

Total de estimados: 125
├─ Draft: 8
├─ Enviados: 15 (esperando respuesta)
├─ Aprobados: 78 (62% win rate)
└─ Rechazados: 24 (19% loss rate)

Valor total estimado: $2,450,000
├─ Aprobados: $1,850,000 (76%)
├─ Pendientes: $425,000 (17%)
└─ Rechazados: $175,000 (7%)

Tasa de conversión: 76%
Tiempo promedio de respuesta: 8 días
Estimado promedio: $19,600
```

---

### 📌 FUNCIÓN 7.9 - Agregar Link de Takeoff

**Concepto de Takeoff/Marked Plans:**
```
"El link de Takeoff o Marked Plans es de Dropbox,
es un link a un alojamiento donde subo archivos pesados,
planos de construcción que son muy pesados para subirlo
a la app o no quiero que la app se sature lenta"

Razón de usar Dropbox:
├─ Planos de construcción = archivos muy pesados (50-200 MB)
├─ Múltiples planos por proyecto
├─ No saturar base de datos de la app
├─ Dropbox maneja archivos grandes eficientemente
└─ Cliente puede descargar directamente
```

**Interface de Links:**
```
"Hay un espacio donde se agrega el link de los planos
marcados o un archivo, debe de tener el icono de PDF
y un título que diga 'Marked Plans Info Click',
así será más visible para que ellos puedan ver eso"

Vista en Estimado:

┌────────────────────────────────────────────────┐
│ 📄 PLANOS Y DOCUMENTOS                         │
├────────────────────────────────────────────────┤
│ [📄 PDF] Marked Plans Info Click               │
│          https://dropbox.com/s/abc123...       │
│                                                │
│ [📄 PDF] Structural Plans                      │
│          https://dropbox.com/s/def456...       │
│                                                │
│ [📄 PDF] Electrical Layout                     │
│          https://dropbox.com/s/ghi789...       │
│                                                │
│ [+ Agregar Nuevo Link]                         │
└────────────────────────────────────────────────┘
```

**Agregar Links:**
```
"Lo único que Admin agregará son los links y puede
agregar más de un icono de PDF por si son varios documentos"

Formulario:

┌────────────────────────────────────────────────┐
│ Agregar Documento                              │
├────────────────────────────────────────────────┤
│ Título:                                        │
│ [Marked Plans Info Click                     ] │
│                                                │
│ Link de Dropbox:                               │
│ [https://dropbox.com/s/abc123...             ] │
│                                                │
│ Tipo de Documento: [Takeoff/Plans ▼]          │
│ ├─ Takeoff/Marked Plans                        │
│ ├─ Structural Plans                            │
│ ├─ Electrical Layout                           │
│ ├─ Plumbing Plans                              │
│ ├─ Site Plans                                  │
│ └─ Other                                       │
│                                                │
│ [Guardar] [Cancelar]                           │
└────────────────────────────────────────────────┘
```

**Múltiples Documentos:**
```
Admin puede agregar varios links:
├─ Planos arquitectónicos
├─ Planos estructurales
├─ Planos eléctricos
├─ Planos de plomería
├─ Takeoff marcado
├─ Especificaciones
└─ Cualquier documento de referencia

Cada uno con:
- Icono de PDF visible
- Título descriptivo
- Link directo a Dropbox
- Click para abrir en nueva pestaña
```

**Visibilidad en PDF del Estimado:**
```
PDF incluye sección:

┌────────────────────────────────────────────────┐
│ PLANOS Y DOCUMENTOS DE REFERENCIA              │
├────────────────────────────────────────────────┤
│ 📄 Marked Plans Info Click                     │
│    https://dropbox.com/s/abc123...             │
│                                                │
│ 📄 Structural Plans                            │
│    https://dropbox.com/s/def456...             │
│                                                │
│ Por favor revise estos documentos para         │
│ detalles completos del scope de trabajo        │
└────────────────────────────────────────────────┘

Cliente puede hacer click en links para ver planos
```

**Mejora Identificada:**
```
⚠️ Validación de Links:
- Verificar que link sea válido
- Preview de Dropbox embebido (opcional)
- Icon según tipo de archivo (PDF, DWG, etc.)
- Warning si link expiró o no es accesible
```

---

### 📌 FUNCIÓN 7.10 - Generar PDF del Estimado

**Diseño Premium - Hecho para Vender:**
```
"El estimado es muy similar a los invoices, solo está
muy bonito visualmente y luce inigualable, el formato
de letras, colores, todo es muy elegante, un estimado
hecho para vender"

Filosofía:
- Primera impresión crítica
- Profesionalismo extremo
- Diferenciación de competencia
- Cliente se siente confiado
- Visual elegante y moderno
```

**Template Elegante:**
```
┌───────────────────────────────────────────────────────┐
│                                                       │
│   🎨 KIBRAY CONSTRUCTION                              │
│   Premium Residential & Commercial Painting           │
│   ─────────────────────────────────────────────────   │
│   License #: [Number] | Insured & Bonded             │
│                                                       │
├───────────────────────────────────────────────────────┤
│                                                       │
│              PROFESSIONAL ESTIMATE                    │
│                                                       │
├───────────────────────────────────────────────────────┤
│ Estimate #: KP1000                                    │
│ Date: November 12, 2024                               │
│ Valid Until: December 12, 2024 (30 days)             │
├───────────────────────────────────────────────────────┤
│                                                       │
│ PREPARED FOR:                                         │
│ Ivan Stanley                                          │
│ [Address]                                             │
│ [Phone] | [Email]                                     │
│                                                       │
│ PROJECT LOCATION:                                     │
│ Villa Moderna - 123 Luxury Lane                       │
│ Beverly Hills, CA 90210                               │
│                                                       │
├───────────────────────────────────────────────────────┤
│                                                       │
│ SCOPE OF WORK                                         │
│                                                       │
│ 1. EXTERIOR WINDOW PAINTING                  $2,000   │
│    Surface preparation, premium primer,               │
│    two coats exterior paint, frames & grilles         │
│                                                       │
│ 2. MAIN ENTRANCE DOORS                       $5,000   │
│    Sanding, wood repair, staining,                    │
│    three coats polyurethane finish                    │
│                                                       │
│ 3. ROOF REPAIR & PAINTING                    $8,000   │
│    Leak repair, surface preparation,                  │
│    elastomeric coating, 10-year warranty              │
│                                                       │
│ 4. INTERIOR COMPLETE                        $12,000   │
│    All walls & ceilings, premium paint,               │
│    includes trim, doors, baseboards                   │
│                                                       │
├───────────────────────────────────────────────────────┤
│                                         Subtotal: $27,000│
│                                         Tax (0%): $0     │
│                                                       │
│                              TOTAL INVESTMENT: $27,000│
│                                                       │
├───────────────────────────────────────────────────────┤
│                                                       │
│ 📄 PROJECT DOCUMENTS                                  │
│                                                       │
│ 📄 Marked Plans Info Click                            │
│    https://dropbox.com/s/abc123...                    │
│                                                       │
│ 📄 Color Specifications                               │
│    https://dropbox.com/s/def456...                    │
│                                                       │
├───────────────────────────────────────────────────────┤
│                                                       │
│ WHAT'S INCLUDED:                                      │
│ ✓ Premium Benjamin Moore paints                      │
│ ✓ Complete surface preparation                        │
│ ✓ Professional craftsmanship                          │
│ ✓ Clean workspace daily                               │
│ ✓ Final walkthrough & approval                        │
│ ✓ 2-year warranty on workmanship                      │
│                                                       │
│ PAYMENT TERMS:                                        │
│ • 30% deposit upon acceptance                         │
│ • 40% at 50% completion                               │
│ • 30% upon final completion                           │
│                                                       │
│ TIMELINE:                                             │
│ • Estimated start: 7 days after deposit               │
│ • Estimated duration: 3-4 weeks                       │
│ • Weather-dependent for exterior work                 │
│                                                       │
│ This estimate is valid for 30 days from date issued   │
│                                                       │
├───────────────────────────────────────────────────────┤
│                                                       │
│ Questions? We're here to help!                        │
│                                                       │
│ 📧 admin@kibray.com                                   │
│ 📱 (555) 123-4567                                     │
│ 🌐 www.kibray.com                                     │
│                                                       │
│ Thank you for considering Kibray Construction!        │
│ We look forward to transforming your space.           │
│                                                       │
└───────────────────────────────────────────────────────┘
```

**Características Visuales Premium:**
```
Tipografía:
├─ Headers: Montserrat Bold (moderno, elegante)
├─ Cuerpo: Open Sans (legible, profesional)
├─ Números: Roboto Mono (claridad en precios)
└─ Tamaños jerárquicos claros

Colores:
├─ Primario: Azul navy profundo (#1a2332)
├─ Acento: Dorado elegante (#d4af37)
├─ Texto: Gris oscuro (#2d3748)
├─ Background: Blanco puro (#ffffff)
└─ Secciones: Gris muy claro (#f7fafc)

Layout:
├─ Márgenes amplios (profesional)
├─ Espaciado generoso entre secciones
├─ Íconos modernos y minimalistas
├─ Líneas sutiles para separación
└─ Balance visual perfecto

Branding:
├─ Logo grande y prominente
├─ Colores corporativos consistentes
├─ Tagline profesional
├─ Información de licencias visible
└─ Elementos de confianza (insured, bonded)
```

**Diferenciadores vs Invoice:**
```
Invoice (funcional):
- Enfoque en números
- Secciones de pago claras
- Balance y historial de pagos
- Formal y directo

Estimate (vende):
- Enfoque en valor y beneficios
- Describe qué incluye cada item
- Timeline y proceso claros
- Garantías prominentes
- Testimonios (futuro)
- Elementos de confianza
- Validez de la oferta
- Términos y condiciones atractivos
```

**Elementos Únicos del Estimate:**
```
"What's Included" section:
- Lista de beneficios con checkmarks
- Materiales premium destacados
- Garantías mencionadas
- Proceso de trabajo explicado

Timeline clara:
- Cuándo empieza
- Cuánto dura
- Qué esperar

Payment terms amigables:
- Desglose por etapas
- No todo upfront
- Cliente siente control

Validez de oferta:
- "Valid for 30 days"
- Crea urgencia suave
- Profesional

Call to action:
- Contacto fácil
- Múltiples formas de comunicar
- Invitación a preguntar
```

**Generación del PDF:**
```
Tecnología:
- WeasyPrint con CSS premium
- Fuentes embebidas
- Alta resolución
- Tamaño optimizado (~500KB)

Trigger:
- Al enviar estimado (adjunto en email)
- Al hacer click "Descargar PDF"
- Al cliente acceder vía link seguro

Almacenamiento:
- /media/estimates/2024/11/KP1000.pdf
- Accesible vía link único
- No expira (archivo permanente)
```

**Mejora CRÍTICA Identificada:**
```
🔴 PRIORIDAD ALTA: Premium Estimate Template

Componentes a diseñar:
1. Template HTML/CSS elegante y moderno
2. Tipografía premium (Google Fonts)
3. Color scheme corporativo profesional
4. Iconos modernos (Font Awesome Pro o custom)
5. Layout responsive para diferentes tamaños
6. Sección "What's Included" con checkmarks
7. Timeline visual clara
8. Payment terms profesionales
9. Branding consistente con identidad
10. Multiple templates para elegir

Objetivo:
"El mejor estimado que el cliente haya visto nunca"
```

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 7**

### Mejoras CRÍTICAS:
1. 🔴 **Premium Estimate Template**
   - Diseño visual excepcional
   - Tipografía y colores elegantes
   - Layout moderno y profesional
   - "Hecho para vender"

### Mejoras Importantes:
2. ⚠️ Generación automática de código (KP1000, KP1001...)
3. ⚠️ Dashboard organizado por estados (Draft, Sent, Approved, Rejected)
4. ⚠️ Múltiples links de Dropbox con íconos PDF
5. ⚠️ Validación de links de Dropbox
6. ⚠️ Preview de documentos embebido (opcional)
7. ✅ Auto-creación de proyecto desde estimado aprobado
8. ✅ Tracking de conversión (win rate, loss rate)
9. ✅ Métricas de performance (tiempo de respuesta, valor promedio)
10. ⚠️ Cliente puede aprobar online (futuro) con firma digital

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)

**Total documentado: 72/250+ funciones (29%)**

**Pendientes:**
- ⏳ Módulo 8: Órdenes de Cambio (11 funciones)
- ⏳ Módulo 9: Presupuesto/Earned Value (14 funciones) - CRÍTICO
- ⏳ Módulos 10-27: 160+ funciones

---

## ✅ **MÓDULO 8: ÓRDENES DE CAMBIO (CHANGE ORDERS)** (11/11 COMPLETO)

### 🔄 **FILOSOFÍA DE CHANGE ORDERS**

**Concepto Crítico:**
```
Change Orders son la realidad de construcción:
- Cliente cambia de opinión
- Se descubre trabajo no previsto
- Se agrega scope adicional
- Se remueve trabajo original
- Cliente quiere mejoras

Dos tipos de clientes:
1. Nuevos: CO requiere firma antes de empezar
2. Confianza: "Solo creamos el CO y los vamos alimentando"
```

---

### 📌 FUNCIÓN 8.1 - Crear Nueva Orden de Cambio

**Permisos de Creación:**
```
Tres orígenes de COs:

1. Admin crea CO:
├─ Acceso completo
├─ Crea CO directamente
├─ Estado inicial: Approved (auto-aprobado)
└─ Puede empezar trabajo inmediatamente

2. PM crea CO:
├─ Puede crear CO
├─ Estado inicial: Approved (auto-aprobado)
├─ "El PM puede crear cambios de órdenes y los puede
│   aprobar para poder hacer su trabajo"
├─ No requiere aprobación adicional
└─ Razón: PM está en sitio, necesita actuar rápido

3. Cliente crea CO (submit):
├─ Cliente puede solicitar cambio
├─ Estado inicial: Pending
├─ Requiere aprobación de Admin
├─ Admin revisa → Aprueba/Rechaza
└─ Si aprueba → Cliente puede firmar (ideal)
```

**Ubicación de Creación:**
```
"Se crean dentro de un proyecto"

Navegación:
Proyecto → Change Orders → Nuevo CO

Vinculación automática:
- CO siempre vinculado a proyecto específico
- No hay COs globales sin proyecto
- Tracking por proyecto
```

**Escenarios de Uso:**

**Escenario 1 - Cliente Nuevo (Proceso Formal):**
```
"Yo pregunto al cliente y él me dice que sí,
yo puedo crear un CO y enviárselo para pedir que lo firme,
es lo ideal"

Proceso:
1. Durante trabajo, PM identifica cambio necesario
2. PM contacta cliente: "Necesitamos agregar X"
3. Cliente acepta verbalmente
4. PM crea CO en sistema
5. Sistema genera PDF del CO
6. PM envía a cliente para firma digital
7. Cliente firma
8. CO marcado como Approved con firma
9. Trabajo puede proceder
10. CO se factura después
```

**Escenario 2 - Cliente de Confianza (Streamlined):**
```
"A clientes viejos que ya confían en nosotros,
solo creamos el cambio de orden y los vamos alimentando"

Proceso:
1. PM identifica trabajo adicional necesario
2. PM crea CO en sistema
3. CO auto-aprobado (no requiere firma)
4. PM asigna empleados al CO
5. Trabajo procede inmediatamente
6. Tiempo y materiales se registran
7. Al final, CO se incluye en factura
8. Cliente confía en el proceso

Razón:
- Relación establecida
- Historial de confianza
- Velocidad de ejecución
- Menos burocracia
```

**Escenario 3 - Time & Material (T&M):**
```
"Dijeron 'quiero esto' y eso se agrega por tiempo y material"

Proceso:
1. Cliente pide trabajo adicional
2. Cliente dice: "No necesito costo previo, solo háganlo"
3. PM crea CO con estimado aproximado o sin monto
4. Trabajo procede
5. Tiempo de empleados se registra al CO
6. Materiales se asignan al CO
7. Al terminar: Total real = Labor + Materiales
8. Cliente paga costo real (no estimado fijo)
```

---

### 📌 FUNCIÓN 8.2 - Generar Número de CO Automático

**Sistema de Numeración:**
```
Formato: CO + [CLIENT_INITIALS] + [SEQUENTIAL_NUMBER]

"Se crea CO + dos primeras letras del nombre del cliente
+ el número secuencial del CO"

Ejemplos:

Cliente: Ivan Stanley
Proyecto: Villa Moderna
├─ Primer CO: CO-IS-001
├─ Segundo CO: CO-IS-002
├─ Tercer CO: CO-IS-003

Cliente: María González
Proyecto: Casa Residencial
├─ Primer CO: CO-MG-001
├─ Segundo CO: CO-MG-002

Cliente: John Smith
Proyecto: Remodelación
├─ Primer CO: CO-JS-001
```

**Generación Automática:**
```python
def generate_co_number(project):
    client_name = project.client.name
    # Extract initials
    names = client_name.split()
    initials = ''.join([n[0].upper() for n in names[:2]])
    # "Ivan Stanley" -> "IS"
    
    # Count existing COs for this project
    co_count = ChangeOrder.objects.filter(project=project).count()
    next_number = co_count + 1
    
    # Build CO number
    co_number = f"CO-{initials}-{next_number:03d}"
    # "CO-IS-001"
    
    return co_number
```

**Secuencia por Proyecto:**
```
Importante: Numeración es por PROYECTO, no global

Proyecto A (Ivan Stanley):
- CO-IS-001, CO-IS-002, CO-IS-003

Proyecto B (Ivan Stanley - otro proyecto):
- CO-IS-001, CO-IS-002 (reinicia por proyecto)

Razón:
- COs específicos de cada proyecto
- Fácil identificación
- No confusión entre proyectos
```

---

### 📌 FUNCIÓN 8.3 - Describir el Cambio Solicitado

**Información Requerida:**
```
"Se necesita saber qué se agrega o se remueve"

Descripción completa incluye:

1. Qué se solicita:
   ├─ Ejemplo: "Agregar pintar un ventilador"
   ├─ "Remover pared entre cocina y comedor"
   └─ "Cambiar color de pintura en sala principal"

2. Razón del cambio (opcional):
   ├─ "Cliente cambió de opinión"
   ├─ "Problema estructural encontrado"
   ├─ "Mejora solicitada por diseñador"
   └─ "Trabajo no considerado en estimado original"

3. Detalles técnicos:
   ├─ Colores si es necesario
   ├─ Materiales específicos
   ├─ Especificaciones técnicas
   └─ Cualquier requerimiento especial
```

**Información Definida por PM/Admin:**
```
"Esos detalles los define el PM o Admin"

Campos adicionales:

1. Descripción detallada:
   - Qué trabajo específicamente
   - Cómo se hará
   - Qué materiales se usarán

2. Colores (si aplica):
   - Benjamin Moore Swiss Coffee
   - RAL 9016 Traffic White
   - Custom color match

3. Advertencias:
   - "Requiere mover muebles del cliente"
   - "Trabajo ruidoso - avisar a vecinos"
   - "Requiere corte de electricidad temporal"
   - "Puede afectar uso de la cocina por 2 días"

4. Asistencia necesaria:
   - "Requiere electricista certificado"
   - "Necesita dos personas mínimo"
   - "Requiere equipo especial (scaffold)"
   - "Subcontratista de plomería necesario"

5. Cuándo se realizará:
   "Así se avisa al resto del equipo"
   - Fecha estimada de inicio
   - Duración estimada
   - Coordinación con otros trabajos
   - Notificación al equipo
```

**Formulario de Creación:**
```
┌────────────────────────────────────────────────┐
│ Crear Change Order                             │
├────────────────────────────────────────────────┤
│ Proyecto: Villa Moderna (auto-fill)            │
│ Cliente: Ivan Stanley (auto-fill)              │
│ Número: CO-IS-003 (auto-generado)              │
│                                                │
│ ¿Qué se solicita?                              │
│ [Agregar pintura de ventiladores de techo     │
│  en todas las habitaciones]                   │
│                                                │
│ Tipo de Cambio:                                │
│ (•) Agregar trabajo (+)                        │
│ ( ) Remover trabajo (-)                        │
│ ( ) Modificar trabajo existente               │
│                                                │
│ Descripción Detallada:                         │
│ [Pintar 5 ventiladores de techo existentes.   │
│  Incluye desmontaje, limpieza, preparación,   │
│  2 capas de pintura, y reinstalación.         │
│  Color: Benjamin Moore Simply White]          │
│                                                │
│ Monto Estimado (opcional):                     │
│ [$500.00                                      ]│
│ ( ) Time & Material (sin monto fijo)          │
│                                                │
│ Advertencias:                                  │
│ [Se requerirá apagar ventiladores durante     │
│  trabajo. Duración 1 día por habitación]      │
│                                                │
│ Asistencia Necesaria:                          │
│ [Electricista para desconectar/reconectar     │
│  ventiladores de manera segura]               │
│                                                │
│ Fecha Estimada:                                │
│ Inicio: [Nov 20, 2024]                        │
│ Duración: [3 días]                            │
│                                                │
│ Impacto en Cronograma:                         │
│ [☑] Insertar en cronograma existente          │
│ Posición: [Después de "Pintura de paredes"]  │
│                                                │
│ Notas Adicionales:                             │
│ [Cliente solicitó después de ver ventiladores │
│  sucios. Precio acordado verbalmente.]        │
│                                                │
│ [Crear CO] [Crear y Enviar a Cliente] [❌]    │
└────────────────────────────────────────────────┘
```

---

### 📌 FUNCIÓN 8.4 - Establecer Monto del Cambio

**Tipos de Monto:**

**Positivos (Agregar Trabajo):**
```
Monto > $0

Ejemplos:
- Agregar habitación: +$15,000
- Pintar ventiladores: +$500
- Cambiar pisos: +$8,000
- Trabajo adicional no previsto: +$3,500

Impacto:
- Aumenta presupuesto del proyecto
- Cliente pagará más
- Se factura como línea adicional
```

**Negativos (Remover Trabajo):**
```
Monto < $0

"Los cambios negativos son los cambios en donde
se remueven paredes, puertas, del scope original,
por ejemplo se marca como remover, y eso hace que
se reduzca el presupuesto o estimado aprobado"

Ejemplos:
- Remover pared: -$2,000
- No pintar garage (scope original): -$1,500
- Cancelar trabajo de deck: -$5,000

Impacto:
- Reduce presupuesto del proyecto
- Cliente paga menos
- Crédito en factura
- Documentación del cambio
```

**Sin Monto (Time & Material):**
```
"Dijeron 'quiero esto' y eso se agrega por tiempo y material"

Monto = $0 inicial (o TBD)

Proceso:
1. CO creado sin monto fijo
2. Trabajo procede
3. Tiempo de empleados registrado
4. Materiales asignados
5. Al terminar:
   Total_Real = (Horas × Tarifa) + Materiales
6. Ese total se factura

Ventaja:
- No necesita estimado previo
- Cliente acepta costo real
- Más rápido para empezar
- Transparencia total
```

**Cambios de $0 (Solo Scope):**
```
Monto = $0 (no afecta precio)

Ejemplos:
- Cambio de color (mismo costo)
- Reorganizar schedule
- Cambio de método (misma labor)
- Ajuste técnico sin costo

Razón:
- Documentación del cambio
- Aprobación formal
- Tracking de modificaciones
- No impacto financiero
```

**Quién Establece el Monto:**
```
PM o Admin calculan:

Proceso:
1. PM evalúa trabajo requerido
2. Calcula labor:
   - Horas estimadas × Tarifa
   - Ejemplo: 10h × $50/h = $500

3. Calcula materiales:
   - Lista materiales necesarios
   - Precios de proveedores
   - Ejemplo: Pintura $80, supplies $20 = $100

4. Aplica markup (opcional):
   - Labor markup: 100% ($500 → $1,000)
   - Material markup: 15% ($100 → $115)

5. Total CO: $1,115
6. Redondea: $1,200 (pricing estratégico)

O usa pricing basado en experiencia:
"5 ventiladores normalmente cuestan $100 c/u = $500"
```

---

### 📌 FUNCIÓN 8.5 - Cambiar Estado del CO

**Estados del Change Order:**
```
Pending (Pendiente):
├─ CO creado por cliente (submit)
├─ Esperando aprobación de Admin
├─ No se puede trabajar aún
└─ Requiere revisión

Approved (Aprobado):
├─ CO aprobado para trabajo
├─ PM/Admin auto-aprobado, o
├─ Admin aprobó CO de cliente
├─ Puede proceder trabajo
└─ Empleados pueden asignar tiempo

Rejected (Rechazado):
├─ CO no aprobado
├─ No se hará el trabajo
├─ Razón documentada
└─ Cliente notificado

In Progress (En Progreso):
├─ Trabajo del CO ha comenzado
├─ Empleados trabajando en CO
├─ Tiempo y materiales registrándose
└─ Tracking activo

Completed (Completado):
├─ Trabajo del CO terminado
├─ Listo para facturar
├─ Total real calculado
└─ Cliente puede ver resultado
```

**Flujo de Estados:**
```
Flujo Cliente Submit:
Pending → (Admin revisa) → Approved → In Progress → Completed
                        ↘ Rejected

Flujo PM/Admin Crea:
Approved (auto) → In Progress → Completed

Flujo T&M:
Approved → In Progress (tracking tiempo) → Completed (total calculado)

Flujo Rechazado:
Pending → Rejected (no procede)
```

**Transiciones:**
```
Automáticas:
├─ PM/Admin crea → Approved (inmediato)
├─ Empleado hace clock in a CO → In Progress
└─ PM marca completado → Completed

Manuales:
├─ Admin aprueba CO de cliente → Approved
├─ Admin rechaza CO → Rejected
└─ PM marca inicio → In Progress
```

**Proceso de Aprobación Multi-nivel:**
```
"En los cambios de órdenes el Admin y PM los aprueban"

Contexto:
- PM está en sitio
- PM ve trabajo necesario
- PM pregunta a cliente
- Cliente acepta verbalmente

Dos enfoques:

Enfoque 1 - Clientes Nuevos:
1. PM crea CO
2. PM envía a cliente para firma
3. Cliente firma digitalmente
4. Estado → Approved con firma
5. Trabajo procede

Enfoque 2 - Clientes de Confianza:
1. PM crea CO
2. Auto-approved (no firma necesaria)
3. Trabajo procede
4. Se factura después
5. Cliente paga sin cuestionar
```

---

### 📌 FUNCIÓN 8.6 - Vincular CO con Proyecto

**Vinculación Obligatoria:**
```
"Sí, los CO siempre están vinculados a un proyecto"

No hay COs sin proyecto:
- CO se crea DESDE el proyecto
- CO hereda información del proyecto
- CO afecta presupuesto del proyecto
- CO se factura en invoices del proyecto

Relación 1:N:
- Un proyecto puede tener múltiples COs
- Un CO pertenece a un solo proyecto
```

**Auto-vinculación:**
```
Al crear CO desde proyecto:
1. Admin/PM está en proyecto Villa Moderna
2. Click "Nuevo Change Order"
3. Sistema auto-llena:
   ├─ Proyecto: Villa Moderna
   ├─ Cliente: Ivan Stanley
   └─ Número: CO-IS-003 (secuencial del proyecto)
4. No puede cambiar proyecto (vinculación fija)
```

**Vista en Proyecto:**
```
Proyecto Villa Moderna:
├─ Información general
├─ Budget
├─ Schedule
├─ Change Orders: (sección dedicada)
│  ├─ CO-IS-001: Habitación extra (+$15,000) ✅ Completed
│  ├─ CO-IS-002: Eliminar garage (-$2,000) ✅ Completed
│  ├─ CO-IS-003: Ventiladores (+$500) 🔄 In Progress
│  └─ [+ Nuevo Change Order]
└─ Finances
```

---

### 📌 FUNCIÓN 8.7 - Registrar Quién Solicitó el Cambio

**Tracking de Origen:**
```
"Sí, se registra quién lo creó"

Sistema registra:
├─ created_by: User (PM, Admin, Cliente)
├─ created_at: Timestamp
├─ requested_by: String (origen real)
└─ reason: String (por qué se solicitó)
```

**Flujos por Origen:**

**1. Cliente Solicita:**
```
"Si lo crea el cliente tiene que pasar por
approved por el Admin"

Proceso:
1. Cliente accede a portal del proyecto
2. Cliente crea solicitud de CO:
   - Describe lo que quiere
   - Opcionalmente agrega fotos
   - Submit
3. Sistema crea CO:
   - Estado: Pending
   - created_by: Cliente
   - requested_by: "Cliente (Ivan Stanley)"
4. Admin recibe notificación
5. Admin revisa:
   - Calcula costo
   - Evalúa impacto en timeline
   - Aprueba o rechaza
6. Si aprueba:
   - Estado: Approved
   - Cliente puede firmar (opcional)
   - Trabajo puede proceder
```

**2. PM Crea:**
```
"Si lo crea el PM o Admin se van directos"

Proceso:
1. PM identifica necesidad en sitio
2. PM crea CO en sistema:
   - Estado: Approved (auto)
   - created_by: PM
   - requested_by: "PM - trabajo necesario"
3. PM puede empezar trabajo inmediatamente
4. No requiere aprobación adicional

Razón:
"El PM puede crear cambios de órdenes y los puede
aprobar para poder hacer su trabajo"
- PM tiene autoridad en campo
- Necesita actuar rápido
- Confianza en juicio del PM
```

**3. Admin Crea:**
```
Proceso:
1. Admin crea CO (oficina o sitio)
2. Estado: Approved (auto)
3. created_by: Admin
4. requested_by: "Admin - [razón]"
5. Trabajo procede

Razones comunes:
- Trabajo no previsto descubierto
- Mejora sugerida al cliente
- Corrección de error en estimado
- Upgrade solicitado por diseñador
```

**Razones de Solicitud:**
```
Ejemplos de "requested_by":

Cliente:
- "Cliente solicitó cambio de color"
- "Cliente quiere agregar habitación"
- "Cliente eliminó trabajo de garage"

PM:
- "PM identificó daño estructural no previsto"
- "PM sugirió mejora técnica"
- "Trabajo necesario para código/inspección"

Admin:
- "Admin corrigió error en estimado original"
- "Descuento por trabajo reducido"
- "Upgrade aprobado por diseñador"

Problema:
- "Problema encontrado durante demolición"
- "Descubrimiento de daño por agua"
- "Código requiere trabajo adicional"
```

---

### 📌 FUNCIÓN 8.8 - Asignar Tiempo de Trabajo a CO

**Asignación de Empleados:**
```
PM asigna empleados a CO específico

Proceso:
1. CO-IS-003 aprobado (Ventiladores)
2. PM asigna:
   - Juan Pérez (Pintor)
   - María González (Helper)
3. Empleados ven CO en su lista de proyectos
4. Pueden hacer switch al CO cuando trabajen en él
```

**Switch Automático Disponible:**
```
"Los empleados pueden hacer switch siempre que haya
un CO dentro del proyecto, así evitamos pérdida de
tiempo por asignación"

Flujo del empleado:

1. Empleado hace clock in a Proyecto Villa Moderna
2. Trabajando en proyecto principal...
3. PM dice: "Ahora trabaja en CO-IS-003 (ventiladores)"
4. Empleado en app:
   └─ Click "Cambiar proyecto"
   └─ Ve opciones:
      ├─ Villa Moderna (principal)
      ├─ CO-IS-001 (habitación) - completed
      ├─ CO-IS-002 (garage) - completed
      └─ CO-IS-003 (ventiladores) - in progress
5. Selecciona CO-IS-003
6. Tiempo se registra al CO (no al proyecto principal)
7. Al terminar, puede regresar a proyecto principal
```

**Beneficio de Switch Flexible:**
```
Sin asignación previa requerida:
- Empleado puede switch a cualquier CO activo
- No necesita esperar a que PM asigne
- Reduce tiempo de idle
- PM puede dirigir trabajo verbalmente
- Sistema documenta tiempo correctamente

Validación:
- Solo COs en estado "Approved" o "In Progress"
- COs del proyecto actual
- Empleado asignado al proyecto
```

**Tracking de Tiempo por CO:**
```
Vista del CO:

CO-IS-003: Ventiladores (+$500)
├─ Presupuesto: $500
├─ Tiempo registrado:
│  ├─ Juan Pérez: 4h × $50 = $200
│  ├─ María González: 4h × $35 = $140
│  └─ Total Labor: $340
├─ Materiales: $80
├─ Total Real: $420
├─ Balance: $80 under budget ✅
└─ Estado: In Progress
```

---

### 📌 FUNCIÓN 8.9 - Asignar Gastos a CO

**Quién Puede Asignar:**
```
"Los PM y Admin pueden asignar gastos"

Proceso de asignación:
1. PM/Admin va a crear gasto
2. Formulario de gasto muestra:

   Asignar a:
   ( ) Proyecto principal: Villa Moderna
   (•) Change Order:
       [CO-IS-003: Ventiladores ▼]
       
   Opciones de COs:
   ├─ Proyecto Principal
   ├─ CO-IS-001: Habitación extra
   ├─ CO-IS-002: Eliminar garage
   └─ CO-IS-003: Ventiladores

3. PM selecciona CO-IS-003
4. Gasto se asigna directamente al CO
```

**Origen de Selección:**
```
"Ejemplo: van a agregar gastos y ahí seleccionan
de uno de los items de:
- Estimado aprobado, o
- Del budget, o
- Si hay un CO lo seleccionan de la lista,
así ese gasto tiene dirección"

Dropdown unificado:

Categorizar gasto:
[Seleccionar categoría ▼]
├─ PROYECTO PRINCIPAL:
│  ├─ Pintura de ventanas (Estimado)
│  ├─ Pintura de puertas (Estimado)
│  ├─ Labor (Budget)
│  └─ Materiales generales (Budget)
├─ CHANGE ORDERS:
│  ├─ CO-IS-001: Habitación extra
│  ├─ CO-IS-002: Eliminar garage
│  └─ CO-IS-003: Ventiladores
└─ Sin categoría

Gasto asignado tiene "dirección" clara
```

**Ejemplo Práctico:**
```
Escenario:
PM compra pintura para ventiladores (CO-IS-003)

1. PM va a Home Depot
2. Compra: Pintura $60, Brochas $20 = $80
3. PM registra gasto:
   ├─ Monto: $80
   ├─ Categoría: Materiales
   ├─ Asignar a: CO-IS-003 (Ventiladores)
   ├─ Descripción: "Pintura y brochas para ventiladores"
   └─ Recibo: [foto uploaded]
4. Gasto vinculado a CO-IS-003
5. Tracking actualizado:
   └─ CO-IS-003 Materiales: $80
```

---

### 📌 FUNCIÓN 8.10 - Tracking de Budget vs Real por CO

**Budget Definido (Algunos COs):**
```
CO con presupuesto fijo:

CO-IS-001: Agregar habitación
├─ Presupuesto Aprobado: $15,000
├─ Labor Real:
│  ├─ 150h × $50 = $7,500
├─ Materiales Real:
│  ├─ Framing: $2,500
│  ├─ Drywall: $1,800
│  ├─ Pintura: $900
│  ├─ Eléctrico: $1,200
│  └─ Total: $6,400
├─ Total Real: $13,900
├─ Balance: $1,100 under budget ✅
└─ Margen: 7.3%

Dashboard muestra:
- ✅ Verde: Dentro de presupuesto
- Proyección de finalización
- Ganancia esperada
```

**Time & Material (Otros COs):**
```
"No siempre hay un budget definido para los COs,
hay veces que solo se hace tracking Time + Materials"

CO-IS-003: Ventiladores (T&M)
├─ Presupuesto: TBD (Time & Material)
├─ Tracking:
│  ├─ Labor:
│  │  ├─ Juan: 4h × $50 = $200
│  │  └─ María: 4h × $35 = $140
│  ├─ Materiales: $80
│  └─ Total Actual: $420
├─ Cliente Pagará: $420 (costo real)
└─ Markup puede aplicarse al facturar

No comparación con budget (no hay budget fijo)
Solo tracking de costo real
```

**Vista de Tracking:**
```
Dashboard del CO:

┌────────────────────────────────────────────────┐
│ CO-IS-001: Agregar Habitación Extra            │
├────────────────────────────────────────────────┤
│ Estado: In Progress                            │
│ Tipo: Budget Fijo                              │
│                                                │
│ FINANCIERO:                                    │
│ Presupuesto: $15,000                           │
│ Gastado: $13,900 (93%)                         │
│ Restante: $1,100                               │
│                                                │
│ DESGLOSE:                                      │
│ Labor: $7,500 / $8,000 (94%) ✅                │
│ Materiales: $6,400 / $7,000 (91%) ✅           │
│                                                │
│ PROGRESO:                                      │
│ ████████████████░░░░ 80%                       │
│                                                │
│ TIEMPO REGISTRADO:                             │
│ Juan Pérez: 80h                                │
│ Pedro López: 70h                               │
│ Total: 150h                                    │
│                                                │
│ PRÓXIMOS PASOS:                                │
│ - Terminar instalación eléctrica               │
│ - Pintura final                                │
│ - Inspección                                   │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ CO-IS-003: Ventiladores (T&M)                  │
├────────────────────────────────────────────────┤
│ Estado: In Progress                            │
│ Tipo: Time & Material                          │
│                                                │
│ COSTO ACUMULADO:                               │
│ Labor: $340                                    │
│ Materiales: $80                                │
│ TOTAL: $420                                    │
│                                                │
│ MARKUP AL FACTURAR:                            │
│ Labor: $340 → $680 (100% markup)               │
│ Materiales: $80 → $92 (15% markup)             │
│ Total a Facturar: $772                         │
│                                                │
│ PROGRESO:                                      │
│ ████████░░░░░░░░░░░░ 40%                       │
│ 2 de 5 ventiladores completados                │
└────────────────────────────────────────────────┘
```

---

### 📌 FUNCIÓN 8.11 - Dashboard de Change Orders

**Vista Principal de COs por Proyecto:**
```
"Sí, un dashboard para ver dentro de cada proyecto
los CO, y toda la información relacionada a ellos
financiera y estados"

Proyecto Villa Moderna → Change Orders Tab:

┌────────────────────────────────────────────────────────────┐
│ 📊 CHANGE ORDERS DASHBOARD                                 │
├────────────────────────────────────────────────────────────┤
│ Resumen:                                                   │
│ Total COs: 3                                               │
│ Valor Total: +$13,500 (aprobados)                          │
│ Completados: 2 | En Progreso: 1 | Pendientes: 0          │
├────────────────────────────────────────────────────────────┤
│ 🟢 COMPLETADOS (2)                    Valor: +$13,000     │
├────────────────────────────────────────────────────────────┤
│ CO-IS-001 │ Habitación extra    │ $15,000 │ Real: $13,900│
│           │ Budget: ✅ $1,100 under                        │
│           │ Margen: 7.3%                                   │
│           │ Facturado: ✅ Invoice KP10001IS02              │
├────────────────────────────────────────────────────────────┤
│ CO-IS-002 │ Eliminar garage     │ -$2,000 │ Crédito      │
│           │ Facturado: ✅ Invoice KP10001IS02              │
├────────────────────────────────────────────────────────────┤
│ 🔵 EN PROGRESO (1)                   Valor: +$500         │
├────────────────────────────────────────────────────────────┤
│ CO-IS-003 │ Ventiladores (T&M)  │ TBD     │ Real: $420   │
│           │ Progreso: 40% (2 de 5)                         │
│           │ Labor: $340 | Mat: $80                         │
│           │ [Ver Detalles] [Marcar Completado]            │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ 💰 IMPACTO FINANCIERO                                      │
├────────────────────────────────────────────────────────────┤
│ Presupuesto Original: $50,000                              │
│ COs Aprobados:        +$13,500                             │
│ Total Actualizado:    $63,500                              │
│                                                            │
│ Facturado:            $15,000 (COs completados)            │
│ Por Facturar:         $500 (CO-IS-003 pendiente)           │
├────────────────────────────────────────────────────────────┤
│ 📅 IMPACTO EN CRONOGRAMA                                   │
├────────────────────────────────────────────────────────────┤
│ Timeline Original: 8 semanas                               │
│ Extensión por COs: +2 semanas                              │
│ Timeline Actualizado: 10 semanas                           │
│                                                            │
│ CO-IS-001 agregó: +10 días                                 │
│ CO-IS-003 agregará: +3 días (estimado)                     │
├────────────────────────────────────────────────────────────┤
│ 📋 ACCIONES RÁPIDAS                                        │
│ [+ Nuevo Change Order]                                     │
│ [Ver Todos los COs] [Exportar Reporte] [Notificar Cliente]│
└────────────────────────────────────────────────────────────┘
```

**Métricas Críticas:**
```
Por proyecto:
├─ Total de COs (cantidad)
├─ Valor total de COs ($)
├─ COs por estado (gráfico)
├─ Impacto en presupuesto total
├─ Impacto en timeline
├─ COs pendientes de facturar
└─ Ganancia/pérdida por COs

Por CO individual:
├─ Budget vs Real (si aplica)
├─ Progreso de trabajo
├─ Tiempo registrado
├─ Materiales usados
├─ Estado actual
├─ Fecha de completación estimada
└─ Facturado o pendiente
```

**Filtros y Vistas:**
```
Filtros disponibles:
├─ Por estado (Approved, In Progress, Completed)
├─ Por tipo (Budget fijo vs T&M)
├─ Por monto (positivos, negativos, neutros)
├─ Por fecha de creación
├─ Facturados vs No facturados
└─ Por quien solicitó (Cliente, PM, Admin)

Vistas especiales:
├─ COs que excedieron budget (⚠️)
├─ COs listos para facturar (💰)
├─ COs pendientes de aprobación (⏳)
└─ COs completados este mes (📊)
```

**Integración con Schedule:**
```
"Afecta el cronograma, se puede crear un item
que se inserta dentro del cronograma"

Cuando CO es aprobado:
1. Sistema pregunta: "¿Agregar al cronograma?"
2. PM acepta
3. Sistema muestra cronograma actual
4. PM selecciona dónde insertar:
   └─ Después de: "Pintura de paredes"
   └─ Antes de: "Pintura de trim"
5. CO se inserta en cronograma:
   ├─ Nombre: CO-IS-003 (Ventiladores)
   ├─ Duración: 3 días
   ├─ Recursos: Juan, María
   └─ Dependencias: Después de pintura de paredes
6. Timeline se ajusta automáticamente
7. Equipo ve nuevo item en daily plan
```

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 8**

### Mejoras CRÍTICAS:
1. 🔴 **Portal del Cliente para Solicitar COs**
   - Cliente puede submit CO requests
   - Upload de fotos/documentos
   - Tracking de solicitudes
   - Notificaciones a Admin

2. 🔴 **Sistema de Firma Digital para COs**
   - Cliente firma COs antes de empezar
   - Legal y documentado
   - Timestamped
   - PDF con firma embebida

### Mejoras Importantes:
3. ⚠️ Dashboard completo de COs por proyecto
4. ⚠️ Tracking de Budget vs Real por CO
5. ⚠️ Integración con cronograma (insertar items)
6. ⚠️ Generación automática de número (CO-IS-001)
7. ✅ Switch flexible de empleados a COs
8. ✅ Asignación de gastos a COs
9. ✅ Tracking de Time & Material
10. ✅ Métricas de impacto financiero
11. ⚠️ Alertas cuando CO excede budget
12. ⚠️ Lista de COs listos para facturar

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)

**Total documentado: 83/250+ funciones (33%)**

**Pendientes:**
- ⏳ Módulos 10-27: 150+ funciones

---

## ✅ **MÓDULO 9: PRESUPUESTO Y EARNED VALUE MANAGEMENT** (14/14 COMPLETO) ⭐ CRÍTICO

### 📌 FUNCIÓN 9.1 - Cost Codes (Códigos de Costo)

**Propósito:**
```
Sistema de categorización universal para organizar y rastrear
todos los costos del proyecto (labor, materiales, equipos).

Ejemplos:
├─ LAB001 - Instalación de drywall
├─ LAB002 - Pintura de paredes
├─ MAT001 - Materiales eléctricos
├─ MAT002 - Pintura y supplies
└─ EQP001 - Renta de equipo
```

**Estructura del Modelo:**
```python
class CostCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=50, blank=True)  # labor, material, equipment
    active = models.BooleanField(default=True)
```

**Uso en el Sistema:**
```
Cost Codes se usan en:
├─ BudgetLines (presupuesto del proyecto)
├─ EstimateLines (líneas de estimados)
├─ Expenses (categorizar gastos)
├─ TimeEntry (opcional: categorizar horas trabajadas)
├─ InvoiceLines (líneas de factura)
└─ ChangeOrders (líneas de órdenes de cambio)
```

**Mejoras Identificadas:**
- ✅ Sistema universal de codes activo
- ⚠️ Falta: Jerarquía de cost codes (códigos padre/hijo)
- ⚠️ Falta: Templates de cost codes por tipo de proyecto
- ⚠️ Falta: Análisis histórico por cost code

---

### 📌 FUNCIÓN 9.2 - Crear Budget Lines (Líneas de Presupuesto)

**Flujo de Creación:**
```
1. Admin/PM accede al proyecto
2. Va a pestaña "Budget"
3. Agrega líneas con cost codes
4. Define cantidades y costos unitarios
5. Sistema calcula baseline automáticamente
```

**Campos de BudgetLine:**
```python
BudgetLine:
├─ project (FK)
├─ cost_code (FK)
├─ description (texto adicional)
├─ qty (cantidad)
├─ unit (unidad: sq ft, lf, ea, hrs)
├─ unit_cost (costo por unidad)
├─ allowance (Boolean: es un allowance?)
├─ baseline_amount (auto-calculado: qty × unit_cost)
├─ revised_amount (puede ser modificado después)
├─ planned_start (fecha inicio planeada)
├─ planned_finish (fecha fin planeada)
└─ weight_override (peso opcional para EV)
```

**Cálculo Automático:**
```
baseline_amount = qty × unit_cost

Ejemplo:
qty = 1000 sq ft
unit_cost = $2.50
baseline_amount = $2,500
```

**Validaciones:**
```python
def clean(self):
    # planned_finish >= planned_start
    if self.planned_start and self.planned_finish:
        if self.planned_finish < self.planned_start:
            raise ValidationError("Planned finish must be on/after planned start.")
    
    # weight_override entre 0 y 1
    if self.weight_override is not None:
        if self.weight_override < 0 or self.weight_override > 1:
            raise ValidationError("Weight override must be between 0 and 1.")
```

**Vista en Dashboard:**
```
Proyecto: Villa Moderna
Budget Lines:

┌─────────────────────────────────────────────────────────────┐
│ Cost Code │ Description    │ Qty      │ Unit │ Unit $│ Total│
├───────────┼────────────────┼──────────┼──────┼───────┼──────┤
│ LAB001    │ Drywall install│ 2,500 sf │ sf   │ $1.50 │$3,750│
│ LAB002    │ Painting       │ 2,500 sf │ sf   │ $2.00 │$5,000│
│ MAT001    │ Paint materials│ 50 gal   │ gal  │ $35   │$1,750│
│ MAT002    │ Drywall sheets │ 40 ea    │ ea   │ $12   │  $480│
│ EQP001    │ Equipment rent │ 10 days  │ day  │ $100  │$1,000│
├───────────┴────────────────┴──────────┴──────┴───────┼──────┤
│ BASELINE TOTAL:                                      │$11,980│
└──────────────────────────────────────────────────────┴──────┘

[+ Add Budget Line] [Import from Estimate] [Export CSV]
```

**Mejoras Identificadas:**
- ✅ Cálculo automático de baseline
- ✅ Validaciones de fechas y weights
- ⚠️ Falta: Importar budget lines desde estimate aprobado (auto-fill)
- ⚠️ Falta: Templates de budget por tipo de proyecto

---

### 📌 FUNCIÓN 9.3 - Planificar Budget Lines (Schedule)

**Propósito:**
```
Asignar fechas de inicio/fin planeadas a cada línea de presupuesto
para poder calcular Planned Value (PV) con el método de Earned Value.
```

**Vista: budget_line_plan_view**
```python
@login_required
def budget_line_plan_view(request, line_id):
    line = get_object_or_404(BudgetLine, pk=line_id)
    form = BudgetLineScheduleForm(request.POST or None, instance=line)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('budget_lines', project_id=line.project_id)
    return render(request, 'core/budget_line_plan.html', {'line': line, 'form': form})
```

**Formulario:**
```
Planificación de Línea de Presupuesto
─────────────────────────────────────

Cost Code: LAB001 - Drywall Installation
Budget: $3,750

Planned Start:  [2025-08-01] 📅
Planned Finish: [2025-08-15] 📅

Weight Override (opcional):
└─ Dejar vacío para calcular automáticamente
└─ O especificar peso (0.0 - 1.0)

[Save] [Cancel]
```

**Cálculo de Planned Value (PV):**
```python
def line_planned_percent(line, as_of: date) -> Decimal:
    """
    Calcula % planeado de una línea según fechas.
    Método: Progreso lineal entre planned_start y planned_finish
    """
    if not line.planned_start or not line.planned_finish:
        return Decimal('1')  # 100% si no hay fechas
    
    if as_of <= line.planned_start:
        return Decimal('0')  # No ha comenzado
    
    if as_of >= line.planned_finish:
        return Decimal('1')  # Ya terminó según plan
    
    # Entre start y finish: progreso lineal
    total_days = (line.planned_finish - line.planned_start).days
    if total_days <= 0:
        return Decimal('1')
    
    done_days = (as_of - line.planned_start).days
    return Decimal(done_days) / Decimal(total_days)

# Ejemplo:
# planned_start: Aug 1
# planned_finish: Aug 15 (14 días)
# as_of: Aug 8 (7 días transcurridos)
# progress = 7/14 = 50%
# PV = baseline_amount × 50% = $3,750 × 0.5 = $1,875
```

**Mejoras Identificadas:**
- ✅ Planificación de fechas por línea
- ✅ Cálculo lineal de PV
- ⚠️ Falta: Visualización gráfica de timeline de budget lines
- ⚠️ Falta: Integración directa con Schedule items

---

### 📌 FUNCIÓN 9.4 - Registrar Progress (Avance de Trabajo)

**Modelo BudgetProgress:**
```python
class BudgetProgress(models.Model):
    budget_line = models.ForeignKey(BudgetLine, on_delete=models.CASCADE, 
                                    related_name='progress_points')
    date = models.DateField()
    qty_completed = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percent_complete = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0–100
    note = models.CharField(max_length=200, blank=True)
```

**Cálculo Automático de Percent Complete:**
```python
def save(self, *args, **kwargs):
    # Si no se especifica percent, calcula desde qty
    total_qty = getattr(self.budget_line, 'qty', None)
    if (not self.percent_complete or self.percent_complete == 0) and total_qty:
        if total_qty != 0:
            self.percent_complete = min(100, (self.qty_completed / total_qty) * 100)
    
    self.full_clean()
    super().save(*args, **kwargs)

# Ejemplo:
# BudgetLine: 2,500 sq ft de drywall
# BudgetProgress: qty_completed = 1,250 sq ft
# Auto-calcula: percent_complete = 50%
```

**Formulario de Registro:**
```
Registrar Progreso
──────────────────

Proyecto: Villa Moderna
Fecha: [2025-08-08] 📅

Budget Line: [LAB001 - Drywall Installation ▼]

Cantidad Completada: [1,250] sq ft
Percent Complete: [50] % (auto-calculado si se deja vacío)

Notas: [Primera mitad de la sala completada]

[Save Progress] [Cancel]
```

**Validaciones:**
```python
def clean(self):
    super().clean()
    # percent_complete entre 0 y 100
    if self.percent_complete is not None:
        if self.percent_complete < 0 or self.percent_complete > 100:
            raise ValidationError("Percent complete must be between 0 and 100.")
    
    # qty_completed no puede ser negativa
    if self.qty_completed is not None and self.qty_completed < 0:
        raise ValidationError("Qty completed cannot be negative.")
```

**Historial de Progress:**
```
LAB001 - Drywall Installation
Total Budget: 2,500 sq ft | $3,750

┌────────────────────────────────────────────────────────┐
│ Fecha      │ Qty Done │ % Complete │ Note              │
├────────────┼──────────┼────────────┼───────────────────┤
│ 2025-08-08 │ 1,250 sf │ 50%        │ Primera mitad     │
│ 2025-08-06 │ 800 sf   │ 32%        │ Sala principal    │
│ 2025-08-04 │ 500 sf   │ 20%        │ Inicio            │
└────────────┴──────────┴────────────┴───────────────────┘

Progreso actual (último punto): 50% completado
EV = $3,750 × 50% = $1,875
```

**Permisos:**
```
Crear/editar progress:
├─ Admin/Staff: ✅ Siempre
├─ Project Manager: ✅ Siempre
└─ Employee/Client: ❌ Solo lectura
```

**Mejoras Identificadas:**
- ✅ Cálculo automático de percent desde qty
- ✅ Validaciones robustas
- ⚠️ Falta: Foto upload para documentar avance
- ⚠️ Falta: Notificación automática cuando alcanza milestones (25%, 50%, 75%, 100%)

---

### 📌 FUNCIÓN 9.5 - Importar Progress por CSV

**Propósito:**
```
Permitir carga masiva de puntos de progreso desde archivo CSV.
Útil para importar datos históricos o actualizaciones semanales.
```

**Vista: upload_project_progress**
```python
@login_required
@staff_required
def upload_project_progress(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if not _is_staffish(request.user):
        messages.error(request, "No tienes permisos para importar progreso.")
        return redirect('project_ev', project_id=project.id)
    
    # Procesa archivo CSV
    # Detecta delimitador automáticamente (,  ;  o tab)
    # Crea/actualiza BudgetProgress records
```

**Formato del CSV:**
```csv
cost_code,date,percent_complete,qty_completed,note
LAB001,2025-08-08,50,1250,Primera mitad completada
LAB002,2025-08-08,25,625,Pintura en progreso
MAT001,2025-08-07,100,50,Todo el material recibido
```

**Columnas Requeridas:**
```
Obligatorias:
├─ cost_code (debe existir en el sistema)
└─ date (formato: YYYY-MM-DD, MM/DD/YYYY, o DD/MM/YYYY)

Opcionales:
├─ percent_complete (0-100)
├─ qty_completed (decimal)
└─ note (texto)
```

**Lógica de Importación:**
```python
# 1. Busca el cost_code
cost_code = CostCode.objects.get(code=cc)

# 2. Busca la BudgetLine del proyecto
bl = BudgetLine.objects.filter(project=project, cost_code=cost_code).first()

# 3. Si no existe y create_missing=True, la crea automáticamente
if not bl and create_missing:
    bl = BudgetLine.objects.create(
        project=project, 
        cost_code=cost_code,
        description=f"Auto {cc}", 
        qty=0, 
        unit="", 
        unit_cost=0
    )

# 4. Calcula percent_complete desde qty si no viene
if pct_val is None and bl.qty:
    pct_val = min(100, (qty_val / bl.qty) * 100)

# 5. Crea o actualiza el BudgetProgress
obj, created = BudgetProgress.objects.get_or_create(
    budget_line=bl, 
    date=date,
    defaults={'qty_completed': qty_val, 'percent_complete': pct_val, 'note': note}
)

if not created:
    # Ya existe: actualiza valores
    obj.qty_completed = qty_val
    obj.percent_complete = pct_val
    obj.note = note
    obj.save()
```

**Resultados:**
```
Resultado de Importación
─────────────────────────

✅ Creados: 5 puntos de progreso
✅ Actualizados: 2 puntos existentes
⚠️ Omitidos: 1 por errores

Errores:
- Fila 8: CostCode no existe: XYZ999
```

**Mejoras Identificadas:**
- ✅ Auto-detección de delimitador
- ✅ Creación automática de BudgetLines faltantes
- ✅ Manejo de duplicados (actualiza en lugar de error)
- ⚠️ Falta: Preview antes de importar
- ⚠️ Falta: Validación de fechas futuras

---

### 📌 FUNCIÓN 9.6 - Exportar Progress a CSV

**Vista: project_progress_csv**
```python
@login_required
@staff_required
def project_progress_csv(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    
    # Filtros opcionales
    start = request.GET.get('start')  # YYYY-MM-DD
    end = request.GET.get('end')      # YYYY-MM-DD
    
    # Query
    qs = BudgetProgress.objects.filter(budget_line__project=project)
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)
    
    # Export to CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="progress_{project.id}_{end}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['project_id','date','cost_code','description',
                     'percent_complete','qty_completed','note'])
    
    for p in qs:
        writer.writerow([
            project.id,
            p.date,
            p.budget_line.cost_code.code,
            p.budget_line.description,
            float(p.percent_complete),
            float(p.qty_completed),
            p.note
        ])
    
    return response
```

**Uso:**
```
GET /projects/42/progress/csv/?start=2025-08-01&end=2025-08-31

Descarga: progress_42_2025-08-31.csv
```

**Mejoras Identificadas:**
- ✅ Exportación funcional
- ⚠️ Falta: Opciones de filtrado por cost_code
- ⚠️ Falta: Formato Excel (xlsx) además de CSV

---

### 📌 FUNCIÓN 9.7 - Calcular Earned Value (EV)

**Servicio: compute_project_ev**
```python
from core.services.earned_value import compute_project_ev

def compute_project_ev(project, as_of=None):
    """
    Calcula métricas de Earned Value Management para un proyecto.
    
    Returns:
        {
            'date': as_of,
            'baseline_total': Decimal,
            'PV': Planned Value,
            'EV': Earned Value,
            'AC': Actual Cost,
            'SPI': Schedule Performance Index (EV/PV),
            'CPI': Cost Performance Index (EV/AC),
            'percent_complete_cost': EV/baseline × 100
        }
    """
    if as_of is None:
        as_of = timezone.now().date()
    
    baseline_total = Decimal('0')
    PV = Decimal('0')
    EV = Decimal('0')
    AC = Decimal('0')
    
    # 1. BASELINE TOTAL
    lines = list(project.budget_lines.all())
    for bl in lines:
        baseline_total += bl.baseline_amount or 0
    
    # 2. PLANNED VALUE (PV)
    # Método: Progreso lineal por fechas planeadas
    for bl in lines:
        planned_pct = line_planned_percent(bl, as_of)
        PV += (bl.baseline_amount or 0) * planned_pct
    
    # 3. EARNED VALUE (EV)
    # Método: Último punto de progreso reportado
    for bl in lines:
        prog = bl.progress_points.filter(date__lte=as_of).order_by('-date').first()
        if prog:
            EV += (bl.baseline_amount or 0) * (Decimal(prog.percent_complete) / Decimal('100'))
    
    # 4. ACTUAL COST (AC)
    # 4a. Expenses
    exp_qs = Expense.objects.filter(project=project, date__lte=as_of)
    for e in exp_qs:
        AC += Decimal(e.amount or 0)
    
    # 4b. PayrollEntry (si existe)
    try:
        from core.models import PayrollEntry
        pe_qs = PayrollEntry.objects.filter(payroll__project=project, payroll__week_end__lte=as_of)
        for pe in pe_qs:
            hrs = Decimal(pe.hours_worked or 0)
            rate = Decimal(pe.hourly_rate or 0)
            AC += hrs * rate
    except Exception:
        pass
    
    # 4c. TimeEntry (solo si tiene rate, para evitar duplicación)
    try:
        te_qs = TimeEntry.objects.filter(project=project, date__lte=as_of)
        for t in te_qs:
            hrs = Decimal(getattr(t, 'hours_worked', 0) or 0)
            rate = Decimal(getattr(t, 'hourly_rate', 0) or 0)
            if rate:
                AC += hrs * rate
    except Exception:
        pass
    
    # 5. ÍNDICES DE RENDIMIENTO
    SPI = (EV / PV) if PV else None  # Schedule Performance Index
    CPI = (EV / AC) if AC else None  # Cost Performance Index
    
    return {
        'date': as_of,
        'baseline_total': baseline_total,
        'PV': PV,
        'EV': EV,
        'AC': AC,
        'SPI': SPI,
        'CPI': CPI,
        'percent_complete_cost': (EV / baseline_total * 100) if baseline_total else None
    }
```

**Interpretación de Métricas:**
```
EARNED VALUE METRICS

Baseline Total: $50,000
(Total presupuesto original del proyecto)

PV (Planned Value): $30,000
└─ "Debíamos haber completado $30k de trabajo al día de hoy"
└─ Basado en fechas planeadas de cada budget line

EV (Earned Value): $25,000
└─ "Hemos completado $25k de trabajo real"
└─ Basado en progress reportado (% complete)

AC (Actual Cost): $28,000
└─ "Hemos gastado $28k hasta ahora"
└─ Basado en expenses + payroll + time entries

ÍNDICES:

SPI = EV / PV = 25,000 / 30,000 = 0.83
├─ SPI < 1.0 = Detrás del cronograma ⚠️
├─ SPI = 1.0 = En cronograma ✅
└─ SPI > 1.0 = Adelantado al cronograma 🎉

CPI = EV / AC = 25,000 / 28,000 = 0.89
├─ CPI < 1.0 = Sobre presupuesto ⚠️ ($1.12 gastado por cada $1 de valor)
├─ CPI = 1.0 = En presupuesto ✅
└─ CPI > 1.0 = Bajo presupuesto 🎉

VARIANZAS:

Cost Variance (CV) = EV - AC = 25,000 - 28,000 = -$3,000
└─ Negativo = Sobre presupuesto por $3,000 ⚠️

Schedule Variance (SV) = EV - PV = 25,000 - 30,000 = -$5,000
└─ Negativo = Detrás del cronograma por $5,000 de valor ⚠️

Percent Complete: EV / Baseline = 25,000 / 50,000 = 50%
└─ Proyecto está 50% completo basado en costo
```

**Mejoras Identificadas:**
- ✅ Cálculo completo de métricas EVM estándar
- ✅ Integración con múltiples fuentes de AC (expenses, payroll, time)
- ⚠️ Falta: Forecast (EAC, ETC, VAC)
- ⚠️ Falta: Alertas cuando SPI o CPI caen bajo umbrales

---

### 📌 FUNCIÓN 9.8 - Dashboard de Earned Value

**Vista: project_ev_view**
```
Vista principal del dashboard de Earned Value por proyecto.
```

**Pantalla Principal:**
```
┌────────────────────────────────────────────────────────────┐
│ 📊 EARNED VALUE MANAGEMENT                                 │
│ Proyecto: Villa Moderna                                    │
│ Fecha: 2025-08-24                         [Cambiar Fecha ▼]│
├────────────────────────────────────────────────────────────┤
│ 💰 MÉTRICAS FINANCIERAS                                    │
├────────────────────────────────────────────────────────────┤
│ Baseline Total:    $50,000                                 │
│                                                            │
│ PV (Planned):      $30,000  ████████████░░░░░░░░  60%     │
│ EV (Earned):       $25,000  ██████████░░░░░░░░░░  50%     │
│ AC (Actual):       $28,000  ██████████████░░░░░░  56%     │
├────────────────────────────────────────────────────────────┤
│ 📈 ÍNDICES DE RENDIMIENTO                                  │
├────────────────────────────────────────────────────────────┤
│ SPI (Schedule):    0.83  ⚠️ DETRÁS DEL CRONOGRAMA         │
│                         (17% detrás)                       │
│                                                            │
│ CPI (Cost):        0.89  ⚠️ SOBRE PRESUPUESTO             │
│                         (Gastando $1.12 por cada $1 ganado)│
├────────────────────────────────────────────────────────────┤
│ 📊 VARIANZAS                                               │
├────────────────────────────────────────────────────────────┤
│ Cost Variance:     -$3,000  ⚠️ Sobre presupuesto          │
│ Schedule Variance: -$5,000  ⚠️ Detrás del plan            │
├────────────────────────────────────────────────────────────┤
│ 📅 PROGRESO POR LÍNEA DE PRESUPUESTO                       │
├────────────────────────────────────────────────────────────┤
│ Cost Code │ Description    │ Baseline │ Planned│ Earned   │
├───────────┼────────────────┼──────────┼────────┼──────────┤
│ LAB001    │ Drywall        │ $3,750   │ $2,250 │ $1,875   │
│           │                │          │  60%   │  50% ⚠️  │
│ LAB002    │ Painting       │ $5,000   │ $3,000 │ $2,500   │
│           │                │          │  60%   │  50% ⚠️  │
│ MAT001    │ Paint mat.     │ $1,750   │ $1,750 │ $1,750   │
│           │                │          │ 100%   │ 100% ✅  │
└───────────┴────────────────┴──────────┴────────┴──────────┘

[+ Add Progress] [Import CSV] [Export Report] [View Trend →]
```

**Formulario de Progress Inline:**
```
┌────────────────────────────────────────────────────────────┐
│ ➕ REGISTRAR NUEVO PROGRESO                                │
├────────────────────────────────────────────────────────────┤
│ Fecha: [2025-08-24] 📅                                     │
│ Budget Line: [LAB001 - Drywall ▼]                          │
│ Qty Completed: [1500] sq ft                                │
│ Percent: [60] %                                            │
│ Nota: [Cocina y baño completados]                          │
│                                                            │
│ [Save Progress] [Cancel]                                   │
└────────────────────────────────────────────────────────────┘
```

**Permisos:**
```python
can_edit_progress = _is_staffish(request.user)

# Roles que pueden agregar progress:
├─ Admin/Superuser: ✅
├─ Project Manager: ✅
└─ Employee/Client: ❌ Solo lectura
```

**Paginación:**
```
Muestra 20 puntos de progreso por página por defecto.
Parámetros URL:
├─ ?page=2 (siguiente página)
├─ ?ps=50 (cambiar page size)
└─ ?as_of=2025-08-15 (cambiar fecha de análisis)
```

**Mejoras Identificadas:**
- ✅ Dashboard completo con métricas EVM
- ✅ Visualización clara de SPI/CPI
- ✅ Formulario inline para agregar progress
- ⚠️ Falta: Gráfica visual de PV/EV/AC (líneas de tendencia)
- ⚠️ Falta: Comparación con proyectos similares

---

### 📌 FUNCIÓN 9.9 - Trend Analysis (Serie de Tiempo)

**Vista: project_ev_series**
```python
@login_required
def project_ev_series(request, project_id):
    """
    Genera serie de tiempo de PV/EV/AC para gráficas.
    
    Parámetros:
    - days: número de días hacia atrás (default: 30)
    - end: fecha final (default: hoy)
    
    Returns: JSON con arrays de datos para Chart.js
    """
    project = get_object_or_404(Project, pk=project_id)
    days = int(request.GET.get('days', 30))
    end = timezone.now().date()
    start = end - timedelta(days=days - 1)
    
    labels, pv, ev, ac = [], [], [], []
    cur = start
    while cur <= end:
        s = compute_project_ev(project, as_of=cur)
        labels.append(cur.isoformat())
        pv.append(float(s.get('PV') or 0))
        ev.append(float(s.get('EV') or 0))
        ac.append(float(s.get('AC') or 0))
        cur += timedelta(days=1)
    
    return JsonResponse({
        'labels': labels,
        'PV': pv,
        'EV': ev,
        'AC': ac
    })
```

**Uso:**
```javascript
// En el frontend
fetch('/projects/42/ev/series/?days=30')
  .then(res => res.json())
  .then(data => {
    // data.labels = ['2025-07-25', '2025-07-26', ...]
    // data.PV = [5000, 5500, 6000, ...]
    // data.EV = [4500, 5000, 5400, ...]
    // data.AC = [4800, 5300, 5900, ...]
    
    // Render con Chart.js
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.labels,
        datasets: [
          {label: 'Planned Value (PV)', data: data.PV, borderColor: 'blue'},
          {label: 'Earned Value (EV)', data: data.EV, borderColor: 'green'},
          {label: 'Actual Cost (AC)', data: data.AC, borderColor: 'red'}
        ]
      }
    });
  });
```

**Gráfica Visual:**
```
Earned Value Trend (Last 30 Days)

$60k ┤                                              
     │                                          ╱── Planned (PV)
$50k ┤                                      ╱───
     │                                  ╱───    
$40k ┤                              ╱───        ╱─ Earned (EV)
     │                          ╱───        ╱───
$30k ┤                      ╱───        ╱───    
     │                  ╱───        ╱───        ╱─ Actual (AC)
$20k ┤              ╱───        ╱───        ╱───
     │          ╱───        ╱───        ╱───
$10k ┤      ╱───        ╱───        ╱───
     │  ╱───        ╱───        ╱───
  $0 ┴───────────────────────────────────────────
     Jul 25    Aug 1     Aug 8    Aug 15   Aug 24

Análisis:
• PV (azul) crece linealmente según plan
• EV (verde) está por debajo = proyecto atrasado
• AC (rojo) está por encima de EV = sobre presupuesto
```

**Mejoras Identificadas:**
- ✅ Serie de tiempo funcional
- ✅ JSON response listo para gráficas
- ⚠️ Falta: Implementación del frontend con Chart.js
- ⚠️ Falta: Línea de forecast (proyección)

---

### 📌 FUNCIÓN 9.10 - Exportar EV a CSV

**Vista: project_ev_csv**
```python
@login_required
def project_ev_csv(request, project_id):
    """
    Exporta serie de tiempo de métricas EV a CSV.
    Útil para análisis en Excel o importar a otros sistemas.
    """
    project = get_object_or_404(Project, pk=project_id)
    days = int(request.GET.get('days', 45))
    end = timezone.now().date()
    start = end - timedelta(days=days - 1)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ev_{project.id}_{end.isoformat()}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'PV', 'EV', 'AC', 'SPI', 'CPI'])
    
    cur = start
    while cur <= end:
        s = compute_project_ev(project, as_of=cur)
        pv = s.get('PV') or 0
        ev = s.get('EV') or 0
        ac = s.get('AC') or 0
        spi = (ev / pv) if pv else ''
        cpi = (ev / ac) if ac else ''
        
        writer.writerow([
            cur.isoformat(),
            float(pv),
            float(ev),
            float(ac),
            float(spi) if spi else '',
            float(cpi) if cpi else ''
        ])
        cur += timedelta(days=1)
    
    return response
```

**Uso:**
```
GET /projects/42/ev/csv/?days=45

Descarga: ev_42_2025-08-24.csv
```

**Formato CSV:**
```csv
Date,PV,EV,AC,SPI,CPI
2025-07-10,1000.00,900.00,950.00,0.90,0.95
2025-07-11,1500.00,1300.00,1400.00,0.87,0.93
2025-07-12,2000.00,1700.00,1850.00,0.85,0.92
...
2025-08-24,30000.00,25000.00,28000.00,0.83,0.89
```

**Mejoras Identificadas:**
- ✅ Export funcional
- ⚠️ Falta: Formato Excel (xlsx)
- ⚠️ Falta: Incluir varianzas (CV, SV) en el export

---

### 📌 FUNCIÓN 9.11 - Editar/Eliminar Progress

**Editar Progress:**
```python
@login_required
@staff_required
def edit_progress(request, project_id, pk):
    prog = BudgetProgress.objects.get(pk=pk, budget_line__project_id=project_id)
    
    if request.method == "POST":
        form = BudgetProgressEditForm(request.POST, instance=prog)
        if form.is_valid():
            form.save()
            messages.success(request, "Progreso actualizado.")
            return redirect('project_ev', project_id=project_id)
    else:
        form = BudgetProgressEditForm(instance=prog)
    
    return render(request, 'core/progress_edit_form.html', {
        'form': form, 
        'project': prog.budget_line.project, 
        'prog': prog
    })
```

**Eliminar Progress:**
```python
@login_required
@staff_required
@require_POST
def delete_progress(request, project_id, pk):
    if not _is_staffish(request.user):
        messages.error(request, "No tienes permisos para borrar progreso.")
        return redirect('project_ev', project_id=project_id)
    
    prog = get_object_or_404(BudgetProgress, pk=pk, budget_line__project_id=project_id)
    prog.delete()
    messages.success(request, "Progreso eliminado.")
    return redirect('project_ev', project_id=project_id)
```

**Permisos:**
```
Editar/Eliminar Progress:
├─ Admin/Superuser: ✅
├─ Project Manager: ✅
└─ Employee/Client: ❌
```

**Vista de Edición:**
```
┌────────────────────────────────────────────────────────────┐
│ ✏️ EDITAR PROGRESO                                         │
├────────────────────────────────────────────────────────────┤
│ Proyecto: Villa Moderna                                    │
│ Budget Line: LAB001 - Drywall Installation                 │
│                                                            │
│ Fecha: [2025-08-08] 📅                                     │
│ Qty Completed: [1250] sq ft                                │
│ Percent: [50] %                                            │
│ Nota: [Primera mitad completada]                           │
│                                                            │
│ [Update] [Delete] [Cancel]                                 │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Edición funcional
- ✅ Eliminación con confirmación
- ⚠️ Falta: Audit log de cambios (quién editó/borró qué)

---

### 📌 FUNCIÓN 9.12 - Download Sample CSV

**Vista: download_progress_sample**
```python
@login_required
def download_progress_sample(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    
    resp = HttpResponse(content_type='text/csv')
    resp['Content-Disposition'] = f'attachment; filename="progress_sample_project_{project.id}.csv"'
    
    resp.write("project_id,cost_code,date,percent_complete,qty_completed,note\r\n")
    # Fila de ejemplo
    resp.write(f"{project.id},LAB001,2025-08-24,25,,Inicio\r\n")
    
    return resp
```

**Archivo Descargado:**
```csv
project_id,cost_code,date,percent_complete,qty_completed,note
42,LAB001,2025-08-24,25,,Inicio
```

**Uso:**
```
1. Usuario descarga sample CSV
2. Llena con datos reales en Excel
3. Sube el archivo completo usando "Import CSV"
```

**Mejoras Identificadas:**
- ✅ Template básico funcional
- ⚠️ Falta: Incluir todas las budget lines del proyecto en el sample
- ⚠️ Falta: Incluir múltiples filas de ejemplo

---

### 📌 FUNCIÓN 9.13 - Dashboard Admin (Métricas EV de Todos los Proyectos)

**Integración en Dashboard Principal:**
```python
@login_required
def dashboard_admin(request):
    today = timezone.now().date()
    projects = Project.objects.filter(status='active')
    
    summary_data = []
    for project in projects:
        metrics = compute_project_ev(project, as_of=today)
        
        # Calcula health indicators
        spi = metrics.get('SPI') or 1
        cpi = metrics.get('CPI') or 1
        
        # Status
        if spi >= 0.95 and cpi >= 0.95:
            health = 'healthy'  # 🟢
        elif spi >= 0.85 and cpi >= 0.85:
            health = 'warning'  # 🟡
        else:
            health = 'critical'  # 🔴
        
        summary_data.append({
            'project': project,
            'baseline': metrics.get('baseline_total'),
            'ev': metrics.get('EV'),
            'ac': metrics.get('AC'),
            'spi': spi,
            'cpi': cpi,
            'health': health,
            'percent_complete': metrics.get('percent_complete_cost')
        })
    
    context = {
        'summary_data': summary_data,
        # ... otras métricas del dashboard
    }
    return render(request, 'core/dashboard_admin.html', context)
```

**Vista en Dashboard:**
```
┌────────────────────────────────────────────────────────────┐
│ 📊 PROYECTOS ACTIVOS - EARNED VALUE SUMMARY                │
├────────────────────────────────────────────────────────────┤
│ Proyecto       │ Budget │ % Done│ SPI  │ CPI  │ Health    │
├────────────────┼────────┼───────┼──────┼──────┼───────────┤
│ Villa Moderna  │ $50k   │ 50%   │ 0.83 │ 0.89 │ 🟡 Warning│
│ Remodel Home   │ $85k   │ 75%   │ 1.05 │ 1.12 │ 🟢 Healthy│
│ Office Complex │ $200k  │ 30%   │ 0.72 │ 0.81 │ 🔴 Critical│
│ Touch-up Job   │ $5k    │ 90%   │ 0.95 │ 1.01 │ 🟢 Healthy│
└────────────────┴────────┴───────┴──────┴──────┴───────────┘

Health Indicators:
├─ 🟢 Healthy:  SPI ≥ 0.95 AND CPI ≥ 0.95
├─ 🟡 Warning:  SPI ≥ 0.85 AND CPI ≥ 0.85
└─ 🔴 Critical: SPI < 0.85 OR CPI < 0.85

[View Full Report] [Export All Projects]
```

**Mejoras Identificadas:**
- ✅ Integración en dashboard
- ✅ Health indicators visuales
- ⚠️ Falta: Gráfica de distribución de proyectos por health
- ⚠️ Falta: Alertas automáticas cuando proyecto pasa a Critical

---

### 📌 FUNCIÓN 9.14 - Budget Lines Management

**Vista: budget_lines_view**
```python
@login_required
def budget_lines_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = BudgetLineForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        bl = form.save(commit=False)
        bl.project = project
        bl.save()
        return redirect('budget_lines', project_id=project.id)
    
    lines = project.budget_lines.select_related('cost_code')
    
    return render(request, 'core/budget_lines.html', {
        'project': project,
        'lines': lines,
        'form': form
    })
```

**Vista Principal:**
```
┌────────────────────────────────────────────────────────────┐
│ 💰 BUDGET LINES - Villa Moderna                            │
├────────────────────────────────────────────────────────────┤
│ Cost Code │ Description   │ Qty    │ Unit │ Cost │ Total  │
├───────────┼───────────────┼────────┼──────┼──────┼────────┤
│ LAB001    │ Drywall       │ 2,500  │ sf   │ $1.50│ $3,750 │
│ LAB002    │ Painting      │ 2,500  │ sf   │ $2.00│ $5,000 │
│ MAT001    │ Paint mat.    │ 50     │ gal  │ $35  │ $1,750 │
│ MAT002    │ Drywall sheets│ 40     │ ea   │ $12  │   $480 │
│ EQP001    │ Equipment rent│ 10     │ day  │ $100 │ $1,000 │
├───────────┴───────────────┴────────┴──────┴──────┼────────┤
│ TOTAL BASELINE:                                  │ $11,980│
└──────────────────────────────────────────────────┴────────┘

┌────────────────────────────────────────────────────────────┐
│ ➕ ADD NEW BUDGET LINE                                     │
├────────────────────────────────────────────────────────────┤
│ Cost Code: [Select ▼]                                      │
│ Description: [Optional additional details]                 │
│ Qty: [0] Unit: [ea ▼] Unit Cost: [$0.00]                  │
│ Planned Start: [📅] Planned Finish: [📅]                   │
│                                                            │
│ [Add Line] [Import from Estimate]                          │
└────────────────────────────────────────────────────────────┘
```

**Acciones por Línea:**
```
Cada budget line tiene:
├─ [📝 Edit] - Editar qty, unit cost, fechas
├─ [📅 Plan] - Ir a vista de planificación de fechas
├─ [📊 Progress] - Ver historial de progreso
└─ [🗑️ Delete] - Eliminar línea (solo si no tiene progress)
```

**Mejoras Identificadas:**
- ✅ CRUD completo de budget lines
- ✅ Cálculo automático de baseline
- ⚠️ Falta: Botón "Import from Estimate" funcional
- ⚠️ Falta: Edición inline (sin ir a otra página)

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 9**

### Mejoras CRÍTICAS:
1. 🔴 **Implementación de Forecast (EAC, ETC, VAC)**
   - Estimate at Completion
   - Estimate to Complete
   - Variance at Completion
   - Proyecciones basadas en tendencias

2. 🔴 **Gráficas Visuales de PV/EV/AC**
   - Implementar Chart.js en frontend
   - Líneas de tendencia
   - Proyección futura

3. 🔴 **Alertas Automáticas**
   - Cuando SPI < 0.85 (detrás del cronograma)
   - Cuando CPI < 0.85 (sobre presupuesto)
   - Cuando proyecto pasa a estado Critical

### Mejoras Importantes:
4. ⚠️ Import Budget Lines desde Estimate aprobado
5. ⚠️ Templates de Budget Lines por tipo de proyecto
6. ⚠️ Jerarquía de Cost Codes (padre/hijo)
7. ⚠️ Análisis histórico de performance por Cost Code
8. ⚠️ Foto upload para documentar progress
9. ⚠️ Notificaciones automáticas en milestones (25%, 50%, 75%, 100%)
10. ⚠️ Export a Excel (xlsx) además de CSV
11. ⚠️ Audit log de ediciones de progress
12. ⚠️ Preview antes de importar CSV
13. ⚠️ Gráfica de distribución de proyectos por health status
14. ⚠️ Comparación con proyectos similares

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO

**Total documentado: 97/250+ funciones (39%)**

**Pendientes:**
- ⏳ Módulos 11-27: 140+ funciones

---

## ✅ **MÓDULO 10: CRONOGRAMA (SCHEDULE)** (12/12 COMPLETO)

### 📌 FUNCIÓN 10.1 - Crear Categorías de Cronograma (Fases)

**Propósito:**
```
Organizar el cronograma del proyecto en categorías/fases jerárquicas.
Las categorías agrupan items relacionados y permiten mejor visualización.

Ejemplos de Categorías:
├─ Site Preparation
├─ Foundation
├─ Framing
├─ Electrical
├─ Plumbing
├─ Drywall
├─ Painting
└─ Finishing
```

**Modelo ScheduleCategory:**
```python
class ScheduleCategory(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, 
                                related_name='schedule_categories')
    name = models.CharField(max_length=200)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, 
                              null=True, blank=True, related_name='children')
    order = models.IntegerField(default=0)
    is_phase = models.BooleanField(default=False, 
                                   help_text="Categoría representa una fase agregada")
    cost_code = models.ForeignKey('CostCode', on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='schedule_categories')
    
    class Meta:
        ordering = ['project', 'parent__id', 'order', 'name']
        unique_together = ('project', 'name', 'parent')
```

**Jerarquía de Categorías:**
```
Proyecto: Villa Moderna

📁 Site Preparation (Fase)
   ├─ 📂 Clearing & Demolition
   └─ 📂 Site Protection

📁 Interior Work (Fase)
   ├─ 📂 Drywall Installation
   ├─ 📂 Painting
   │  ├─ 📄 Walls Painting
   │  └─ 📄 Trim Painting
   └─ 📂 Finishing
```

**Vista de Creación:**
```
┌────────────────────────────────────────────────────────────┐
│ ➕ CREAR CATEGORÍA DE CRONOGRAMA                           │
├────────────────────────────────────────────────────────────┤
│ Nombre: [Site Preparation]                                 │
│ Categoría Padre: [None ▼] (para categoría raíz)           │
│ Cost Code: [Select ▼] (opcional)                           │
│ Es Fase: [✓] (marcar para fases agregadas)                │
│ Orden: [0] (menor número = aparece primero)                │
│                                                            │
│ [Crear Categoría] [Cancel]                                 │
└────────────────────────────────────────────────────────────┘
```

**Cálculo Automático de % Complete:**
```python
@property
def percent_complete(self):
    """
    Promedio simple de los items directos o, si no hay, de subcategorías.
    """
    # Si tiene items, promedia items
    items = self.items.all()
    if items.exists():
        vals = [i.percent_complete or 0 for i in items]
        return int(sum(vals) / len(vals)) if vals else 0
    
    # Si no tiene items, promedia subcategorías
    kids = self.children.all()
    if kids.exists():
        vals = [c.percent_complete for c in kids]
        return int(sum(vals) / len(vals)) if vals else 0
    
    return 0

# Ejemplo:
# Categoría "Painting" tiene 3 items:
#   - Walls: 100%
#   - Trim: 50%
#   - Touch-ups: 0%
# percent_complete = (100 + 50 + 0) / 3 = 50%
```

**Mejoras Identificadas:**
- ✅ Jerarquía padre/hijo funcional
- ✅ Cálculo automático de progreso
- ✅ Unique constraint (no duplicados)
- ⚠️ Falta: Drag & drop para reordenar categorías
- ⚠️ Falta: Templates de categorías por tipo de proyecto
- ⚠️ Falta: Color coding para categorías

---

### 📌 FUNCIÓN 10.2 - Crear Items de Cronograma

**Modelo ScheduleItem:**
```python
class ScheduleItem(models.Model):
    STATUS_CHOICES = [
        ('NOT_STARTED', 'No iniciado'),
        ('IN_PROGRESS', 'En progreso'),
        ('BLOCKED', 'Bloqueado'),
        ('DONE', 'Completado'),
    ]
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE, 
                                related_name='schedule_items')
    category = models.ForeignKey(ScheduleCategory, on_delete=models.CASCADE, 
                                 related_name='items')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    # Fechas y estado
    planned_start = models.DateField(null=True, blank=True)
    planned_end = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_STARTED')
    percent_complete = models.IntegerField(default=0)
    is_milestone = models.BooleanField(default=False, 
                                       help_text="Hito se muestra como diamante en Gantt")
    
    # Vínculos contables/estimación
    budget_line = models.ForeignKey('BudgetLine', on_delete=models.SET_NULL, 
                                    null=True, blank=True)
    estimate_line = models.ForeignKey('EstimateLine', on_delete=models.SET_NULL, 
                                      null=True, blank=True)
    cost_code = models.ForeignKey('CostCode', on_delete=models.SET_NULL, 
                                  null=True, blank=True)
```

**Formulario de Creación:**
```
┌────────────────────────────────────────────────────────────┐
│ ➕ CREAR ITEM DE CRONOGRAMA                                │
├────────────────────────────────────────────────────────────┤
│ Categoría: [Painting ▼]                                    │
│ O crear nueva: [_________________]                         │
│                                                            │
│ Título: [Paint walls - living room]                        │
│ Descripción:                                               │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Apply two coats of SW7006 Extra White                  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Planned Start: [2025-08-10] 📅                             │
│ Planned End:   [2025-08-12] 📅                             │
│                                                            │
│ Estado: [NOT_STARTED ▼]                                    │
│ % Complete: [0]                                            │
│ Es Milestone: [  ] (marcar para hitos importantes)         │
│                                                            │
│ Vínculos opcionales:                                       │
│ Cost Code: [Select ▼]                                      │
│ Budget Line: [Select ▼]                                    │
│ Estimate Line: [Select ▼]                                  │
│                                                            │
│ [Crear Item] [Cancel]                                      │
└────────────────────────────────────────────────────────────┘
```

**Ejemplo de Items:**
```
Categoría: Painting

┌────────────────────────────────────────────────────────────┐
│ 📋 Paint walls - living room                               │
│ Status: IN_PROGRESS (75%)                                  │
│ Aug 10 - Aug 12 (3 days)                                   │
│ Cost Code: LAB002                                          │
├────────────────────────────────────────────────────────────┤
│ 📋 Paint trim - all rooms                                  │
│ Status: NOT_STARTED (0%)                                   │
│ Aug 13 - Aug 15 (3 days)                                   │
│ Cost Code: LAB003                                          │
├────────────────────────────────────────────────────────────┤
│ 💎 Final walkthrough                                       │
│ Status: NOT_STARTED (0%)                                   │
│ Aug 16 (milestone)                                         │
│ 💎 = Milestone (hito importante)                           │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Vínculos a budget/estimate lines
- ✅ Support para milestones
- ✅ Estados claros (NOT_STARTED, IN_PROGRESS, BLOCKED, DONE)
- ⚠️ Falta: Asignación de empleados/recursos al item
- ⚠️ Falta: Alertas cuando item está BLOCKED
- ⚠️ Falta: Attachments (planos, specs) por item

---

### 📌 FUNCIÓN 10.3 - Establecer Fechas y Duración

**Cálculo de Duración:**
```python
# Automático al guardar
def save(self, *args, **kwargs):
    # Calcular duración en días
    if self.planned_start and self.planned_end:
        delta = (self.planned_end - self.planned_start).days + 1
        self.duration_days = delta
    super().save(*args, **kwargs)
```

**Vista de Fechas:**
```
Item: Paint walls - living room

Fechas Planeadas:
├─ Start: Aug 10, 2025
├─ End:   Aug 12, 2025
└─ Duration: 3 días (business days)

Fechas Reales (al completar):
├─ Actual Start: Aug 11, 2025 (1 día de retraso ⚠️)
├─ Actual End:   Aug 13, 2025
└─ Actual Duration: 3 días

Varianza:
├─ Schedule Variance: +1 día (comenzó tarde)
└─ Duration Variance: 0 días (tomó el tiempo planeado)
```

**Validaciones:**
```python
def clean(self):
    super().clean()
    # End date must be >= start date
    if self.planned_start and self.planned_end:
        if self.planned_end < self.planned_start:
            raise ValidationError("Planned end must be on or after planned start.")
```

**Mejoras Identificadas:**
- ✅ Validación de fechas
- ⚠️ Falta: Cálculo de business days (excluir weekends)
- ⚠️ Falta: Tracking de fechas reales (actual start/end)
- ⚠️ Falta: Alertas cuando se exceden fechas planeadas

---

### 📌 FUNCIÓN 10.4 - Asignar Responsable

**Campo Assigned To:**
```python
class ScheduleItem(models.Model):
    # ... otros campos
    assigned_to = models.ForeignKey('Employee', on_delete=models.SET_NULL, 
                                    null=True, blank=True, 
                                    related_name='schedule_items')
```

**Interfaz:**
```
┌────────────────────────────────────────────────────────────┐
│ 📋 Paint walls - living room                               │
├────────────────────────────────────────────────────────────┤
│ Responsable: [Juan Pérez ▼]                                │
│              [Cambiar] [Notificar]                          │
│                                                            │
│ Equipo asignado:                                           │
│ ├─ 👤 Juan Pérez (Lead)                                    │
│ ├─ 👤 María García                                         │
│ └─ 👤 Pedro López                                          │
│                                                            │
│ [+ Agregar miembro]                                        │
└────────────────────────────────────────────────────────────┘
```

**Notificaciones:**
```
Cuando se asigna un item:
1. Email/notificación al responsable
2. Item aparece en su "Morning Dashboard"
3. Recordatorio 1 día antes de planned_start
```

**Mejoras Identificadas:**
- ⚠️ Falta: Campo assigned_to en el modelo (actualmente no existe)
- ⚠️ Falta: Support para múltiples empleados por item
- ⚠️ Falta: Notificaciones automáticas de asignación

---

### 📌 FUNCIÓN 10.5 - Marcar Hitos (Milestones)

**Campo is_milestone:**
```python
is_milestone = models.BooleanField(default=False, 
                                   help_text="Hito se muestra como diamante en Gantt")
```

**Visualización en Gantt:**
```
Timeline (Gantt):

Aug 1   Aug 5   Aug 10  Aug 15  Aug 20  Aug 25  Aug 30
│───────│───────│───────│───────│───────│───────│───────│
├─────────────────────────────────────────────────────────┤
│ Site Prep       ████████                                 │
│ Foundation              ████████████                     │
│ Framing                         ████████████████         │
│ Inspection 1                            💎 (milestone)   │
│ Electrical                                  ████████     │
│ Plumbing                                    ████████     │
│ Inspection 2                                        💎   │
└─────────────────────────────────────────────────────────┘

💎 = Milestone (sin duración, fecha específica)
████ = Task con duración
```

**Ejemplos de Milestones:**
```
Milestones comunes:
├─ 💎 Project Kickoff
├─ 💎 Foundation Inspection
├─ 💎 Rough-in Inspection
├─ 💎 Final Inspection
├─ 💎 Client Walkthrough
└─ 💎 Project Completion
```

**Diferencia: Milestone vs Task:**
```
Regular Task:
├─ Tiene duración (start to end)
├─ Muestra barra en Gantt
├─ Puede tener % completado parcial
└─ Representa trabajo a realizar

Milestone:
├─ Fecha única (no duración)
├─ Muestra diamante en Gantt
├─ Solo 0% o 100%
└─ Representa punto de decisión/revisión
```

**Mejoras Identificadas:**
- ✅ Campo is_milestone funcional
- ⚠️ Falta: Auto-notificación cuando se alcanza milestone
- ⚠️ Falta: Milestone dependencies (bloquear siguiente fase hasta milestone)

---

### 📌 FUNCIÓN 10.6 - Actualizar Porcentaje de Progreso

**Método Manual:**
```
Admin/PM actualiza manualmente el % complete
```

**Método Automático (desde Tareas):**
```python
def recalculate_progress(self, save=True):
    """
    Calcula % según tareas vinculadas (excluye canceladas).
    """
    qs = self.tasks.exclude(status='Cancelada')
    total = qs.count()
    
    if total == 0:
        pct = 0
    else:
        done = qs.filter(status='Completada').count()
        pct = int((done / total) * 100)
    
    self.percent_complete = max(0, min(100, pct))
    
    # Auto-actualizar estado
    if self.percent_complete >= 100:
        self.status = 'DONE'
    elif qs.filter(status='En Progreso').exists():
        self.status = 'IN_PROGRESS'
    elif total > 0 and done == 0:
        self.status = 'NOT_STARTED'
    
    if save:
        self.save(update_fields=['percent_complete', 'status'])
    
    return self.percent_complete

# Ejemplo:
# ScheduleItem: "Paint walls"
# Tiene 5 tareas vinculadas:
#   - Prep walls: Completada
#   - First coat: Completada
#   - Second coat: En Progreso
#   - Touch-ups: Pendiente
#   - Cleanup: Pendiente
# 
# Completadas: 2 de 5 = 40%
# Estado: IN_PROGRESS (porque hay tareas en progreso)
```

**Vista de Progreso:**
```
┌────────────────────────────────────────────────────────────┐
│ 📋 Paint walls - living room                               │
├────────────────────────────────────────────────────────────┤
│ Progreso: 40% ████████░░░░░░░░░░                           │
│ Status: IN_PROGRESS                                        │
│                                                            │
│ Tareas (2 de 5 completadas):                               │
│ ✅ Prep walls                                              │
│ ✅ First coat                                              │
│ 🔄 Second coat (En Progreso)                               │
│ ⏸️ Touch-ups (Pendiente)                                   │
│ ⏸️ Cleanup (Pendiente)                                     │
│                                                            │
│ [Recalcular Progreso] [Marcar Completado]                  │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Recálculo automático desde tareas
- ✅ Auto-actualización de estado
- ⚠️ Falta: Progress history/log
- ⚠️ Falta: Peso ponderado de tareas (algunas más importantes)

---

### 📌 FUNCIÓN 10.7 - Establecer Dependencias entre Items

**Modelo de Dependencias:**
```python
class ScheduleDependency(models.Model):
    DEPENDENCY_TYPES = [
        ('FS', 'Finish-to-Start'),  # A termina, luego B empieza
        ('SS', 'Start-to-Start'),   # A y B empiezan juntos
        ('FF', 'Finish-to-Finish'), # A y B terminan juntos
        ('SF', 'Start-to-Finish'),  # A empieza, luego B termina
    ]
    
    predecessor = models.ForeignKey('ScheduleItem', on_delete=models.CASCADE, 
                                    related_name='successors')
    successor = models.ForeignKey('ScheduleItem', on_delete=models.CASCADE, 
                                  related_name='predecessors')
    dependency_type = models.CharField(max_length=2, choices=DEPENDENCY_TYPES, 
                                       default='FS')
    lag_days = models.IntegerField(default=0, 
                                   help_text="Días de espera (+ lag) o adelanto (- lag)")
```

**Ejemplo de Dependencias:**
```
Foundation → Framing (Finish-to-Start)
├─ Foundation debe terminar antes de empezar Framing
├─ Si Foundation termina Aug 10, Framing empieza Aug 11
└─ Lag: 0 días

Electrical + Plumbing (Start-to-Start)
├─ Ambos empiezan al mismo tiempo
├─ Si Electrical empieza Aug 15, Plumbing empieza Aug 15
└─ Lag: 0 días

Painting → Final Inspection (Finish-to-Start + 2 days lag)
├─ Painting termina, esperar 2 días, luego inspección
├─ Si Painting termina Aug 20, Inspection es Aug 22
└─ Lag: +2 días (para secado)
```

**Vista de Dependencias:**
```
┌────────────────────────────────────────────────────────────┐
│ 📋 Framing                                                 │
├────────────────────────────────────────────────────────────┤
│ DEPENDENCIAS:                                              │
│                                                            │
│ Predecesores (debe esperar a):                             │
│ ├─ Foundation (FS) - debe terminar primero                 │
│ └─ Site Prep (FS) - debe terminar primero                  │
│                                                            │
│ Sucesores (bloqueados por este):                           │
│ ├─ Electrical (FS) - esperando que termine Framing         │
│ ├─ Plumbing (FS) - esperando que termine Framing           │
│ └─ Drywall (FS) - esperando que termine Framing            │
│                                                            │
│ [+ Agregar Dependencia]                                    │
└────────────────────────────────────────────────────────────┘

ALERTAS:
⚠️ Foundation está retrasada - Framing no puede empezar
```

**Mejoras Identificadas:**
- ⚠️ Falta: Modelo ScheduleDependency (actualmente no existe)
- ⚠️ Falta: Cálculo automático de critical path
- ⚠️ Falta: Validación de dependencias circulares
- ⚠️ Falta: Auto-ajuste de fechas cuando cambian predecesores

---

### 📌 FUNCIÓN 10.8 - Visualizar Gantt Chart

**Vista React del Gantt:**
```python
@login_required
def schedule_gantt_react_view(request, project_id):
    """
    Render the React-based Gantt chart for project schedule.
    """
    project = get_object_or_404(Project, pk=project_id)
    
    # Serialize schedule data for React
    categories = ScheduleCategory.objects.filter(project=project).prefetch_related('items')
    
    schedule_data = []
    for cat in categories:
        cat_data = {
            'id': f'cat-{cat.id}',
            'name': cat.name,
            'type': 'category',
            'percent_complete': cat.percent_complete,
            'items': []
        }
        
        for item in cat.items.all():
            item_data = {
                'id': f'item-{item.id}',
                'title': item.title,
                'start': item.planned_start.isoformat() if item.planned_start else None,
                'end': item.planned_end.isoformat() if item.planned_end else None,
                'percent_complete': item.percent_complete,
                'status': item.status,
                'is_milestone': item.is_milestone,
            }
            cat_data['items'].append(item_data)
        
        schedule_data.append(cat_data)
    
    context = {
        'project': project,
        'schedule_data': json.dumps(schedule_data),
    }
    
    return render(request, 'schedule_gantt_react.html', context)
```

**Gantt Chart Visual:**
```
┌────────────────────────────────────────────────────────────────────────────┐
│ GANTT CHART - Villa Moderna                                                │
├────────────────────────────────────────────────────────────────────────────┤
│                    Aug 1    Aug 8    Aug 15   Aug 22   Aug 29   Sep 5     │
│                    ├────────├────────├────────├────────├────────├─────────│
│ Site Prep (100%)   ████████                                                │
│ ├─ Clear site      ██████                                                  │
│ └─ Protection      ████                                                    │
│                                                                            │
│ Foundation (75%)           ████████████                                    │
│ ├─ Excavation              ████                                            │
│ ├─ Forms                       ████                                        │
│ └─ Pour                            ████                                    │
│                                                                            │
│ Framing (30%)                          ████████████████                    │
│ ├─ Walls                                   ██████                          │
│ ├─ Roof                                          ██████                    │
│ └─ Inspection 1                                      💎                    │
│                                                                            │
│ Electrical (0%)                                        ████████            │
│ Plumbing (0%)                                          ████████            │
│                                                                            │
│ Final Insp. (0%)                                                   💎      │
└────────────────────────────────────────────────────────────────────────────┘

Leyenda:
████ = Completado
░░░░ = Pendiente
💎 = Milestone
```

**Funcionalidades del Gantt React:**
```
Interactivas:
├─ Drag & drop para mover fechas
├─ Zoom in/out del timeline
├─ Tooltip con detalles al hover
├─ Click para editar item
├─ Colores por estado (verde=done, azul=in progress, gris=not started)
└─ Critical path highlighting
```

**Mejoras Identificadas:**
- ✅ Vista React básica implementada
- ⚠️ Falta: Implementación completa de drag & drop
- ⚠️ Falta: Export a PDF/imagen
- ⚠️ Falta: Baseline comparison (plan vs actual)

---

### 📌 FUNCIÓN 10.9 - Generador Automático de Cronograma

**Vista: schedule_generator_view**
```python
@login_required
def schedule_generator_view(request, project_id):
    """
    Vista del generador de cronograma jerárquico.
    - Lista categorías e ítems existentes
    - Permite generar automáticamente desde estimado aprobado
    - CRUD inline para categorías e ítems
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Get approved estimate for generation
    approved_estimate = project.estimates.filter(approved=True).order_by('-version').first()
    
    # Handle POST actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Generate from estimate
        if action == 'generate_from_estimate' and approved_estimate:
            return _generate_schedule_from_estimate(request, project, approved_estimate)
    
    # ... render form
```

**Función de Generación:**
```python
def _generate_schedule_from_estimate(request, project, estimate):
    """
    Auto-genera categorías e ítems desde un estimado aprobado.
    Agrupa por cost_code.category y crea ScheduleItem por cada EstimateLine.
    """
    with transaction.atomic():
        created_cats = {}
        created_items = 0
        
        # Get all estimate lines grouped by cost code category
        lines = estimate.lines.select_related('cost_code').order_by(
            'cost_code__category', 'cost_code__code'
        )
        
        for line in lines:
            cc = line.cost_code
            cat_name = cc.category.capitalize() if cc.category else "General"
            
            # Get or create category
            if cat_name not in created_cats:
                cat, created = ScheduleCategory.objects.get_or_create(
                    project=project,
                    name=cat_name,
                    defaults={'cost_code': cc, 'order': len(created_cats)}
                )
                created_cats[cat_name] = cat
            else:
                cat = created_cats[cat_name]
            
            # Create schedule item from estimate line
            item_title = f"{cc.code} - {line.description or cc.name}"
            
            # Check if already exists
            existing = ScheduleItem.objects.filter(
                project=project,
                category=cat,
                title=item_title
            ).first()
            
            if not existing:
                ScheduleItem.objects.create(
                    project=project,
                    category=cat,
                    title=item_title,
                    description=line.description or "",
                    order=created_items,
                    estimate_line=line,
                    cost_code=cc,
                    status='NOT_STARTED',
                    percent_complete=0,
                )
                created_items += 1
        
        messages.success(
            request,
            f'Generado: {len(created_cats)} categorías y {created_items} ítems '
            f'desde el estimado {estimate.code}.'
        )
    
    return redirect('schedule_generator', project_id=project.id)
```

**Proceso de Generación:**
```
1. Admin aprueba Estimate
2. Va a Schedule Generator
3. Click "Generate from Estimate"
4. Sistema:
   ├─ Agrupa EstimateLines por cost_code.category
   ├─ Crea ScheduleCategory por cada categoría única
   ├─ Crea ScheduleItem por cada EstimateLine
   └─ Vincula items con estimate_line y cost_code

5. Resultado:
   ├─ Categoría "Labor" con 5 items
   ├─ Categoría "Material" con 3 items
   └─ Categoría "Equipment" con 2 items

6. PM puede luego:
   ├─ Asignar fechas a cada item
   ├─ Establecer dependencias
   ├─ Asignar responsables
   └─ Ajustar orden
```

**Vista del Generador:**
```
┌────────────────────────────────────────────────────────────┐
│ 🤖 GENERADOR DE CRONOGRAMA                                 │
├────────────────────────────────────────────────────────────┤
│ Proyecto: Villa Moderna                                    │
│                                                            │
│ ✅ Estimado Aprobado Encontrado:                           │
│ └─ KPVM1001 (v2) - $50,000                                 │
│    └─ 15 líneas de estimado                                │
│                                                            │
│ [🚀 Generar Cronograma desde Estimado]                     │
│                                                            │
│ ⚠️ Esto creará categorías e items automáticamente          │
│    basados en el estimado. Items existentes no se          │
│    duplicarán.                                             │
├────────────────────────────────────────────────────────────┤
│ CRONOGRAMA ACTUAL:                                         │
│                                                            │
│ 📁 Labor (3 items) - 33% complete                          │
│ 📁 Material (2 items) - 100% complete                      │
│ 📁 Equipment (1 item) - 0% complete                        │
│                                                            │
│ Total: 3 categorías, 6 items                               │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Generación automática desde estimate
- ✅ Prevención de duplicados
- ✅ Agrupación por categoría
- ⚠️ Falta: Estimación automática de fechas (basada en qty/labor)
- ⚠️ Falta: Auto-creación de dependencias lógicas
- ⚠️ Falta: Templates de cronograma por tipo de proyecto

---

### 📌 FUNCIÓN 10.10 - Schedule Público para Clientes

**Vista Pública:**
```python
def public_schedule_view(request, project_id, token):
    """
    Vista pública del cronograma para clientes.
    Requiere token de acceso para seguridad.
    """
    project = get_object_or_404(Project, pk=project_id)
    
    # Validar token
    if not project.validate_public_token(token):
        return HttpResponseForbidden("Invalid access token")
    
    categories = ScheduleCategory.objects.filter(
        project=project
    ).prefetch_related('items')
    
    context = {
        'project': project,
        'categories': categories,
        'is_public': True,
    }
    
    return render(request, 'core/schedule_public.html', context)
```

**URL Pública:**
```
https://kibray.com/schedule/public/42/abc123def456/

Proyecto: Villa Moderna
Cliente: John Smith

┌────────────────────────────────────────────────────────────┐
│ 📅 CRONOGRAMA DEL PROYECTO                                 │
├────────────────────────────────────────────────────────────┤
│ Site Preparation                        ✅ 100%            │
│ ├─ Clear and protect site               ✅                 │
│ └─ Setup utilities                      ✅                 │
│                                                            │
│ Foundation                              🔄 75%             │
│ ├─ Excavation                           ✅                 │
│ ├─ Forms and rebar                      ✅                 │
│ └─ Pour concrete                        🔄                 │
│                                                            │
│ Framing                                 ⏸️ 0%              │
│ ├─ Wall framing                         ⏸️                 │
│ └─ Roof framing                         ⏸️                 │
│                                                            │
│ Última actualización: Aug 24, 2025 3:45 PM                 │
└────────────────────────────────────────────────────────────┘

No muestra:
├─ ❌ Costos/presupuestos
├─ ❌ Detalles financieros
├─ ❌ Nombres de empleados
└─ ✅ Solo progreso y fechas estimadas
```

**Mejoras Identificadas:**
- ⚠️ Falta: Implementación de public token system
- ⚠️ Falta: Vista simplificada para clientes
- ⚠️ Falta: Notificaciones cuando se actualiza cronograma

---

### 📌 FUNCIÓN 10.11 - Exportar a Calendario

**Export a ICS (iCalendar):**
```python
@login_required
def project_schedule_ics(request, project_id):
    """
    Exporta el cronograma del proyecto a formato iCalendar (.ics)
    Compatible con Google Calendar, Outlook, Apple Calendar, etc.
    """
    project = get_object_or_404(Project, pk=project_id)
    items = ScheduleItem.objects.filter(project=project, 
                                        planned_start__isnull=False)
    
    # Crear archivo ICS
    cal = Calendar()
    cal.add('prodid', '-//Kibray Schedule//EN')
    cal.add('version', '2.0')
    
    for item in items:
        event = Event()
        event.add('summary', f'{project.name}: {item.title}')
        event.add('dtstart', item.planned_start)
        
        if item.is_milestone:
            # Milestone = evento de un día
            event.add('dtend', item.planned_start)
        else:
            event.add('dtend', item.planned_end or item.planned_start)
        
        event.add('description', item.description or '')
        event.add('status', item.status)
        
        cal.add_component(event)
    
    response = HttpResponse(cal.to_ical(), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="schedule_{project.id}.ics"'
    
    return response
```

**Google Calendar Integration:**
```python
@login_required
def project_schedule_google_calendar(request, project_id):
    """
    Genera link para agregar eventos a Google Calendar.
    """
    project = get_object_or_404(Project, pk=project_id)
    # ... genera URL de Google Calendar
    # https://calendar.google.com/calendar/render?action=TEMPLATE&...
```

**Uso:**
```
Cliente/PM puede:
1. Descargar archivo .ics
2. Importar a su calendario preferido
3. Recibir notificaciones de milestones
4. Sincronizar automáticamente con Google Calendar
```

**Mejoras Identificadas:**
- ⚠️ Falta: Implementación completa de ICS export
- ⚠️ Falta: Google Calendar integration
- ⚠️ Falta: Auto-sync cuando cambia cronograma

---

### 📌 FUNCIÓN 10.12 - CRUD de Categorías e Items

**Edit Category:**
```python
@login_required
def schedule_category_edit(request, category_id):
    category = get_object_or_404(ScheduleCategory, id=category_id)
    project = category.project
    
    if request.method == 'POST':
        form = ScheduleCategoryForm(request.POST, instance=category, project=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Categoría "{category.name}" actualizada.')
            return redirect('schedule_generator', project_id=project.id)
    else:
        form = ScheduleCategoryForm(instance=category, project=project)
    
    return render(request, 'core/schedule_category_form.html', {
        'form': form,
        'category': category,
        'project': project,
    })
```

**Delete Category:**
```python
@login_required
def schedule_category_delete(request, category_id):
    category = get_object_or_404(ScheduleCategory, id=category_id)
    project = category.project
    
    if request.method == 'POST':
        cat_name = category.name
        category.delete()
        messages.success(request, f'Categoría "{cat_name}" eliminada.')
        return redirect('schedule_generator', project_id=project.id)
    
    return render(request, 'core/schedule_category_confirm_delete.html', {
        'category': category,
        'project': project,
    })
```

**Edit Item:**
```python
@login_required
def schedule_item_edit(request, item_id):
    item = get_object_or_404(ScheduleItem, id=item_id)
    project = item.project
    
    if request.method == 'POST':
        form = ScheduleItemForm(request.POST, instance=item, project=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Ítem "{item.title}" actualizado.')
            return redirect('schedule_generator', project_id=project.id)
    else:
        form = ScheduleItemForm(instance=item, project=project)
    
    return render(request, 'core/schedule_item_form.html', {
        'form': form,
        'item': item,
        'project': project,
    })
```

**Delete Item:**
```python
@login_required
def schedule_item_delete(request, item_id):
    item = get_object_or_404(ScheduleItem, id=item_id)
    project = item.project
    
    if request.method == 'POST':
        item_title = item.title
        item.delete()
        messages.success(request, f'Ítem "{item_title}" eliminado.')
        return redirect('schedule_generator', project_id=project.id)
    
    return render(request, 'core/schedule_item_confirm_delete.html', {
        'item': item,
        'project': project,
    })
```

**Permisos:**
```
CRUD de Schedule:
├─ Admin/Superuser: ✅ Todos los permisos
├─ Project Manager: ✅ Todos los permisos en sus proyectos
├─ Employee: ❌ Solo lectura
└─ Client: ❌ Solo lectura (vista pública)
```

**Mejoras Identificadas:**
- ✅ CRUD completo implementado
- ✅ Permisos por rol
- ⚠️ Falta: Bulk edit/delete de items
- ⚠️ Falta: History/audit log de cambios

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 10**

### Mejoras CRÍTICAS:
1. 🔴 **Sistema de Dependencias entre Items**
   - Modelo ScheduleDependency
   - Tipos: FS, SS, FF, SF
   - Lag days
   - Critical path calculation
   - Validación de dependencias circulares

2. 🔴 **Asignación de Recursos/Empleados**
   - Campo assigned_to en ScheduleItem
   - Soporte para múltiples empleados por item
   - Notificaciones automáticas de asignación
   - Vista de carga de trabajo por empleado

3. 🔴 **Tracking de Fechas Reales**
   - actual_start y actual_end fields
   - Schedule variance calculation
   - Alertas cuando se exceden fechas planeadas
   - Baseline comparison (plan vs actual)

### Mejoras Importantes:
4. ⚠️ Drag & drop en Gantt para ajustar fechas
5. ⚠️ Export Gantt a PDF/imagen
6. ⚠️ Cálculo de business days (excluir weekends/holidays)
7. ⚠️ Templates de cronograma por tipo de proyecto
8. ⚠️ Auto-estimación de fechas desde estimate (basado en qty/labor)
9. ⚠️ Color coding para categorías
10. ⚠️ Progress history/log
11. ⚠️ Peso ponderado de tareas
12. ⚠️ Schedule público con token system
13. ⚠️ ICS export completo
14. ⚠️ Google Calendar integration
15. ⚠️ Auto-notificación de milestones
16. ⚠️ Milestone dependencies
17. ⚠️ Bulk edit/delete
18. ⚠️ History/audit log

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)

**Total documentado: 109/250+ funciones (44%)**

**Pendientes:**
- ⏳ Módulos 12-27: 130+ funciones

---

## ✅ **MÓDULO 11: TAREAS (TASKS)** (12/12 COMPLETO)

### 📌 FUNCIÓN 11.1 - Crear Nueva Tarea

**Modelo Task:**
```python
class Task(models.Model):
    """
    Tareas del proyecto, incluyendo touch-ups solicitados por clientes.
    El cliente puede crear tareas con fotos, el PM las asigna a empleados.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=50, 
        default="Pendiente",
        choices=[
            ('Pendiente', 'Pendiente'),
            ('En Progreso', 'En Progreso'),
            ('Completada', 'Completada'),
            ('Cancelada', 'Cancelada'),
        ]
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='created_tasks',
                                   help_text="Usuario que creó la tarea (cliente o staff)")
    assigned_to = models.ForeignKey('Employee', on_delete=models.SET_NULL, 
                                    null=True, blank=True,
                                    related_name='assigned_tasks',
                                    help_text="Empleado asignado por el PM")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_touchup = models.BooleanField(default=False, 
                                     help_text="Marcar si esta tarea es un touch-up")
    image = models.ImageField(upload_to="tasks/", blank=True, null=True, 
                             help_text="Foto del touch-up")
    schedule_item = models.ForeignKey('ScheduleItem', on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='tasks')
```

**Flujo de Creación - Staff/PM:**
```
Admin/PM crea tarea directamente:

┌────────────────────────────────────────────────────────────┐
│ ➕ CREAR TAREA                                             │
├────────────────────────────────────────────────────────────┤
│ Proyecto: [Villa Moderna ▼]                                │
│                                                            │
│ Título: [Instalar fixtures en baño principal]              │
│                                                            │
│ Descripción:                                               │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Instalar lavamanos, inodoro y regadera.                │ │
│ │ Fixtures en bodega.                                    │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Estado: [Pendiente ▼]                                      │
│ Asignar a: [Juan Pérez ▼]                                 │
│                                                            │
│ Foto (opcional): [Elegir archivo]                          │
│                                                            │
│ Es Touch-up: [  ]                                          │
│                                                            │
│ Vincular con Schedule Item: [Select ▼] (opcional)          │
│                                                            │
│ [Crear Tarea] [Cancel]                                     │
└────────────────────────────────────────────────────────────┘
```

**Flujo de Creación - Cliente:**
```
Cliente crea tarea (principalmente touch-ups):

Vista: client_create_task(request, project_id)
Proceso:
1. Cliente accede a su proyecto
2. Ve botón "Reportar Issue/Touch-up"
3. Llena formulario simple:
   ├─ Título
   ├─ Descripción
   └─ Foto (opcional)
4. Sistema auto-marca como is_touchup=True
5. Estado inicial: "Pendiente"
6. Notificación enviada a PM

┌────────────────────────────────────────────────────────────┐
│ 📸 REPORTAR TOUCH-UP                                       │
├────────────────────────────────────────────────────────────┤
│ Proyecto: Villa Moderna                                    │
│                                                            │
│ ¿Qué necesita corrección?                                  │
│ [Pintura rayada en pared de la sala]                       │
│                                                            │
│ Descripción:                                               │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ La pared junto a la ventana tiene marcas               │ │
│ │ de pintura. Parece que se rozó con muebles.            │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Foto (ayuda a entender el problema):                       │
│ [📷 Tomar foto] o [📁 Elegir archivo]                      │
│                                                            │
│ [Enviar Touch-up] [Cancel]                                 │
└────────────────────────────────────────────────────────────┘

Resultado:
✅ Touch-up creado
📧 PM notificado
🔔 "Gracias. El PM revisará y asignará a un empleado."
```

**Notificaciones:**
```python
from core.notifications import notify_task_created

# Después de crear tarea
notify_task_created(task, request.user)

# Notifica a:
├─ Project Manager del proyecto
├─ Admin/Superusers
└─ Email con link directo a la tarea
```

**Mejoras Identificadas:**
- ✅ Creación por cliente implementada
- ✅ Creación por staff implementada
- ✅ Campo is_touchup para diferenciar
- ✅ Notificaciones automáticas
- ⚠️ Falta: Prioridad (Alta, Media, Baja)
- ⚠️ Falta: Fecha límite/due date
- ⚠️ Falta: Tags/labels para categorizar

---

### 📌 FUNCIÓN 11.2 - Asignar Tarea a Empleado

**Campo assigned_to:**
```python
assigned_to = models.ForeignKey('Employee', 
                                on_delete=models.SET_NULL, 
                                null=True, blank=True,
                                related_name='assigned_tasks')
```

**Asignación Manual (PM/Admin):**
```
┌────────────────────────────────────────────────────────────┐
│ 📋 Pintura rayada en pared de la sala                      │
│ Estado: Pendiente                                          │
├────────────────────────────────────────────────────────────┤
│ Creado por: John Smith (Cliente)                           │
│ Fecha: Aug 24, 2025 2:30 PM                                │
│                                                            │
│ Descripción:                                               │
│ La pared junto a la ventana tiene marcas de pintura.       │
│ Parece que se rozó con muebles.                            │
│                                                            │
│ 📷 [Ver foto adjunta]                                      │
├────────────────────────────────────────────────────────────┤
│ 👤 ASIGNAR A:                                              │
│ [Juan Pérez ▼]                                             │
│ [Asignar y Notificar]                                      │
│                                                            │
│ Empleados disponibles:                                     │
│ • Juan Pérez (Pintor - 2 tareas pendientes)                │
│ • María García (Pintor - 1 tarea pendiente)                │
│ • Pedro López (General - 5 tareas pendientes)              │
└────────────────────────────────────────────────────────────┘

Al asignar:
1. Task.assigned_to = empleado seleccionado
2. Notificación enviada al empleado
3. Tarea aparece en morning dashboard del empleado
4. PM recibe confirmación
```

**Asignación Rápida (Touch-up Board):**
```python
@login_required
def touchup_quick_update(request, task_id):
    """AJAX endpoint for quick status/assignment updates on touch-up board."""
    task = get_object_or_404(Task, id=task_id, is_touchup=True)
    
    if action == 'assign':
        employee_id = request.POST.get('employee_id')
        if employee_id:
            employee = get_object_or_404(User, id=employee_id)
            task.assigned_to = employee
            task.save()
            return JsonResponse({'success': True, 'assigned_to': employee.username})
        else:
            # Desasignar
            task.assigned_to = None
            task.save()
            return JsonResponse({'success': True, 'assigned_to': 'Sin asignar'})
```

**Vista Touch-up Board:**
```
TOUCH-UP BOARD - Villa Moderna

┌─────────────────────┬──────────────────────┬────────────────────┐
│ PENDIENTES (3)      │ EN PROGRESO (2)      │ COMPLETADAS (5)    │
├─────────────────────┼──────────────────────┼────────────────────┤
│ 🔴 Pintura rayada   │ 🔵 Fix moldura       │ ✅ Puerta raspada  │
│    Sin asignar      │    Juan Pérez        │    María García    │
│    [Asignar ▼]      │    [Cambiar ▼]       │    Aug 20          │
│                     │                      │                    │
│ 🔴 Grieta en pared  │ 🔵 Limpiar mancha    │ ✅ Ventana sucia   │
│    Sin asignar      │    Pedro López       │    Juan Pérez      │
│    [Asignar ▼]      │    [Cambiar ▼]       │    Aug 19          │
│                     │                      │                    │
│ 🔴 Caulking faltante│                      │ ✅ Touch-up baño   │
│    Sin asignar      │                      │    María García    │
│    [Asignar ▼]      │                      │    Aug 18          │
└─────────────────────┴──────────────────────┴────────────────────┘

Acciones rápidas:
• Click en [Asignar ▼] → Dropdown con empleados
• Click en [Cambiar ▼] → Reasignar a otro empleado
• Drag & drop entre columnas para cambiar estado
```

**Mejoras Identificadas:**
- ✅ Asignación manual funcional
- ✅ Asignación rápida AJAX en touch-up board
- ✅ Notificaciones al empleado
- ⚠️ Falta: Auto-asignación basada en carga de trabajo
- ⚠️ Falta: Sugerencia de empleado basada en skills

---

### 📌 FUNCIÓN 11.3 - Vincular Tarea con Proyecto

**Campo project (FK):**
```python
project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
```

**Acceso a Tareas por Proyecto:**
```python
# Todas las tareas del proyecto
tasks = project.tasks.all()

# Solo touch-ups
touchups = project.tasks.filter(is_touchup=True)

# Tareas pendientes
pending = project.tasks.filter(status='Pendiente')

# Tareas asignadas a un empleado en este proyecto
employee_tasks = project.tasks.filter(assigned_to=employee)
```

**Vista de Tareas del Proyecto:**
```python
@login_required
def task_list_view(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id)
    tasks = Task.objects.filter(project=project).order_by("-id")
    # ... render template
```

**Dashboard del Proyecto:**
```
┌────────────────────────────────────────────────────────────┐
│ 📊 VILLA MODERNA - RESUMEN                                 │
├────────────────────────────────────────────────────────────┤
│ Budget: $50,000 | Gastado: $28,000 | Restante: $22,000    │
│ Progreso: 56% ████████████░░░░░░░░                         │
├────────────────────────────────────────────────────────────┤
│ 📋 TAREAS                                                  │
│ Total: 15 | Pendientes: 5 | En Progreso: 7 | Listas: 3    │
│                                                            │
│ Touch-ups Pendientes: 3 ⚠️                                 │
│ [Ver Touch-up Board]                                       │
├────────────────────────────────────────────────────────────┤
│ TAREAS RECIENTES:                                          │
│ 🔴 Pintura rayada - Sin asignar (Touch-up)                 │
│ 🔵 Instalar fixtures - Juan Pérez (En Progreso)            │
│ ✅ Limpiar sitio - María García (Completada)               │
│                                                            │
│ [Ver Todas las Tareas]                                     │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Vínculo con proyecto funcional
- ✅ Queries eficientes (related_name)
- ⚠️ Falta: Subtareas (tareas hijas)

---

### 📌 FUNCIÓN 11.4 - Vincular Tarea con Schedule Item

**Campo schedule_item:**
```python
schedule_item = models.ForeignKey('ScheduleItem', 
                                  on_delete=models.SET_NULL, 
                                  null=True, blank=True, 
                                  related_name='tasks')
```

**Propósito:**
```
Conectar tareas específicas con items del cronograma.
Permite:
├─ Tracking automático de progreso del schedule item
├─ Ver qué tareas componen cada fase del cronograma
└─ Calcular % completado basado en tareas terminadas
```

**Ejemplo de Vínculo:**
```
ScheduleItem: "Pintura de Interiores"
├─ Task 1: Prep walls - living room (Completada) ✅
├─ Task 2: First coat - living room (Completada) ✅
├─ Task 3: Second coat - living room (En Progreso) 🔵
├─ Task 4: Prep walls - bedroom (Pendiente) 🔴
└─ Task 5: Paint bedroom (Pendiente) 🔴

Progreso auto-calculado: 2 de 5 completadas = 40%
```

**Recálculo Automático:**
```python
# En ScheduleItem model
def recalculate_progress(self, save=True):
    """
    Calcula % según tareas vinculadas (excluye canceladas).
    """
    qs = self.tasks.exclude(status='Cancelada')
    total = qs.count()
    
    if total == 0:
        pct = 0
    else:
        done = qs.filter(status='Completada').count()
        pct = int((done / total) * 100)
    
    self.percent_complete = max(0, min(100, pct))
    
    # Auto-actualizar estado
    if self.percent_complete >= 100:
        self.status = 'DONE'
    elif qs.filter(status='En Progreso').exists():
        self.status = 'IN_PROGRESS'
    elif total > 0 and done == 0:
        self.status = 'NOT_STARTED'
    
    if save:
        self.save(update_fields=['percent_complete', 'status'])
    
    return self.percent_complete
```

**Trigger de Recálculo:**
```python
# Cuando se actualiza estado de una tarea
@receiver(post_save, sender=Task)
def update_schedule_item_progress(sender, instance, **kwargs):
    if instance.schedule_item:
        instance.schedule_item.recalculate_progress(save=True)
```

**Mejoras Identificadas:**
- ✅ Vínculo con schedule_item implementado
- ✅ Recálculo automático de progreso
- ⚠️ Falta: Signal para auto-recálculo cuando cambia tarea
- ⚠️ Falta: Vista de tareas por schedule item

---

### 📌 FUNCIÓN 11.5 - Establecer Estado de Tarea

**Estados Disponibles:**
```python
STATUS_CHOICES = [
    ('Pendiente', 'Pendiente'),      # Creada, esperando asignación
    ('En Progreso', 'En Progreso'),  # Empleado trabajando
    ('Completada', 'Completada'),    # Trabajo terminado
    ('Cancelada', 'Cancelada'),      # No se realizará
]
```

**Flujo de Estados:**
```
Pendiente → En Progreso → Completada
    ↓
Cancelada (en cualquier momento)
```

**Cambio de Estado - Manual:**
```
┌────────────────────────────────────────────────────────────┐
│ 📋 Instalar fixtures en baño                               │
├────────────────────────────────────────────────────────────┤
│ Estado actual: En Progreso                                 │
│                                                            │
│ Cambiar a:                                                 │
│ • Pendiente                                                │
│ • En Progreso ✓ (actual)                                   │
│ • Completada                                               │
│ • Cancelada                                                │
│                                                            │
│ [Actualizar Estado]                                        │
└────────────────────────────────────────────────────────────┘
```

**Cambio de Estado - Touch-up Board (AJAX):**
```python
def touchup_quick_update(request, task_id):
    if action == 'status':
        new_status = request.POST.get('status')
        if new_status in dict(Task.STATUS_CHOICES).keys():
            task.status = new_status
            if new_status == 'Completada':
                task.completed_at = timezone.now()
            task.save()
            return JsonResponse({'success': True, 'status': task.get_status_display()})
```

**Auto-timestamping:**
```
Cuando estado cambia a "Completada":
├─ completed_at = timezone.now()
├─ Notificación al PM
└─ Actualiza % de schedule_item (si vinculada)

Cuando estado cambia de "Completada" a otro:
├─ completed_at = None
└─ Recalcula % de schedule_item
```

**Vista de Estados:**
```
TAREAS POR ESTADO

┌──────────────┬───────┬─────────┐
│ Estado       │ Count │ %       │
├──────────────┼───────┼─────────┤
│ Pendiente    │   5   │  33%    │
│ En Progreso  │   7   │  47%    │
│ Completada   │   3   │  20%    │
│ Cancelada    │   0   │   0%    │
├──────────────┼───────┼─────────┤
│ TOTAL        │  15   │ 100%    │
└──────────────┴───────┴─────────┘
```

**Mejoras Identificadas:**
- ✅ Estados claros y funcionales
- ✅ Auto-timestamping de completed_at
- ✅ Cambio rápido vía AJAX
- ⚠️ Falta: Estado "Bloqueada" (esperando materiales/otro trabajo)
- ⚠️ Falta: Historial de cambios de estado
- ⚠️ Falta: Razón de cancelación (campo opcional)

---

### 📌 FUNCIÓN 11.6 - Marcar como Touch-up

**Campo is_touchup:**
```python
is_touchup = models.BooleanField(default=False, 
                                 help_text="Marcar si esta tarea es un touch-up")
```

**Touch-ups vs Tareas Regulares:**
```
TAREA REGULAR:
├─ Parte del trabajo planificado
├─ Incluida en cronograma original
├─ Asignada desde el inicio
└─ Ejemplo: "Instalar drywall en sala"

TOUCH-UP:
├─ Corrección/reparación no planeada
├─ Generalmente reportada por cliente
├─ Creada después de trabajo "completado"
├─ Requiere atención especial
└─ Ejemplo: "Pintura rayada en pared"
```

**Creación Automática como Touch-up:**
```python
# Cliente crea tarea = auto-marcada como touch-up
@login_required
def client_create_task(request, project_id):
    # ...
    task = Task.objects.create(
        project=project,
        title=title,
        description=description,
        status="Pendiente",
        created_by=request.user,
        image=image,
        is_touchup=True,  # ← Auto-marcado
    )
```

**Touch-up Board Dedicado:**
```python
@login_required
def touchup_board(request, project_id):
    """Vista dedicada para gestionar touch-ups del proyecto."""
    project = get_object_or_404(Project, id=project_id)
    qs = project.tasks.filter(is_touchup=True).select_related(
        'assigned_to', 'created_by'
    ).order_by('-created_at')
    # ... filtros y render
```

**Dashboard - Separación de Touch-ups:**
```
┌────────────────────────────────────────────────────────────┐
│ 📊 PROYECTO: VILLA MODERNA                                 │
├────────────────────────────────────────────────────────────┤
│ TAREAS REGULARES:                                          │
│ Total: 12 | Pendientes: 2 | En Progreso: 7 | Listas: 3    │
│                                                            │
│ TOUCH-UPS: ⚠️                                              │
│ Total: 8 | Pendientes: 3 | En Progreso: 2 | Listas: 3     │
│ [Ir a Touch-up Board]                                      │
└────────────────────────────────────────────────────────────┘
```

**Filtro de Touch-ups:**
```
TODAS LAS TAREAS DEL PROYECTO

Filtros:
[✓] Mostrar solo touch-ups
[  ] Excluir touch-ups
[  ] Mostrar todas

Estado: [Todos ▼]
Asignado a: [Todos ▼]

┌────────────────────────────────────────────────────────────┐
│ 🔧 Pintura rayada (Touch-up)                               │
│ Creado por: Cliente | Sin asignar | Pendiente              │
├────────────────────────────────────────────────────────────┤
│ 🔧 Moldura despegada (Touch-up)                            │
│ Creado por: Cliente | Juan Pérez | En Progreso             │
├────────────────────────────────────────────────────────────┤
│ 📋 Instalar fixtures (Regular)                             │
│ Creado por: PM | María García | Completada                 │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Campo is_touchup funcional
- ✅ Touch-up board dedicado
- ✅ Auto-marcado para tareas de cliente
- ⚠️ Falta: Métricas de touch-ups por proyecto (KPI)
- ⚠️ Falta: Reportes de touch-ups por categoría

---

### 📌 FUNCIÓN 11.7 - Agregar Imagen a la Tarea

**Campo image:**
```python
image = models.ImageField(upload_to="tasks/", blank=True, null=True, 
                         help_text="Foto del touch-up")
```

**Upload por Cliente:**
```
┌────────────────────────────────────────────────────────────┐
│ 📸 REPORTAR TOUCH-UP                                       │
├────────────────────────────────────────────────────────────┤
│ ¿Qué necesita corrección?                                  │
│ [Pintura rayada en pared]                                  │
│                                                            │
│ Descripción:                                               │
│ [La pared junto a la ventana tiene marcas...]              │
│                                                            │
│ Foto (recomendado):                                        │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [📷 Tomar Foto]  o  [📁 Elegir Archivo]                │ │
│ │                                                        │ │
│ │ ✅ pintura_rayada.jpg (2.3 MB)                         │ │
│ │ [x] Remover                                            │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Enviar Touch-up]                                          │
└────────────────────────────────────────────────────────────┘
```

**Vista de Imagen en Tarea:**
```
┌────────────────────────────────────────────────────────────┐
│ 📋 PINTURA RAYADA EN PARED                                 │
├────────────────────────────────────────────────────────────┤
│ Estado: Pendiente                                          │
│ Creado por: John Smith (Cliente)                           │
│ Fecha: Aug 24, 2025 2:30 PM                                │
│                                                            │
│ Descripción:                                               │
│ La pared junto a la ventana tiene marcas de pintura.       │
│ Parece que se rozó con muebles.                            │
│                                                            │
│ 📷 FOTO ADJUNTA:                                           │
│ ┌────────────────────────────────────────────────────────┐ │
│ │                                                        │ │
│ │         [Imagen de pared con rayones]                 │ │
│ │                                                        │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│ [Ver imagen completa] [Descargar]                          │
│                                                            │
│ 👤 Sin asignar | [Asignar a empleado ▼]                    │
└────────────────────────────────────────────────────────────┘
```

**Galería de Touch-ups:**
```
TOUCH-UPS CON FOTOS

┌─────────────┬─────────────┬─────────────┐
│ 📷          │ 📷          │ 📷          │
│ Pintura     │ Moldura     │ Grieta      │
│ rayada      │ despegada   │ en pared    │
│ Pendiente   │ En Progreso │ Completada  │
│ [Ver]       │ [Ver]       │ [Ver]       │
└─────────────┴─────────────┴─────────────┘
```

**Mejoras Identificadas:**
- ✅ Upload de imagen funcional
- ✅ Almacenamiento en media/tasks/
- ⚠️ Falta: Múltiples imágenes por tarea
- ⚠️ Falta: Imagen de "antes" y "después"
- ⚠️ Falta: Anotaciones/marcadores en la imagen
- ⚠️ Falta: Compresión automática de imágenes grandes

---

### 📌 FUNCIÓN 11.8 - Agregar Comentarios a Tareas

**Modelo Comment:**
```python
class Comment(models.Model):
    """
    Comentarios en proyectos, pueden estar asociados a tareas específicas.
    Permiten adjuntar imágenes para comunicación visual.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, 
                                related_name='comments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to="comments/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Relacionar comentario con tarea si aplica
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                            null=True, blank=True,
                            related_name='comments',
                            help_text="Tarea relacionada si este comentario es sobre una tarea específica")
```

**Flujo de Comentarios:**
```
┌────────────────────────────────────────────────────────────┐
│ 📋 PINTURA RAYADA EN PARED                                 │
├────────────────────────────────────────────────────────────┤
│ [Detalles de la tarea...]                                  │
├────────────────────────────────────────────────────────────┤
│ 💬 COMENTARIOS (3)                                         │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ PM (Aug 24, 3:00 PM):                                  │ │
│ │ "Asignado a Juan. Tiene pintura sobrante del mismo    │ │
│ │ color para el touch-up."                               │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Juan Pérez (Aug 24, 4:30 PM):                          │ │
│ │ "Pasé por el sitio. Veo el problema. Lo arreglo       │ │
│ │ mañana temprano."                                      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Cliente (Aug 25, 9:15 AM):                             │ │
│ │ "Gracias Juan! Se ve perfecto ahora. 👍"               │ │
│ │ 📷 [Imagen adjunta]                                    │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Agregar comentario:                                    │ │
│ │ ┌────────────────────────────────────────────────────┐ │ │
│ │ │ [Escribe tu comentario aquí...]                    │ │ │
│ │ └────────────────────────────────────────────────────┘ │ │
│ │ [📷 Adjuntar imagen] [Enviar]                          │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Notificaciones de Comentarios:**
```
Cuando alguien comenta en una tarea:
├─ Notificar a assigned_to (empleado asignado)
├─ Notificar a created_by (quien creó la tarea)
├─ Notificar a PM del proyecto
└─ NO notificar a quien escribió el comentario

Email:
Subject: Nuevo comentario en tarea "Pintura rayada"
Body: 
  Juan Pérez comentó:
  "Pasé por el sitio. Veo el problema. Lo arreglo mañana temprano."
  
  Ver tarea: [Link directo]
```

**Mejoras Identificadas:**
- ✅ Modelo Comment con FK a Task
- ✅ Soporte para imagen en comentario
- ⚠️ Falta: Implementación completa de vistas de comentarios
- ⚠️ Falta: Notificaciones automáticas
- ⚠️ Falta: @mentions para notificar usuarios específicos
- ⚠️ Falta: Editar/eliminar comentarios propios

---

### 📌 FUNCIÓN 11.9 - Ver Tareas por Proyecto

**Vista: task_list_view**
```python
@login_required
def task_list_view(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id)
    tasks = Task.objects.filter(project=project).order_by("-id")
    
    can_create = request.user.is_staff
    form = None
    
    if can_create and TaskForm:
        if request.method == "POST":
            form = TaskForm(request.POST, request.FILES)
            if form.is_valid():
                inst = form.save(commit=False)
                inst.created_by = request.user
                inst.project = project
                inst.save()
                messages.success(request, "Tarea creada.")
                return redirect("task_list", project_id=project.id)
        else:
            form = TaskForm(initial={"project": project})
    
    return render(request, "core/task_list.html", {
        "project": project,
        "tasks": tasks,
        "form": form,
        "can_create": can_create
    })
```

**Vista de Lista:**
```
┌────────────────────────────────────────────────────────────┐
│ 📋 TAREAS - VILLA MODERNA                                  │
├────────────────────────────────────────────────────────────┤
│ Filtros:                                                   │
│ Estado: [Todos ▼] | Asignado a: [Todos ▼]                 │
│ [✓] Incluir touch-ups | [  ] Solo touch-ups               │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ 🔴 Pintura rayada (Touch-up)                               │
│    Cliente | Sin asignar | Pendiente                       │
│    Aug 24 | [Ver] [Asignar] [Editar]                       │
│                                                            │
│ 🔵 Instalar fixtures                                       │
│    PM | Juan Pérez | En Progreso                           │
│    Aug 22 | [Ver] [Editar]                                 │
│                                                            │
│ ✅ Limpiar sitio                                           │
│    PM | María García | Completada                          │
│    Aug 20 - Completada: Aug 21 | [Ver]                     │
│                                                            │
│ 🔴 Revisar plomería                                        │
│    PM | Pedro López | Pendiente                            │
│    Aug 19 | [Ver] [Editar]                                 │
│                                                            │
│ [Mostrar más...] (Página 1 de 3)                           │
├────────────────────────────────────────────────────────────┤
│ ➕ CREAR NUEVA TAREA (Staff only)                          │
│ [Formulario de creación rápida]                            │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Vista básica funcional
- ⚠️ Falta: Filtros avanzados (fecha, prioridad)
- ⚠️ Falta: Ordenamiento (por fecha, estado, asignado)
- ⚠️ Falta: Búsqueda por texto
- ⚠️ Falta: Paginación

---

### 📌 FUNCIÓN 11.10 - Ver Tareas por Empleado

**Vista: task_list_all**
```python
@login_required
def task_list_all(request):
    """Lista de tareas asignadas al usuario actual (para empleado)."""
    tasks = Task.objects.filter(
        assigned_to=request.user
    ).select_related("project").order_by("-id")
    
    return render(request, "core/task_list_all.html", {"tasks": tasks})
```

**Morning Dashboard del Empleado:**
```
┌────────────────────────────────────────────────────────────┐
│ 🌅 BUENOS DÍAS, JUAN PÉREZ                                 │
│ Hoy es Lunes, Agosto 25, 2025                              │
├────────────────────────────────────────────────────────────┤
│ 📋 MIS TAREAS (5 pendientes)                               │
│                                                            │
│ PENDIENTES (3):                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 Pintura touch-up - Villa Moderna                    │ │
│ │    Reportado por cliente | Sin fecha límite            │ │
│ │    [Iniciar] [Ver detalles]                            │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 Revisar molduras - Casa Norte                       │ │
│ │    Asignada por PM | Vence: Aug 26                     │ │
│ │    [Iniciar] [Ver detalles]                            │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ EN PROGRESO (2):                                           │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔵 Instalar fixtures - Villa Moderna                   │ │
│ │    Iniciada: Aug 24                                    │ │
│ │    [Marcar Completada] [Ver detalles]                  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔵 Pintar cocina - Proyecto XYZ                        │ │
│ │    Iniciada: Aug 23                                    │ │
│ │    [Marcar Completada] [Ver detalles]                  │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ COMPLETADAS HOY (0)                                        │
│ [Ver todas mis tareas completadas]                         │
└────────────────────────────────────────────────────────────┘
```

**Integración con Time Tracking:**
```
Cuando empleado marca tarea como "En Progreso":
├─ Auto-sugerir clock in para el proyecto
├─ Vincular time entry con la tarea (si aplicable)
└─ Trackear tiempo dedicado a la tarea

Cuando marca como "Completada":
├─ Sugerir clock out (si está trabajando)
└─ Registrar tiempo total dedicado
```

**Mejoras Identificadas:**
- ✅ Vista básica de tareas por empleado
- ⚠️ Falta: Integración con time tracking
- ⚠️ Falta: Notificaciones push cuando se asigna tarea
- ⚠️ Falta: Vista de calendario de tareas

---

### 📌 FUNCIÓN 11.11 - Ver Tareas por Estado

**Filtrado por Estado:**
```python
# En vistas
tasks_pending = Task.objects.filter(project=project, status='Pendiente')
tasks_in_progress = Task.objects.filter(project=project, status='En Progreso')
tasks_completed = Task.objects.filter(project=project, status='Completada')
tasks_cancelled = Task.objects.filter(project=project, status='Cancelada')
```

**Vista Kanban por Estado:**
```
TABLERO DE TAREAS - Villa Moderna

┌─────────────────┬─────────────────┬─────────────────┬────────────────┐
│ PENDIENTES (5)  │ EN PROGRESO (7) │ COMPLETADAS (3) │ CANCELADAS (1) │
├─────────────────┼─────────────────┼─────────────────┼────────────────┤
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────┐ │ ┌────────────┐ │
│ │ Pintura     │ │ │ Instalar    │ │ │ Limpiar     │ │ │ Old task   │ │
│ │ rayada      │ │ │ fixtures    │ │ │ sitio       │ │ │ duplicada  │ │
│ │ Sin asignar │ │ │ Juan Pérez  │ │ │ María G.    │ │ │            │ │
│ └─────────────┘ │ └─────────────┘ │ └─────────────┘ │ └────────────┘ │
│                 │                 │                 │                │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────┐ │                │
│ │ Moldura     │ │ │ Pintar      │ │ │ Ventana     │ │                │
│ │ despegada   │ │ │ cocina      │ │ │ limpia      │ │                │
│ │ Sin asignar │ │ │ Pedro L.    │ │ │ Juan P.     │ │                │
│ └─────────────┘ │ └─────────────┘ │ └─────────────┘ │                │
│                 │                 │                 │                │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────┐ │                │
│ │ Revisar     │ │ │ Caulking    │ │ │ Touch-up    │ │                │
│ │ plomería    │ │ │ baño        │ │ │ baño        │ │                │
│ │ Pedro L.    │ │ │ María G.    │ │ │ María G.    │ │                │
│ └─────────────┘ │ └─────────────┘ │ └─────────────┘ │                │
└─────────────────┴─────────────────┴─────────────────┴────────────────┘

Drag & drop para cambiar estado
```

**Estadísticas por Estado:**
```
RESUMEN DE TAREAS

Total: 16 tareas

Por Estado:
├─ Pendientes:    5 (31%) ████████░░░░░░░░░░░░░░
├─ En Progreso:   7 (44%) █████████████░░░░░░░░░
├─ Completadas:   3 (19%) ██████░░░░░░░░░░░░░░░░
└─ Canceladas:    1 ( 6%) ██░░░░░░░░░░░░░░░░░░░░

Tasa de Completación: 19% (3 de 16)
Tiempo Promedio: 2.5 días
```

**Mejoras Identificadas:**
- ✅ Filtrado por estado funcional
- ⚠️ Falta: Vista Kanban drag & drop
- ⚠️ Falta: Estadísticas automáticas
- ⚠️ Falta: Gráficas de tendencia de estados

---

### 📌 FUNCIÓN 11.12 - Filtrar Tareas de Touch-up

**Touch-up Board con Filtros:**
```python
@login_required
def touchup_board(request, project_id):
    """Vista dedicada para gestionar touch-ups del proyecto."""
    project = get_object_or_404(Project, id=project_id)
    qs = project.tasks.filter(is_touchup=True).select_related(
        'assigned_to', 'created_by'
    ).order_by('-created_at')
    
    # Filters
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    
    assigned = request.GET.get('assigned')
    if assigned == 'unassigned':
        qs = qs.filter(assigned_to__isnull=True)
    elif assigned:
        qs = qs.filter(assigned_to__id=assigned)
    
    date_from = request.GET.get('date_from')
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['created_at', '-created_at', 'status', '-status', 
                   'assigned_to', '-assigned_to']:
        qs = qs.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'core/touchup_board.html', {
        'project': project,
        'page_obj': page_obj,
        # ... filtros
    })
```

**Interfaz de Filtros:**
```
┌────────────────────────────────────────────────────────────┐
│ 🔧 TOUCH-UP BOARD - VILLA MODERNA                          │
├────────────────────────────────────────────────────────────┤
│ FILTROS:                                                   │
│ Estado: [Todos ▼] | Asignado: [Todos ▼]                   │
│ Desde: [2025-08-01 📅] | Hasta: [2025-08-31 📅]            │
│ Ordenar por: [Más reciente ▼]                             │
│ [Aplicar Filtros] [Limpiar]                                │
├────────────────────────────────────────────────────────────┤
│ RESULTADOS (8 touch-ups):                                  │
│                                                            │
│ 🔴 Pintura rayada - Sin asignar (Aug 24)                   │
│ 🔴 Moldura despegada - Sin asignar (Aug 23)                │
│ 🔵 Fix grieta - Juan Pérez (Aug 22) - En Progreso          │
│ 🔵 Limpiar mancha - Pedro López (Aug 21) - En Progreso     │
│ ✅ Ventana sucia - María García (Aug 20) - Completada      │
│ ✅ Caulking faltante - Juan Pérez (Aug 19) - Completada    │
│ ✅ Touch-up baño - María García (Aug 18) - Completada      │
│ ✅ Puerta raspada - Juan Pérez (Aug 17) - Completada       │
│                                                            │
│ [Página 1 de 1]                                            │
└────────────────────────────────────────────────────────────┘
```

**Filtros Rápidos:**
```
Quick Filters:
├─ [Sin asignar] → assigned_to__isnull=True
├─ [Mis touch-ups] → assigned_to=current_user
├─ [Pendientes] → status='Pendiente'
├─ [Completados hoy] → status='Completada', completed_at__date=today
└─ [Urgentes] → created_at < 7 days ago AND status!='Completada'
```

**Export de Touch-ups:**
```
[Exportar a CSV]

Archivo descargado: touchups_villa_moderna_2025-08-25.csv

ID,Título,Estado,Asignado,Creado,Completado,Creado Por
1,Pintura rayada,Pendiente,,2025-08-24,,John Smith
2,Moldura despegada,Pendiente,,2025-08-23,,John Smith
3,Fix grieta,En Progreso,Juan Pérez,2025-08-22,,PM
...
```

**Mejoras Identificadas:**
- ✅ Filtros completos implementados
- ✅ Paginación funcional
- ✅ Ordenamiento múltiple
- ⚠️ Falta: Búsqueda por texto
- ⚠️ Falta: Export a CSV/PDF
- ⚠️ Falta: Saved filters (guardar configuración de filtros)

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 11**

### Mejoras CRÍTICAS:
1. 🔴 **Sistema de Prioridades**
   - Campo priority (Alta, Media, Baja)
   - Auto-priorización basada en urgencia
   - Vista ordenada por prioridad
   - Alertas de tareas alta prioridad

2. 🔴 **Sistema de Fechas Límite**
   - Campo due_date
   - Alertas cuando se acerca deadline
   - Tareas vencidas destacadas
   - Notificaciones automáticas

3. 🔴 **Sistema Completo de Comentarios**
   - Implementación de vistas
   - Notificaciones automáticas
   - @mentions
   - Editar/eliminar comentarios propios

### Mejoras Importantes:
4. ⚠️ Múltiples imágenes por tarea (galería)
5. ⚠️ Imagen antes/después
6. ⚠️ Subtareas (tareas hijas)
7. ⚠️ Tags/labels para categorización
8. ⚠️ Historial de cambios de estado
9. ⚠️ Razón de cancelación
10. ⚠️ Integración con time tracking
11. ⚠️ Auto-asignación inteligente
12. ⚠️ Notificaciones push
13. ⚠️ Vista Kanban drag & drop
14. ⚠️ Estadísticas y KPIs de touch-ups
15. ⚠️ Export a CSV/PDF
16. ⚠️ Búsqueda por texto
17. ⚠️ Saved filters
18. ⚠️ Vista de calendario
19. ⚠️ Compresión automática de imágenes
20. ⚠️ Anotaciones en imágenes

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)

**Total documentado: 121/250+ funciones (48%)**

**Pendientes:**
- ⏳ Módulos 13-27: 120+ funciones

---

## ✅ **MÓDULO 12: PLANES DIARIOS (DAILY PLANS)** (14/14 COMPLETO)

### 📌 FUNCIÓN 12.1 - Crear Plan Diario de Trabajo

**Modelo DailyPlan:**
```python
class DailyPlan(models.Model):
    """
    Daily planning document - must be created before 5pm for next working day
    Forces PMs to think ahead about activities, materials, and assignments
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved by Admin'),
        ('SKIPPED', 'No Planning Needed'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, 
                                related_name='daily_plans')
    plan_date = models.DateField(verbose_name="Date for this plan", 
                                 help_text="The work day this plan is for")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                   related_name='created_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    completion_deadline = models.DateTimeField(
        help_text="Deadline to submit plan (usually 5pm day before)"
    )
    
    # For skipped days
    no_planning_reason = models.TextField(blank=True)
    admin_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                   null=True, blank=True, 
                                   related_name='approved_plans')
    approved_at = models.DateTimeField(null=True, blank=True)
```

**Propósito:**
```
DISCIPLINA DE PLANIFICACIÓN:
├─ PM debe crear plan antes de las 5pm del día anterior
├─ Fuerza a pensar con anticipación
├─ Verifica disponibilidad de materiales
├─ Asigna empleados a actividades
└─ Evita improvisación en sitio
```

**Vista de Creación:**
```python
@login_required
def daily_plan_create(request, project_id):
    """Create a new daily plan for a project"""
    project = get_object_or_404(Project, pk=project_id)
    
    if request.method == 'POST':
        plan_date = datetime.strptime(
            request.POST.get('plan_date'), 
            '%Y-%m-%d'
        ).date()
        
        # Check if plan already exists
        existing = DailyPlan.objects.filter(
            project=project, 
            plan_date=plan_date
        ).first()
        
        if existing:
            messages.warning(request, "Plan already exists")
            return redirect('daily_plan_edit', plan_id=existing.id)
        
        # Set completion deadline (5pm day before)
        completion_deadline = timezone.make_aware(
            datetime.combine(
                plan_date - timedelta(days=1), 
                datetime.min.time().replace(hour=17)
            )
        )
        
        # Create plan
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=plan_date,
            created_by=request.user,
            completion_deadline=completion_deadline,
            status='DRAFT'
        )
        
        messages.success(request, f"Daily plan created for {plan_date}")
        return redirect('daily_plan_edit', plan_id=plan.id)
```

**Interfaz de Creación:**
```
┌────────────────────────────────────────────────────────────┐
│ 📅 CREAR PLAN DIARIO                                       │
├────────────────────────────────────────────────────────────┤
│ Proyecto: Villa Moderna                                    │
│                                                            │
│ Fecha del Plan: [2025-08-26] 📅                            │
│ (El día que se ejecutará el trabajo)                       │
│                                                            │
│ Deadline de entrega: Aug 25, 5:00 PM                       │
│ (Debe ser creado antes de esta hora)                       │
│                                                            │
│ ⚠️ IMPORTANTE:                                             │
│ • Planea con anticipación                                  │
│ • Verifica disponibilidad de materiales                    │
│ • Asigna empleados a cada actividad                        │
│ • Coordina transporte si es necesario                      │
│                                                            │
│ [Crear Plan] [Cancel]                                      │
└────────────────────────────────────────────────────────────┘
```

**Validaciones:**
```python
class Meta:
    unique_together = ['project', 'plan_date']  # Un plan por día por proyecto

def is_overdue(self):
    """Check if plan should have been submitted by now"""
    from django.utils import timezone
    return (timezone.now() > self.completion_deadline and 
            self.status == 'DRAFT')
```

**Mejoras Identificadas:**
- ✅ Sistema de deadline (5pm day before)
- ✅ Unique constraint por proyecto/fecha
- ✅ Verificación de planes overdue
- ⚠️ Falta: Notificaciones automáticas cuando se acerca deadline
- ⚠️ Falta: Recordatorios si no se ha creado plan
- ⚠️ Falta: Templates de planes por tipo de proyecto

---

### 📌 FUNCIÓN 12.2 - Asignar Fecha del Plan

**Campo plan_date:**
```python
plan_date = models.DateField(
    verbose_name="Date for this plan", 
    help_text="The work day this plan is for"
)
```

**Lógica de Fechas:**
```
HOY: Aug 24, 2025 3:00 PM

PM crea plan para: Aug 25, 2025
├─ Deadline: Aug 24, 5:00 PM ✅ (aún tiene tiempo)
└─ Status: DRAFT

PM crea plan para: Aug 26, 2025
├─ Deadline: Aug 25, 5:00 PM (mañana a las 5pm)
└─ Status: DRAFT

Si son las 6:00 PM y plan de mañana no está:
├─ Plan está OVERDUE
├─ Alerta al Admin
└─ PM debe explicar por qué no hay plan
```

**Vista de Calendario:**
```
PLANES DIARIOS - AGOSTO 2025

┌────┬────┬────┬────┬────┬────┬────┐
│ Dom│ Lun│ Mar│ Mié│ Jue│ Vie│ Sáb│
├────┼────┼────┼────┼────┼────┼────┤
│    │    │    │    │  1 │  2 │  3 │
│    │    │    │    │ ✅ │ ✅ │    │
├────┼────┼────┼────┼────┼────┼────┤
│  4 │  5 │  6 │  7 │  8 │  9 │ 10 │
│    │ ✅ │ ✅ │ ✅ │ ✅ │ ✅ │    │
├────┼────┼────┼────┼────┼────┼────┤
│ 11 │ 12 │ 13 │ 14 │ 15 │ 16 │ 17 │
│    │ ✅ │ ✅ │ ⚠️ │ 🔴 │    │    │
└────┴────┴────┴────┴────┴────┴────┘

Leyenda:
✅ = Plan completado y aprobado
⚠️ = Plan en borrador (aún a tiempo)
🔴 = Plan overdue (pasó deadline)
    = Sin plan (día no laborable)
```

**Mejoras Identificadas:**
- ✅ Campo plan_date funcional
- ⚠️ Falta: Vista de calendario visual
- ⚠️ Falta: Bulk creation (crear planes para semana completa)

---

### 📌 FUNCIÓN 12.3 - Establecer Estado del Plan

**Estados del Plan:**
```python
STATUS_CHOICES = [
    ('DRAFT', 'Draft'),             # PM trabajando en el plan
    ('SUBMITTED', 'Submitted'),     # PM envió para aprobación
    ('APPROVED', 'Approved by Admin'), # Admin aprobó
    ('SKIPPED', 'No Planning Needed'), # No hay trabajo ese día
]
```

**Flujo de Estados:**
```
DRAFT → SUBMITTED → APPROVED
   ↓
SKIPPED (si no hay trabajo)
```

**Transiciones de Estado:**
```python
# PM submits plan
if action == 'submit':
    plan.status = 'SUBMITTED'
    plan.save()
    # Notificar a Admin
    notify_plan_submitted(plan)
    messages.success(request, "Plan submitted successfully!")

# Admin approves
if action == 'approve':
    plan.status = 'APPROVED'
    plan.admin_approved = True
    plan.approved_by = request.user
    plan.approved_at = timezone.now()
    plan.save()
    # Notificar a PM y empleados
    notify_plan_approved(plan)
```

**Dashboard de Estados:**
```
┌────────────────────────────────────────────────────────────┐
│ 📊 PLANES ESTA SEMANA                                      │
├────────────────────────────────────────────────────────────┤
│ Lunes Aug 25:                                              │
│ ├─ Villa Moderna: ✅ APPROVED (4 actividades)              │
│ ├─ Casa Norte: ⚠️ SUBMITTED (esperando aprobación)         │
│ └─ Office Complex: 🔴 DRAFT (overdue - vence 6pm ayer)     │
│                                                            │
│ Martes Aug 26:                                             │
│ ├─ Villa Moderna: ✏️ DRAFT (creado, en edición)            │
│ └─ Casa Norte: ⏸️ Sin plan aún                             │
│                                                            │
│ Miércoles Aug 27:                                          │
│ └─ Todos los proyectos: ⏸️ Sin planes aún                  │
└────────────────────────────────────────────────────────────┘

[Crear Nuevo Plan] [Ver Planes Overdue]
```

**Skip Day (No Planning):**
```
Cuando no hay trabajo ese día:

┌────────────────────────────────────────────────────────────┐
│ 🚫 MARCAR DÍA SIN PLANIFICACIÓN                            │
├────────────────────────────────────────────────────────────┤
│ Fecha: Aug 28, 2025                                        │
│ Proyecto: Villa Moderna                                    │
│                                                            │
│ Razón:                                                     │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Esperando inspección de la ciudad.                     │ │
│ │ No se puede trabajar hasta recibir aprobación.         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Marcar como Skip] [Cancel]                                │
└────────────────────────────────────────────────────────────┘

Resultado:
• Status = 'SKIPPED'
• no_planning_reason = filled
• No requiere actividades
• Admin puede ver razón
```

**Mejoras Identificadas:**
- ✅ Estados claros y lógicos
- ✅ Workflow de aprobación
- ✅ Option para skip days
- ⚠️ Falta: Razones predefinidas para skip
- ⚠️ Falta: Reject plan (Admin devuelve a PM)

---

### 📌 FUNCIÓN 12.4 - Registrar Clima del Día

**Campo weather (opcional):**
```python
# En modelo DailyPlan (añadir)
weather_condition = models.CharField(
    max_length=50,
    choices=[
        ('sunny', 'Soleado'),
        ('cloudy', 'Nublado'),
        ('rainy', 'Lluvioso'),
        ('stormy', 'Tormenta'),
    ],
    blank=True,
    help_text="Condición del clima que afecta el trabajo"
)
temperature = models.IntegerField(
    null=True, 
    blank=True,
    help_text="Temperatura en °F"
)
weather_notes = models.TextField(
    blank=True,
    help_text="Notas sobre cómo el clima afectó el trabajo"
)
```

**Uso:**
```
El clima afecta:
├─ Trabajo exterior (pintura, techado, etc.)
├─ Productividad del equipo
├─ Decisión de posponer actividades
└─ Justificación de retrasos

Ejemplo:
Fecha: Aug 25
Clima: Lluvioso ☔
Temp: 68°F
Notas: "Pospusimos pintura exterior. Trabajamos en interiores."
```

**Vista en Plan:**
```
┌────────────────────────────────────────────────────────────┐
│ 📅 PLAN DIARIO - Aug 25, 2025                              │
│ Proyecto: Villa Moderna                                    │
├────────────────────────────────────────────────────────────┤
│ 🌤️ CLIMA:                                                  │
│ Condición: Soleado ☀️                                      │
│ Temperatura: 75°F                                          │
│ Notas: Día perfecto para trabajo exterior                  │
├────────────────────────────────────────────────────────────┤
│ ACTIVIDADES (5):                                           │
│ [Lista de actividades...]                                  │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ⚠️ Falta: Campos de clima en modelo (actualmente no existen)
- ⚠️ Falta: Integración con API de clima (auto-populate)
- ⚠️ Falta: Alertas si pronóstico es malo

---

### 📌 FUNCIÓN 12.5 - Agregar Notas Generales

**Campo general_notes:**
```python
# En modelo DailyPlan (añadir)
general_notes = models.TextField(
    blank=True,
    help_text="Notas generales del PM sobre el día"
)
client_notes = models.TextField(
    blank=True,
    help_text="Notas visibles para el cliente"
)
```

**Uso de Notas:**
```
NOTAS GENERALES (Internas):
├─ Coordinación con otros contractors
├─ Problemas encontrados
├─ Cambios de último minuto
└─ Recordatorios para el equipo

NOTAS PARA CLIENTE:
├─ Resumen del trabajo planeado
├─ Expectativas del día
├─ Áreas a evitar
└─ Actualizaciones de progreso
```

**Interfaz:**
```
┌────────────────────────────────────────────────────────────┐
│ 📝 NOTAS DEL PLAN                                          │
├────────────────────────────────────────────────────────────┤
│ Notas Generales (Internas):                                │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ • Electricista viene 2pm para rough-in                 │ │
│ │ • Recordar traer escalera de 12 pies                   │ │
│ │ • Material extra está en bodega, no en sitio           │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Notas para Cliente:                                        │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Hoy terminaremos el drywall de la sala y comenzaremos │ │
│ │ la cocina. Por favor mantener el área libre de        │ │
│ │ muebles. Estimamos terminar a las 4pm.                │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ⚠️ Falta: Campos de notas en modelo
- ⚠️ Falta: Rich text editor para notas
- ⚠️ Falta: Templates de notas comunes

---

### 📌 FUNCIÓN 12.6 - Crear Actividades Planeadas

**Modelo PlannedActivity:**
```python
class PlannedActivity(models.Model):
    """Individual activity within a daily plan"""
    STATUS_CHOICES = [
        ('PENDING', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('BLOCKED', 'Blocked'),
    ]
    
    daily_plan = models.ForeignKey(DailyPlan, on_delete=models.CASCADE, 
                                   related_name='activities')
    
    # Optional links
    schedule_item = models.ForeignKey(Schedule, on_delete=models.SET_NULL, 
                                     null=True, blank=True)
    activity_template = models.ForeignKey(ActivityTemplate, 
                                         on_delete=models.SET_NULL,
                                         null=True, blank=True)
    
    # Activity details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    # Assignment
    assigned_employees = models.ManyToManyField(Employee, 
                                               related_name='assigned_activities')
    is_group_activity = models.BooleanField(default=True)
    
    # Planning
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, 
                                         null=True, blank=True)
    materials_needed = models.JSONField(default=list)
    materials_checked = models.BooleanField(default=False)
    material_shortage = models.BooleanField(default=False)
    
    # Progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                             default='PENDING')
    progress_percentage = models.IntegerField(default=0)
```

**Creación de Actividad:**
```python
@login_required
def daily_plan_edit(request, plan_id):
    if request.method == 'POST' and action == 'add_activity':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        template_id = request.POST.get('activity_template')
        estimated_hours = request.POST.get('estimated_hours')
        
        # Get next order number
        max_order = plan.activities.aggregate(Max('order'))['order__max'] or 0
        
        activity = PlannedActivity.objects.create(
            daily_plan=plan,
            title=title,
            description=description,
            order=max_order + 1,
            estimated_hours=Decimal(estimated_hours) if estimated_hours else None,
            activity_template_id=template_id if template_id else None,
        )
        
        # Assign employees
        employee_ids = request.POST.getlist('assigned_employees')
        if employee_ids:
            activity.assigned_employees.set(employee_ids)
        
        messages.success(request, f"Activity '{title}' added")
```

**Interfaz de Creación:**
```
┌────────────────────────────────────────────────────────────┐
│ ➕ AGREGAR ACTIVIDAD AL PLAN                               │
├────────────────────────────────────────────────────────────┤
│ Título: [Instalar drywall en sala]                         │
│                                                            │
│ Descripción:                                               │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Paredes perimetrales y cielo. Usar tornillos 1 1/4"   │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Usar Template (SOP): [Drywall Installation ▼] (opcional)   │
│                                                            │
│ Vincular con Schedule: [Drywall - Living Room ▼] (opcional)│
│                                                            │
│ Horas Estimadas: [6.5] hrs                                 │
│                                                            │
│ Asignar Empleados:                                         │
│ [✓] Juan Pérez                                             │
│ [✓] Pedro López                                            │
│ [  ] María García                                          │
│                                                            │
│ Materiales Necesarios:                                     │
│ [+ Agregar material]                                       │
│ • Drywall 4x8 sheets (25 unidades)                         │
│ • Tornillos 1 1/4" (1 caja)                                │
│ • Joint compound (2 galones)                               │
│                                                            │
│ [Agregar Actividad] [Cancel]                               │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Modelo robusto con múltiples vínculos
- ✅ Asignación de múltiples empleados
- ✅ Lista de materiales JSON
- ⚠️ Falta: UI mejorada para agregar materiales
- ⚠️ Falta: Sugerencias de tiempo basadas en historical data

---

### 📌 FUNCIÓN 12.7 - Asignar Actividades a Empleados

**Campo assigned_employees (ManyToMany):**
```python
assigned_employees = models.ManyToManyField(
    Employee,
    related_name='assigned_activities',
    help_text="Employees assigned to this activity"
)
is_group_activity = models.BooleanField(
    default=True,
    help_text="True if all work together, False if divided into sub-tasks"
)
```

**Asignación Múltiple:**
```
ACTIVIDAD: Instalar drywall en sala

Empleados Asignados:
├─ Juan Pérez (Lead)
├─ Pedro López (Helper)
└─ María García (Helper)

Tipo: Group Activity ✓
└─ Todos trabajan juntos en la misma tarea

VS.

Tipo: Divided Activity
└─ Juan: Paredes
└─ Pedro: Cielo
└─ María: Cleanup
```

**Vista en Morning Dashboard:**
```
BUENOS DÍAS, JUAN PÉREZ
Aug 25, 2025

TUS ACTIVIDADES HOY:

┌────────────────────────────────────────────────────────────┐
│ 1. Instalar drywall en sala                                │
│    Proyecto: Villa Moderna                                 │
│    Equipo: Juan (tú), Pedro, María                         │
│    Tiempo estimado: 6.5 hrs                                │
│    ────────────────────────────────────────────────────────│
│    Descripción:                                            │
│    Paredes perimetrales y cielo. Usar tornillos 1 1/4"    │
│    ────────────────────────────────────────────────────────│
│    Materiales:                                             │
│    ✅ Drywall sheets (verificado)                          │
│    ✅ Tornillos (verificado)                               │
│    ✅ Joint compound (verificado)                          │
│    ────────────────────────────────────────────────────────│
│    [Ver SOP] [Iniciar] [Marcar Completada]                 │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ 2. Preparar área para pintura                              │
│    Proyecto: Casa Norte                                    │
│    Equipo: Solo tú                                         │
│    [...]                                                   │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ ManyToMany funcional
- ✅ Distinción entre group vs divided work
- ⚠️ Falta: Roles específicos por empleado (lead, helper)
- ⚠️ Falta: Estimación de tiempo por empleado

---

### 📌 FUNCIÓN 12.8 - Usar Plantillas de Actividades (SOPs)

**Modelo ActivityTemplate:**
```python
class ActivityTemplate(models.Model):
    """
    SOP (Standard Operating Procedure) - Template for common activities
    Used to standardize tasks and educate team
    """
    CATEGORY_CHOICES = [
        ('PREP', 'Preparation'),
        ('COVER', 'Covering'),
        ('SAND', 'Sanding'),
        ('STAIN', 'Staining'),
        ('SEAL', 'Sealing'),
        ('PAINT', 'Painting'),
        ('CAULK', 'Caulking'),
        ('CLEANUP', 'Cleanup'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    
    # SOP Details
    time_estimate = models.DecimalField(max_digits=5, decimal_places=2, 
                                       null=True, blank=True)
    steps = models.JSONField(default=list, 
                            help_text="['Step 1', 'Step 2']")
    materials_list = models.JSONField(default=list)
    tools_list = models.JSONField(default=list)
    tips = models.TextField(blank=True)
    common_errors = models.TextField(blank=True)
    
    # Media
    reference_photos = models.JSONField(default=list)
    video_url = models.URLField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
```

**Ejemplo de SOP:**
```
┌────────────────────────────────────────────────────────────┐
│ 📚 SOP: DRYWALL INSTALLATION                               │
├────────────────────────────────────────────────────────────┤
│ Categoría: PREP                                            │
│ Tiempo Estimado: 6-8 hrs (sala estándar)                   │
├────────────────────────────────────────────────────────────┤
│ PASOS:                                                     │
│ 1. Medir y marcar ubicación de sheets                      │
│ 2. Cortar sheets al tamaño necesario                       │
│ 3. Posicionar y nivelar primer sheet                       │
│ 4. Atornillar cada 8" en studs                             │
│ 5. Continuar con sheets adyacentes                         │
│ 6. Aplicar joint tape en costuras                          │
│ 7. Primera capa de mud                                     │
├────────────────────────────────────────────────────────────┤
│ MATERIALES NECESARIOS:                                     │
│ • Drywall sheets 4x8                                       │
│ • Tornillos 1 1/4" para drywall                            │
│ • Joint compound (mud)                                     │
│ • Joint tape                                               │
├────────────────────────────────────────────────────────────┤
│ HERRAMIENTAS:                                              │
│ • Taladro/drill                                            │
│ • T-square                                                 │
│ • Utility knife                                            │
│ • Drywall saw                                              │
│ • Nivel                                                    │
├────────────────────────────────────────────────────────────┤
│ 💡 TIPS:                                                   │
│ • Siempre cortar sheets en área bien ventilada             │
│ • Usar dos personas para sheets de cielo                   │
│ • Tornillos deben quedar ligeramente hundidos               │
│ • No sobre-apretar (puede romper papel)                    │
├────────────────────────────────────────────────────────────┤
│ ⚠️ ERRORES COMUNES:                                        │
│ • Tornillos muy separados (causa pandeo)                   │
│ • Sheets mal alineados (problemas en mudding)              │
│ • No verificar nivel (paredes chuecas)                     │
├────────────────────────────────────────────────────────────┤
│ 📹 VIDEO TUTORIAL:                                         │
│ https://youtube.com/watch?v=drywall_basics                 │
│                                                            │
│ 📷 FOTOS DE REFERENCIA:                                    │
│ [Ver galería de 8 fotos]                                   │
└────────────────────────────────────────────────────────────┘

[Usar este SOP] [Editar] [Eliminar]
```

**Uso en Plan Diario:**
```
Cuando PM crea actividad:
1. Selecciona SOP de dropdown
2. Sistema auto-llena:
   ├─ Tiempo estimado
   ├─ Lista de materiales
   ├─ Descripción básica
   └─ Steps (checklist)
3. PM puede ajustar según necesidad específica
4. Empleado ve SOP completo en su dashboard
```

**Beneficios:**
```
✅ Estandarización de procesos
✅ Entrenamiento de nuevos empleados
✅ Estimaciones consistentes
✅ Recordatorio de materiales
✅ Menos errores
✅ Base de conocimiento del equipo
```

**Mejoras Identificadas:**
- ✅ Modelo SOP completo y robusto
- ✅ Integración con PlannedActivity
- ⚠️ Falta: Versionado de SOPs
- ⚠️ Falta: Tracking de quién usó qué SOP
- ⚠️ Falta: Feedback de empleados sobre SOPs

---

### 📌 FUNCIÓN 12.9 - Estimar Horas por Actividad

**Campo estimated_hours:**
```python
estimated_hours = models.DecimalField(
    max_digits=5,
    decimal_places=2,
    null=True,
    blank=True
)
```

**Fuentes de Estimación:**
```
1. SOP Template:
   └─ Si actividad usa SOP, auto-llena tiempo estimado

2. Historical Data:
   └─ Sistema calcula promedio de actividades similares pasadas

3. Manual:
   └─ PM ingresa basado en experiencia

4. AI Suggestion (futuro):
   └─ Machine learning basado en históricos del proyecto
```

**Uso de Estimaciones:**
```
PLANIFICACIÓN DEL DÍA:

Actividades:
1. Drywall installation - 6.5 hrs (Juan, Pedro, María)
2. Paint prep - 2 hrs (Juan solo)
3. Material pickup - 1 hr (Pedro solo)
4. Cleanup - 0.5 hrs (todos)
────────────────────────────────────
TOTAL: 10 hrs de trabajo planeado

Empleados disponibles: 3
Horas disponibles: 8 hrs/persona = 24 hrs totales
Utilización: 10/24 = 42% ✅ (hay capacidad)

Si total > horas disponibles:
⚠️ ALERTA: Día sobre-planificado
Sugerencia: Priorizar o agregar empleados
```

**Comparación Real vs Estimado:**
```
ACTIVIDAD: Drywall Installation

Estimado: 6.5 hrs
Real: 7.2 hrs
Varianza: +0.7 hrs (+11%)

Razón: Había más cuts complicados de lo esperado

→ Actualizar SOP con estimado más realista
→ Mejorar estimaciones futuras
```

**Mejoras Identificadas:**
- ✅ Campo de estimación funcional
- ⚠️ Falta: Auto-populate desde SOP
- ⚠️ Falta: Historical averages
- ⚠️ Falta: Tracking de estimado vs real
- ⚠️ Falta: Alertas de sobre-planificación

---

### 📌 FUNCIÓN 12.10 - Registrar Horas Reales

**Integración con TimeEntry:**
```
Cuando empleado completa actividad:
1. Sistema crea TimeEntry automáticamente
2. Vincula con proyecto y empleado
3. Calcula horas trabajadas
4. Compara con estimado

PlannedActivity ← ActivityCompletion → TimeEntry
```

**Modelo ActivityCompletion:**
```python
class ActivityCompletion(models.Model):
    """Record of completed activity with photos and notes"""
    planned_activity = models.OneToOneField(PlannedActivity, 
                                           on_delete=models.CASCADE,
                                           related_name='completion')
    completed_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, 
                                    null=True)
    completion_datetime = models.DateTimeField(auto_now_add=True)
    
    completion_photos = models.JSONField(default=list)
    employee_notes = models.TextField(blank=True)
    progress_percentage = models.IntegerField(default=100)
    
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                   null=True, blank=True,
                                   related_name='verified_completions')
    verified_at = models.DateTimeField(null=True, blank=True)
```

**Proceso de Completion:**
```python
@login_required
def activity_complete(request, activity_id):
    """Mark an activity as complete with photos"""
    activity = get_object_or_404(PlannedActivity, pk=activity_id)
    employee = request.user.employee
    
    if request.method == 'POST':
        progress = int(request.POST.get('progress', 100))
        notes = request.POST.get('notes', '')
        photos = []  # Upload photos
        
        # Create completion record
        completion = ActivityCompletion.objects.create(
            planned_activity=activity,
            completed_by=employee,
            progress_percentage=progress,
            employee_notes=notes,
            completion_photos=photos
        )
        
        # Update activity status
        activity.status = 'COMPLETED'
        activity.progress_percentage = progress
        activity.save()
        
        # Create TimeEntry (auto-calculate hours)
        start_of_day = timezone.now().replace(hour=7, minute=0)
        TimeEntry.objects.create(
            employee=employee,
            project=activity.daily_plan.project,
            date=activity.daily_plan.plan_date,
            clock_in=start_of_day,
            clock_out=timezone.now(),
            notes=f"Completed: {activity.title}"
        )
        
        messages.success(request, "Activity completed!")
        return redirect('employee_morning_dashboard')
```

**Vista de Completion:**
```
┌────────────────────────────────────────────────────────────┐
│ ✅ MARCAR ACTIVIDAD COMPLETADA                             │
├────────────────────────────────────────────────────────────┤
│ Actividad: Instalar drywall en sala                        │
│ Proyecto: Villa Moderna                                    │
│                                                            │
│ Progreso: [████████████████████] 100%                      │
│ (Ajustar si no se completó al 100%)                        │
│                                                            │
│ Notas (internas):                                          │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Todo instalado según plan. Tuvimos que hacer más      │ │
│ │ cortes de lo esperado debido a ventanas.              │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Fotos del Trabajo Completado:                              │
│ [📷 Tomar fotos] (mínimo 2, máximo 10)                     │
│ ┌─────┬─────┬─────┐                                       │
│ │ 📷  │ 📷  │ 📷  │                                       │
│ └─────┴─────┴─────┘                                       │
│                                                            │
│ Tiempo Real:                                               │
│ Inicio: 7:30 AM                                            │
│ Fin: 3:15 PM                                               │
│ Total: 7.75 hrs                                            │
│ (vs estimado: 6.5 hrs = +1.25 hrs)                         │
│                                                            │
│ [Marcar Completada] [Guardar Progreso Parcial]             │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Completion record implementado
- ✅ Fotos de evidencia
- ⚠️ Falta: Auto-crear TimeEntry vinculado
- ⚠️ Falta: Tracking automático de tiempo real
- ⚠️ Falta: Análisis de varianzas

---

### 📌 FUNCIÓN 12.11 - Marcar Actividades como Completadas

Ya documentado en 12.10 (es parte del mismo proceso)

---

### 📌 FUNCIÓN 12.12 - Dashboard de Planes Diarios

**Vista: daily_planning_dashboard**
```python
@login_required
def daily_planning_dashboard(request):
    """Main dashboard for daily planning"""
    today = timezone.now().date()
    
    # Recent plans
    recent_plans = DailyPlan.objects.select_related(
        'project', 'created_by'
    ).order_by('-plan_date')[:20]
    
    # Overdue plans (draft plans past 5pm deadline)
    overdue_plans = DailyPlan.objects.filter(
        status='DRAFT',
        completion_deadline__lt=timezone.now()
    ).select_related('project', 'created_by')
    
    # Today's plans
    todays_plans = DailyPlan.objects.filter(
        plan_date=today
    ).select_related('project')
    
    # Active projects for creating new plans
    active_projects = Project.objects.filter(
        Q(end_date__gte=today) | Q(end_date__isnull=True)
    ).order_by('name')
    
    return render(request, 'core/daily_planning_dashboard.html', {
        'recent_plans': recent_plans,
        'overdue_plans': overdue_plans,
        'todays_plans': todays_plans,
        'active_projects': active_projects,
        'today': today,
    })
```

**Interfaz del Dashboard:**
```
┌────────────────────────────────────────────────────────────┐
│ 📅 DASHBOARD DE PLANIFICACIÓN DIARIA                       │
├────────────────────────────────────────────────────────────┤
│ HOY: Aug 25, 2025                                          │
├────────────────────────────────────────────────────────────┤
│ ⚠️ PLANES OVERDUE (2)                                      │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 Villa Moderna - Aug 25                              │ │
│ │    Deadline: Aug 24, 5:00 PM (overdue 14 hrs)          │ │
│ │    [Completar Ahora]                                   │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 Office Complex - Aug 26                             │ │
│ │    Deadline: Aug 25, 5:00 PM (overdue 2 hrs)           │ │
│ │    [Completar Ahora]                                   │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ ✅ PLANES DE HOY (3)                                       │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Villa Moderna                                          │ │
│ │ 4 actividades | 3 empleados | Status: APPROVED         │ │
│ │ [Ver Plan] [Morning Briefing]                          │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Casa Norte                                             │ │
│ │ 2 actividades | 2 empleados | Status: SUBMITTED        │ │
│ │ [Aprobar] [Ver Plan]                                   │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Remodel Home                                           │ │
│ │ SKIPPED - Esperando inspección                         │ │
│ │ [Ver Razón]                                            │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ 📋 PLANES RECIENTES                                        │
│ Aug 26: 1 plan creado, 2 pendientes                        │
│ Aug 27: 0 planes (⚠️ crear pronto)                         │
│ Aug 28: 0 planes                                           │
│                                                            │
│ [Ver Todos] [Calendario]                                   │
├────────────────────────────────────────────────────────────┤
│ ➕ CREAR NUEVO PLAN                                        │
│ Proyecto: [Select ▼] Fecha: [📅] [Crear]                  │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Dashboard funcional con alertas
- ✅ Vista de planes overdue
- ✅ Creación rápida de planes
- ⚠️ Falta: Gráficas de cumplimiento de deadlines
- ⚠️ Falta: Estadísticas de productividad

---

### 📌 FUNCIÓN 12.13 - Vista de Empleado (Morning Dashboard)

**Vista: employee_morning_dashboard**
```python
@login_required
def employee_morning_dashboard(request):
    """Dashboard for employees to see their daily plan"""
    employee = request.user.employee
    today = timezone.now().date()
    
    # Today's activities assigned to this employee
    todays_activities = PlannedActivity.objects.filter(
        daily_plan__plan_date=today,
        assigned_employees=employee,
        status__in=['PENDING', 'IN_PROGRESS']
    ).select_related(
        'daily_plan__project',
        'activity_template'
    ).prefetch_related('assigned_employees').order_by('order')
    
    return render(request, 'core/employee_morning_dashboard.html', {
        'employee': employee,
        'today': today,
        'activities': todays_activities,
    })
```

**Interfaz Morning Dashboard:**
```
┌────────────────────────────────────────────────────────────┐
│ 🌅 BUENOS DÍAS, JUAN PÉREZ                                 │
│ Lunes, Agosto 25, 2025                                     │
├────────────────────────────────────────────────────────────┤
│ 📋 TUS ACTIVIDADES HOY (3)                                 │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 1️⃣ INSTALAR DRYWALL EN SALA                            │ │
│ │    Villa Moderna                                       │ │
│ │    ⏱️ 6.5 hrs estimadas                                 │ │
│ │    👥 Con: Pedro López, María García                    │ │
│ │    ──────────────────────────────────────────────────  │ │
│ │    📋 PASOS (del SOP):                                 │ │
│ │    1. ☐ Medir y marcar ubicación                       │ │
│ │    2. ☐ Cortar sheets                                  │ │
│ │    3. ☐ Posicionar y nivelar                           │ │
│ │    4. ☐ Atornillar en studs                            │ │
│ │    5. ☐ Aplicar joint tape                             │ │
│ │    ──────────────────────────────────────────────────  │ │
│ │    📦 MATERIALES:                                      │ │
│ │    ✅ Drywall sheets (25 pcs)                          │ │
│ │    ✅ Tornillos 1 1/4" (1 caja)                        │ │
│ │    ✅ Joint compound (2 gal)                           │ │
│ │    ──────────────────────────────────────────────────  │ │
│ │    💡 TIPS:                                            │ │
│ │    • Usar dos personas para sheets de cielo            │ │
│ │    • Tornillos ligeramente hundidos                    │ │
│ │    ──────────────────────────────────────────────────  │ │
│ │    [📖 Ver SOP Completo] [▶️ Iniciar] [✅ Completar]   │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 2️⃣ PREPARAR ÁREA PARA PINTURA                          │ │
│ │    Casa Norte                                          │ │
│ │    ⏱️ 2 hrs | 👤 Solo tú                                │ │
│ │    [Ver detalles]                                      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 3️⃣ CLEANUP FINAL                                       │ │
│ │    Villa Moderna                                       │ │
│ │    ⏱️ 0.5 hrs | 👥 Con todo el equipo                   │ │
│ │    [Ver detalles]                                      │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ 🎯 TOTAL HOY: 9 hrs de trabajo planeado                    │
│                                                            │
│ 📍 UBICACIONES:                                            │
│ • Villa Moderna: 123 Oak St (7am-3pm)                      │
│ • Casa Norte: 456 Elm Ave (3:30pm-5pm)                     │
│                                                            │
│ 🚗 COORDINACIÓN:                                           │
│ • Salir juntos a las 6:45am del shop                       │
│ • Llevar escalera de 12 pies                               │
└────────────────────────────────────────────────────────────┘
```

**Beneficios:**
```
✅ Empleado sabe exactamente qué hacer
✅ No hay confusión ni tiempo perdido
✅ Materiales verificados antes de llegar
✅ SOPs accesibles en el momento
✅ Puede reportar progreso fácilmente
```

**Mejoras Identificadas:**
- ✅ Vista dedicada para empleados
- ✅ Muestra actividades del día
- ✅ Acceso a SOPs
- ⚠️ Falta: App móvil (más conveniente en sitio)
- ⚠️ Falta: Modo offline
- ⚠️ Falta: GPS tracking de ubicación

---

### 📌 FUNCIÓN 12.14 - Alertas de Planes Incompletos

**Sistema de Alertas:**
```python
# En daily_planning_dashboard
overdue_plans = DailyPlan.objects.filter(
    status='DRAFT',
    completion_deadline__lt=timezone.now()
).select_related('project', 'created_by')

# Notificaciones automáticas
if overdue_plans.exists():
    # Email a Admin
    send_overdue_plans_alert(admin_users, overdue_plans)
    
    # Email al PM responsable
    for plan in overdue_plans:
        send_pm_reminder(plan.created_by, plan)
```

**Tipos de Alertas:**
```
1. RECORDATORIO (4pm día anterior):
   "Recordatorio: Debes crear plan para mañana antes de 5pm"

2. ALERTA INMINENTE (4:45pm):
   "⚠️ Solo 15 minutos para completar plan de mañana"

3. OVERDUE (después de 5pm):
   "🔴 PLAN OVERDUE: Plan para mañana no fue creado"

4. MISSING PLANS (9am):
   "⚠️ Faltan planes para los próximos 3 días"

5. MATERIAL SHORTAGE (al crear plan):
   "⚠️ Materiales insuficientes para 2 actividades"
```

**Vista de Alertas:**
```
┌────────────────────────────────────────────────────────────┐
│ 🔔 ALERTAS DE PLANIFICACIÓN                                │
├────────────────────────────────────────────────────────────┤
│ 🔴 CRÍTICO (2):                                            │
│ • Plan para Villa Moderna (Aug 25) overdue 14 hrs          │
│ • Plan para Office Complex (Aug 26) overdue 2 hrs          │
│                                                            │
│ ⚠️ ADVERTENCIAS (3):                                       │
│ • Faltan planes para Aug 27 (2 proyectos)                  │
│ • Material shortage en plan de Casa Norte                   │
│ • Sobre-planificación: 10 hrs con solo 8 hrs disponibles   │
│                                                            │
│ ℹ️ INFORMACIÓN (1):                                        │
│ • Nuevo SOP disponible: "Cabinet Installation"             │
└────────────────────────────────────────────────────────────┘

[Resolver Ahora] [Ver Todas] [Configurar Notificaciones]
```

**Email de Alerta:**
```
Subject: 🔴 PLAN DIARIO OVERDUE - Villa Moderna

Hola Juan,

El plan diario para Villa Moderna del día Aug 25 está overdue.

Deadline: Aug 24, 5:00 PM
Tiempo overdue: 14 horas

Por favor completa el plan lo antes posible o contacta al Admin 
si hay alguna razón válida para el retraso.

[Completar Plan Ahora]

---
Sistema de Planificación Kibray
```

**Mejoras Identificadas:**
- ✅ Detección de planes overdue funcional
- ⚠️ Falta: Sistema de notificaciones automáticas
- ⚠️ Falta: Escalation rules (si PM no responde)
- ⚠️ Falta: Dashboard de alertas centralizado
- ⚠️ Falta: Configuración de preferencias de notificación

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 12**

### Mejoras CRÍTICAS:
1. 🔴 **Sistema de Notificaciones Automáticas**
   - Recordatorios antes de deadline
   - Alertas de overdue
   - Email/SMS a PMs
   - Escalation a Admin

2. 🔴 **App Móvil para Empleados**
   - Morning dashboard en móvil
   - Modo offline
   - Fotos desde el sitio
   - GPS tracking

3. 🔴 **Auto-integración con TimeEntry**
   - Crear time entries desde completions
   - Tracking automático de horas reales
   - Comparación estimado vs real

### Mejoras Importantes:
4. ⚠️ Campos de clima (weather tracking)
5. ⚠️ Notas generales y para cliente
6. ⚠️ Templates de planes por tipo de proyecto
7. ⚠️ Bulk creation de planes (semana completa)
8. ⚠️ Vista de calendario visual
9. ⚠️ Auto-populate tiempo desde SOP
10. ⚠️ Historical averages para estimaciones
11. ⚠️ Alertas de sobre-planificación
12. ⚠️ Versionado de SOPs
13. ⚠️ Feedback de empleados sobre SOPs
14. ⚠️ Reject plan (Admin → PM)
15. ⚠️ Gráficas de cumplimiento
16. ⚠️ Estadísticas de productividad
17. ⚠️ Integración con API de clima
18. ⚠️ Rich text editor para notas

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)
- ✅ Módulo 12: Planes Diarios (14/14) ⭐ CRÍTICO

**Total documentado: 135/250+ funciones (54%)** 🎉 ¡MÁS DE LA MITAD!

**Pendientes:**
- ⏳ Módulos 14-27: 115+ funciones

---

## ✅ **MÓDULO 13: SOPs / PLANTILLAS DE ACTIVIDADES** (5/5 COMPLETO)

### 📌 FUNCIÓN 13.1 - Crear Plantilla de Actividad (SOP)

**Modelo ActivityTemplate:**
```python
class ActivityTemplate(models.Model):
    """
    SOP (Standard Operating Procedure) - Template for common activities
    Used to standardize tasks and educate team
    """
    CATEGORY_CHOICES = [
        ('PREP', 'Preparation'),
        ('COVER', 'Covering'),
        ('SAND', 'Sanding'),
        ('STAIN', 'Staining'),
        ('SEAL', 'Sealing'),
        ('PAINT', 'Painting'),
        ('CAULK', 'Caulking'),
        ('CLEANUP', 'Cleanup'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    
    # SOP Details
    time_estimate = models.DecimalField(max_digits=5, decimal_places=2, 
                                       null=True, blank=True)
    steps = models.JSONField(default=list)  # ['Step 1', 'Step 2']
    materials_list = models.JSONField(default=list)
    tools_list = models.JSONField(default=list)
    tips = models.TextField(blank=True)
    common_errors = models.TextField(blank=True)
    
    # Media
    reference_photos = models.JSONField(default=list)
    video_url = models.URLField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
```

**Vista de Creación:**
```python
@login_required
def sop_create_edit(request, template_id=None):
    """Create or edit an Activity Template (SOP)"""
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")
    
    instance = None
    if template_id:
        instance = get_object_or_404(ActivityTemplate, pk=template_id)
    
    if request.method == 'POST':
        form = ActivityTemplateForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            sop = form.save(commit=False)
            if not instance:
                sop.created_by = request.user
            sop.save()
            form.save_m2m()
            
            # Handle file uploads for reference files
            uploaded_files = request.FILES.getlist('reference_files')
            if uploaded_files:
                from .models import SOPReferenceFile
                for f in uploaded_files:
                    SOPReferenceFile.objects.create(sop=sop, file=f)
            
            messages.success(request, "SOP saved successfully!")
            return redirect('sop_library')
    else:
        form = ActivityTemplateForm(instance=instance)
    
    return render(request, 'core/sop_creator.html', {
        'form': form,
        'editing': bool(instance),
        'sop': instance,
    })
```

**Interfaz de Creación:**
```
┌────────────────────────────────────────────────────────────┐
│ 📚 CREAR NUEVO SOP (Standard Operating Procedure)         │
├────────────────────────────────────────────────────────────┤
│ Nombre: [Drywall Installation - Living Room]               │
│                                                            │
│ Categoría: [Preparation ▼]                                 │
│ • PREP (Preparación)                                       │
│ • COVER (Cubrir/Proteger)                                  │
│ • SAND (Lijar)                                             │
│ • STAIN (Teñir/Manchar)                                    │
│ • SEAL (Sellar)                                            │
│ • PAINT (Pintar)                                           │
│ • CAULK (Calafatear)                                       │
│ • CLEANUP (Limpieza)                                       │
│ • OTHER (Otro)                                             │
│                                                            │
│ Descripción General:                                       │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Instalación de drywall en paredes y cielo de sala     │ │
│ │ estándar. Incluye medición, corte, instalación y      │ │
│ │ primera capa de mud.                                  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Tiempo Estimado: [6.5] horas                               │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ 📝 PASOS DEL PROCESO:                                      │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 1. [Medir y marcar ubicación de sheets]        [×]     │ │
│ │ 2. [Cortar sheets al tamaño necesario]         [×]     │ │
│ │ 3. [Posicionar y nivelar primer sheet]         [×]     │ │
│ │ 4. [Atornillar cada 8" en studs]               [×]     │ │
│ │ 5. [Continuar con sheets adyacentes]           [×]     │ │
│ │ 6. [Aplicar joint tape en costuras]            [×]     │ │
│ │ 7. [Primera capa de mud]                       [×]     │ │
│ └────────────────────────────────────────────────────────┘ │
│ [+ Agregar Paso]                                           │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ 📦 MATERIALES NECESARIOS:                                  │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ • [Drywall sheets 4x8]                         [×]     │ │
│ │ • [Tornillos 1 1/4" para drywall]              [×]     │ │
│ │ • [Joint compound (mud)]                       [×]     │ │
│ │ • [Joint tape]                                 [×]     │ │
│ └────────────────────────────────────────────────────────┘ │
│ [+ Agregar Material]                                       │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ 🔧 HERRAMIENTAS REQUERIDAS:                                │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ • [Taladro/drill con bit para drywall]         [×]     │ │
│ │ • [T-square]                                   [×]     │ │
│ │ • [Utility knife]                              [×]     │ │
│ │ • [Drywall saw]                                [×]     │ │
│ │ • [Nivel de 4 pies]                            [×]     │ │
│ └────────────────────────────────────────────────────────┘ │
│ [+ Agregar Herramienta]                                    │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ 💡 TIPS Y MEJORES PRÁCTICAS:                               │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ • Siempre cortar sheets en área bien ventilada        │ │
│ │ • Usar dos personas para sheets de cielo              │ │
│ │ • Tornillos deben quedar ligeramente hundidos         │ │
│ │ • No sobre-apretar (puede romper papel del drywall)   │ │
│ │ • Mantener espacio de 1/4" entre sheets para mud      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ⚠️ ERRORES COMUNES A EVITAR:                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ • Tornillos muy separados (causa pandeo/sagging)      │ │
│ │ • Sheets mal alineados (problemas en mudding)         │ │
│ │ • No verificar nivel antes de atornillar              │ │
│ │ • Cortes imprecisos (desperdicio de material)         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ 📷 FOTOS DE REFERENCIA:                                    │
│ [📤 Subir fotos] (hasta 10 fotos)                          │
│ ┌─────┬─────┬─────┬─────┐                                 │
│ │ 📷  │ 📷  │ 📷  │ [+] │                                 │
│ └─────┴─────┴─────┴─────┘                                 │
│                                                            │
│ 📹 VIDEO TUTORIAL (opcional):                              │
│ URL: [https://youtube.com/watch?v=...]                     │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ 📎 ARCHIVOS DE REFERENCIA:                                 │
│ [📤 Subir PDFs, diagramas, etc.]                           │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ [✅ Guardar SOP] [📋 Preview] [❌ Cancel]                  │
└────────────────────────────────────────────────────────────┘
```

**Validaciones del Form:**
```python
class ActivityTemplateForm(forms.ModelForm):
    def clean(self):
        cleaned = super().clean()
        required = ['name', 'category', 'tips', 'materials_list', 'tools_list']
        for field in required:
            val = cleaned.get(field)
            if not val or (isinstance(val, list) and not val):
                self.add_error(field, 'This field is required.')
        return cleaned
```

**Mejoras Identificadas:**
- ✅ Modelo completo con todos los campos necesarios
- ✅ Form validation robusto
- ✅ Upload de reference files
- ⚠️ Falta: Editor visual para steps (actualmente JSON)
- ⚠️ Falta: Plantillas predefinidas por categoría
- ⚠️ Falta: Importar SOPs de biblioteca externa

---

### 📌 FUNCIÓN 13.2 - Biblioteca de SOPs (Browse & Search)

**Vista: sop_library**
```python
@login_required
def sop_library(request):
    """Browse and search Activity Templates (SOPs)"""
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")
    
    category = request.GET.get('category', '')
    search = request.GET.get('search', '')
    
    templates = ActivityTemplate.objects.filter(is_active=True)
    
    if category:
        templates = templates.filter(category=category)
    
    if search:
        templates = templates.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(tips__icontains=search)
        )
    
    templates = templates.order_by('category', 'name')
    
    return render(request, 'core/sop_library.html', {
        'templates': templates,
        'categories': ActivityTemplate.CATEGORY_CHOICES,
        'selected_category': category,
        'search_query': search,
    })
```

**Interfaz de Biblioteca:**
```
┌────────────────────────────────────────────────────────────┐
│ 📚 BIBLIOTECA DE SOPs                                      │
├────────────────────────────────────────────────────────────┤
│ [🔍 Buscar SOPs...]                          [+ Crear SOP] │
│                                                            │
│ Filtrar por Categoría: [Todas ▼]                           │
├────────────────────────────────────────────────────────────┤
│ PREP - PREPARACIÓN (12 SOPs)                               │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Drywall Installation                                   │ │
│ │ ⏱️ 6.5 hrs | 📋 7 pasos | 📦 4 materiales              │ │
│ │ Instalación de drywall en paredes y cielo...           │ │
│ │ [👁️ Ver] [✏️ Editar] [📋 Usar en Plan]                  │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Surface Preparation for Painting                       │ │
│ │ ⏱️ 3 hrs | 📋 5 pasos | 📦 6 materiales                │ │
│ │ Limpieza, lijado y preparación de superficie...        │ │
│ │ [👁️ Ver] [✏️ Editar] [📋 Usar en Plan]                  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ SAND - LIJADO (8 SOPs)                                     │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Wood Sanding - Fine Finish                             │ │
│ │ ⏱️ 2 hrs | 📋 4 pasos | 📦 3 materiales                │ │
│ │ [👁️ Ver] [✏️ Editar] [📋 Usar en Plan]                  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ PAINT - PINTURA (15 SOPs)                                  │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Interior Wall Painting - Two Coats                     │ │
│ │ ⏱️ 4 hrs | 📋 6 pasos | 📦 5 materiales                │ │
│ │ [👁️ Ver] [✏️ Editar] [📋 Usar en Plan]                  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Ver más...]                                               │
│                                                            │
│ Total: 47 SOPs activos                                     │
└────────────────────────────────────────────────────────────┘
```

**Búsqueda y Filtrado:**
```
BUSCAR: "paint"

Resultados (8):

PAINT:
• Interior Wall Painting - Two Coats
• Exterior Trim Painting
• Cabinet Painting Process

PREP:
• Surface Preparation for Painting
• Primer Application

OTHER:
• Paint Touch-ups and Corrections
```

**Mejoras Identificadas:**
- ✅ Search funcional (nombre, descripción, tips)
- ✅ Filtrado por categoría
- ✅ Vista organizada por categorías
- ⚠️ Falta: Tags adicionales para mejor búsqueda
- ⚠️ Falta: Sorting por popularidad/uso frecuente
- ⚠️ Falta: Vista de grid vs list
- ⚠️ Falta: Preview rápido sin abrir SOP completo

---

### 📌 FUNCIÓN 13.3 - Ver Detalle de SOP

**Vista Detallada:**
```
┌────────────────────────────────────────────────────────────┐
│ 📖 SOP: DRYWALL INSTALLATION                               │
│ Categoría: PREP - Preparation                              │
│ Creado por: Admin | Actualizado: Aug 20, 2025              │
├────────────────────────────────────────────────────────────┤
│ 📄 DESCRIPCIÓN:                                            │
│ Instalación de drywall en paredes y cielo de sala         │
│ estándar. Incluye medición, corte, instalación y primera   │
│ capa de mud.                                               │
│                                                            │
│ ⏱️ TIEMPO ESTIMADO: 6.5 horas                              │
├────────────────────────────────────────────────────────────┤
│ 📝 PASOS A SEGUIR:                                         │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ☐ 1. Medir y marcar ubicación de sheets               │ │
│ │      Usar T-square para marcar líneas rectas.         │ │
│ │                                                        │ │
│ │ ☐ 2. Cortar sheets al tamaño necesario                │ │
│ │      Usar utility knife, cortar en área ventilada.    │ │
│ │                                                        │ │
│ │ ☐ 3. Posicionar y nivelar primer sheet                │ │
│ │      Dos personas para sheets de cielo.               │ │
│ │                                                        │ │
│ │ ☐ 4. Atornillar cada 8 pulgadas en studs              │ │
│ │      Tornillos ligeramente hundidos, no romper papel. │ │
│ │                                                        │ │
│ │ ☐ 5. Continuar con sheets adyacentes                  │ │
│ │      Mantener 1/4" espacio para mud.                  │ │
│ │                                                        │ │
│ │ ☐ 6. Aplicar joint tape en costuras                   │ │
│ │      Centrar tape sobre costura.                      │ │
│ │                                                        │ │
│ │ ☐ 7. Primera capa de mud                              │ │
│ │      Capa delgada, dejar secar 24hrs.                 │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ 📦 MATERIALES NECESARIOS:                                  │
│ • Drywall sheets 4x8                                       │
│ • Tornillos 1 1/4" para drywall                            │
│ • Joint compound (mud)                                     │
│ • Joint tape                                               │
│                                                            │
│ 🔧 HERRAMIENTAS REQUERIDAS:                                │
│ • Taladro/drill con bit para drywall                       │
│ • T-square                                                 │
│ • Utility knife                                            │
│ • Drywall saw                                              │
│ • Nivel de 4 pies                                          │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ 💡 TIPS Y MEJORES PRÁCTICAS:                               │
│ • Siempre cortar sheets en área bien ventilada             │
│ • Usar dos personas para sheets de cielo                   │
│ • Tornillos deben quedar ligeramente hundidos              │
│ • No sobre-apretar (puede romper papel del drywall)        │
│ • Mantener espacio de 1/4" entre sheets para mud           │
│                                                            │
│ ⚠️ ERRORES COMUNES A EVITAR:                              │
│ • Tornillos muy separados (causa pandeo/sagging)           │
│ • Sheets mal alineados (problemas en mudding)              │
│ • No verificar nivel antes de atornillar                   │
│ • Cortes imprecisos (desperdicio de material)              │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ 📷 FOTOS DE REFERENCIA (8):                                │
│ ┌─────┬─────┬─────┬─────┐                                 │
│ │ 📷  │ 📷  │ 📷  │ 📷  │ [Ver galería]                   │
│ └─────┴─────┴─────┴─────┘                                 │
│                                                            │
│ 📹 VIDEO TUTORIAL:                                         │
│ [▶️ Ver en YouTube] (12:34)                                │
│ https://youtube.com/watch?v=drywall_basics                 │
│                                                            │
│ 📎 ARCHIVOS DE REFERENCIA (2):                             │
│ • drywall_measurements.pdf                                 │
│ • stud_spacing_guide.pdf                                   │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ 📊 ESTADÍSTICAS DE USO:                                    │
│ • Usado en 24 planes diarios                               │
│ • Promedio real: 7.2 hrs (vs estimado 6.5 hrs)             │
│ • Última actualización: Aug 20, 2025                       │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ [📋 Usar en Plan] [✏️ Editar] [📄 Duplicar] [🗑️ Archivar]  │
└────────────────────────────────────────────────────────────┘
```

**Uso desde Daily Plan:**
```
Cuando PM crea actividad:
1. Click "Usar SOP"
2. Selecciona de biblioteca
3. Sistema auto-llena:
   ├─ Nombre de actividad
   ├─ Descripción
   ├─ Tiempo estimado (6.5 hrs)
   ├─ Lista de materiales
   └─ Steps como checklist
4. PM ajusta si necesario
5. Empleado ve SOP completo en su dashboard
```

**Mejoras Identificadas:**
- ✅ Vista completa con todos los detalles
- ⚠️ Falta: Estadísticas de uso (tracking)
- ⚠️ Falta: Comparación estimado vs real automática
- ⚠️ Falta: Comentarios/feedback de empleados
- ⚠️ Falta: Versioning (histórico de cambios)

---

### 📌 FUNCIÓN 13.4 - Editar SOP Existente

**Proceso de Edición:**
```python
# Misma vista que crear, pero con instance
def sop_create_edit(request, template_id=None):
    instance = None
    if template_id:
        instance = get_object_or_404(ActivityTemplate, pk=template_id)
    
    if request.method == 'POST':
        form = ActivityTemplateForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            sop = form.save(commit=False)
            if not instance:
                sop.created_by = request.user
            sop.save()
            # ... upload reference files ...
```

**Interfaz de Edición:**
```
┌────────────────────────────────────────────────────────────┐
│ ✏️ EDITAR SOP: Drywall Installation                       │
├────────────────────────────────────────────────────────────┤
│ [Todos los campos pre-llenados con data existente]        │
│                                                            │
│ Nombre: [Drywall Installation - Living Room]               │
│ Categoría: [Preparation ▼]                                 │
│                                                            │
│ Descripción: [...]                                         │
│                                                            │
│ Pasos:                                                     │
│ 1. [Medir y marcar ubicación de sheets]        [×]         │
│ 2. [Cortar sheets al tamaño necesario]         [×]         │
│ ...                                                        │
│                                                            │
│ ⚠️ ADVERTENCIA:                                            │
│ Este SOP está siendo usado en 3 planes activos.            │
│ Los cambios afectarán planes futuros, no los existentes.   │
│                                                            │
│ [💾 Guardar Cambios] [❌ Cancel]                           │
│                                                            │
│ O crear nueva versión:                                     │
│ [📄 Guardar como Nueva Versión]                            │
└────────────────────────────────────────────────────────────┘
```

**Consideraciones:**
```
EDITAR SOP EN USO:

Opción A: Update in place
├─ Planes futuros usan versión nueva
├─ Planes existentes quedan con versión vieja (snapshot)
└─ Más simple, pero puede causar inconsistencias

Opción B: Versioning
├─ Crear nueva versión
├─ Mantener historial
├─ Planes existentes apuntan a versión específica
└─ Más complejo, pero más seguro

ACTUALMENTE: Sistema usa Opción A (update in place)
```

**Mejoras Identificadas:**
- ✅ Edición funcional
- ⚠️ Falta: Sistema de versionado
- ⚠️ Falta: Advertencia si SOP está en uso
- ⚠️ Falta: Diff viewer (comparar versiones)
- ⚠️ Falta: Rollback a versión anterior

---

### 📌 FUNCIÓN 13.5 - Archivar/Desactivar SOPs

**Campo is_active:**
```python
is_active = models.BooleanField(
    default=True, 
    help_text="Hide inactive templates"
)
```

**Uso:**
```
ARCHIVAR SOP (marcar como inactivo):

Cuándo archivar:
├─ SOP obsoleto (ya no se usa ese proceso)
├─ Reemplazado por SOP mejor
├─ Proceso ya no es parte del negocio
└─ SOP experimental que no funcionó

Efectos:
├─ No aparece en biblioteca
├─ No se puede seleccionar en nuevos planes
├─ Planes existentes siguen funcionando
└─ Admin puede reactivar si necesario
```

**Interfaz:**
```
┌────────────────────────────────────────────────────────────┐
│ 📖 SOP: Old Drywall Process (INACTIVO)                     │
├────────────────────────────────────────────────────────────┤
│ ⚠️ Este SOP está INACTIVO                                 │
│ No aparecerá en la biblioteca ni en búsquedas.             │
│                                                            │
│ Razón: Reemplazado por "Drywall Installation v2"           │
│                                                            │
│ [✅ Reactivar] [🗑️ Eliminar Permanentemente]              │
└────────────────────────────────────────────────────────────┘

En biblioteca:
[✓] Mostrar SOPs inactivos (solo Admin)
```

**Modelo SOPReferenceFile:**
```python
class SOPReferenceFile(models.Model):
    """Reference files (photos, PDFs, etc.) attached to SOPs"""
    sop = models.ForeignKey(
        ActivityTemplate,
        on_delete=models.CASCADE,
        related_name='reference_files'
    )
    file = models.FileField(upload_to='sop_references/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def filename(self):
        return self.file.name.split('/')[-1]
```

**Mejoras Identificadas:**
- ✅ Sistema is_active funcional
- ✅ Reference files upload implementado
- ⚠️ Falta: Razón de desactivación (audit trail)
- ⚠️ Falta: Soft delete vs hard delete
- ⚠️ Falta: Reporte de SOPs no usados (sugerir archivar)

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 13**

### Mejoras CRÍTICAS:
1. 🔴 **Sistema de Versionado**
   - Mantener historial de cambios
   - Planes apuntan a versión específica
   - Rollback capability
   - Diff viewer

2. 🔴 **Tracking de Uso y Analytics**
   - ¿Qué SOPs se usan más?
   - Estimado vs real (mejora continua)
   - SOPs que nunca se usan (archivar)
   - Performance metrics

### Mejoras Importantes:
3. ⚠️ Editor visual para steps (drag & drop)
4. ⚠️ Plantillas predefinidas por categoría
5. ⚠️ Import/Export de SOPs
6. ⚠️ Tags adicionales para búsqueda
7. ⚠️ Sorting por popularidad
8. ⚠️ Vista de grid vs list
9. ⚠️ Preview rápido (modal)
10. ⚠️ Comentarios/feedback de empleados
11. ⚠️ Advertencia si SOP está en uso activo
12. ⚠️ Razón de desactivación (audit)
13. ⚠️ Reporte de SOPs no usados

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)
- ✅ Módulo 12: Planes Diarios (14/14) ⭐ CRÍTICO
- ✅ Módulo 13: SOPs/Plantillas (5/5)

**Total documentado: 140/250+ funciones (56%)** 🎉

**Pendientes:**
- ⏳ Módulos 15-27: 112+ funciones

---

## ✅ **MÓDULO 14: MINUTAS / TIMELINE DE PROYECTO** (3/3 COMPLETO)

### 📌 FUNCIÓN 14.1 - Crear Minuta de Proyecto

**Modelo ProjectMinute:**
```python
class ProjectMinute(models.Model):
    """
    Timeline de decisiones, llamadas, aprobaciones y cambios del proyecto.
    Para Admin y Clientes mantener registro histórico de comunicaciones.
    """
    EVENT_TYPE_CHOICES = [
        ('decision', 'Decisión'),
        ('call', 'Llamada'),
        ('email', 'Correo'),
        ('meeting', 'Reunión'),
        ('approval', 'Aprobación'),
        ('change', 'Cambio/Modificación'),
        ('issue', 'Problema'),
        ('milestone', 'Hito'),
        ('note', 'Nota'),
    ]
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE, 
                                related_name='minutes')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, 
                                  default='note')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Quién y cuándo
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    event_date = models.DateTimeField(
        help_text="Fecha/hora del evento real (puede ser diferente de created_at)"
    )
    
    # Participantes (opcional)
    participants = models.TextField(
        blank=True, 
        help_text="Nombres de participantes en llamada/reunión"
    )
    
    # Archivos adjuntos
    attachment = models.FileField(upload_to='minutes/%Y/%m/', blank=True, null=True)
    
    # Visibilidad
    visible_to_client = models.BooleanField(
        default=True, 
        help_text="¿El cliente puede ver esta minuta?"
    )
```

**Propósito:**
```
REGISTRO HISTÓRICO DE COMUNICACIONES:
├─ Decisiones importantes del proyecto
├─ Llamadas con cliente
├─ Aprobaciones de cambios
├─ Hitos alcanzados
├─ Problemas encontrados
└─ Documentación para referencia futura

BENEFICIOS:
├─ Transparencia con cliente
├─ Protección legal (registro de acuerdos)
├─ Memoria institucional
├─ Tracking de decisiones
└─ Audit trail
```

**Vista de Creación:**
```python
@login_required
def project_minute_create(request, project_id):
    """Crear nueva minuta"""
    project = get_object_or_404(Project, id=project_id)
    
    # Solo admin/staff pueden crear minutas
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "No tienes permisos para crear minutas.")
        return redirect('project_minutes_list', project_id=project.id)
    
    from core.models import ProjectMinute
    
    if request.method == 'POST':
        event_type = request.POST.get('event_type')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        event_date_str = request.POST.get('event_date')
        participants = request.POST.get('participants', '')
        visible_to_client = request.POST.get('visible_to_client') == 'on'
        attachment = request.FILES.get('attachment')
        
        if not title or not event_date_str:
            messages.error(request, "Título y fecha son requeridos.")
        else:
            try:
                event_date = timezone.datetime.fromisoformat(event_date_str)
            except Exception:
                event_date = timezone.now()
            
            ProjectMinute.objects.create(
                project=project,
                event_type=event_type,
                title=title,
                description=description,
                event_date=event_date,
                participants=participants,
                attachment=attachment,
                visible_to_client=visible_to_client,
                created_by=request.user
            )
            messages.success(request, "Minuta creada exitosamente.")
            return redirect('project_minutes_list', project_id=project.id)
```

**Interfaz de Creación:**
```
┌────────────────────────────────────────────────────────────┐
│ 📝 NUEVA MINUTA - Villa Moderna                            │
├────────────────────────────────────────────────────────────┤
│ Tipo de Evento: [Decisión ▼]                               │
│ • Decisión                                                 │
│ • Llamada                                                  │
│ • Correo                                                   │
│ • Reunión                                                  │
│ • Aprobación                                               │
│ • Cambio/Modificación                                      │
│ • Problema                                                 │
│ • Hito                                                     │
│ • Nota                                                     │
│                                                            │
│ Título: [Cliente aprobó cambio de color en sala]           │
│                                                            │
│ Fecha/Hora del Evento: [2025-08-25 14:30] 📅⏰             │
│                                                            │
│ Descripción:                                               │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Cliente revisó muestras de color y decidió cambiar    │ │
│ │ de "Warm Beige" a "Cool Gray" para la sala principal. │ │
│ │ Confirmó que está dispuesto a absorber costo          │ │
│ │ adicional de repintar.                                │ │
│ │                                                        │ │
│ │ Próximos pasos:                                        │ │
│ │ - Ordenar nuevo paint (Cool Gray)                     │ │
│ │ - Reprogramar pintor para próxima semana              │ │
│ │ - Crear change order por $450                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Participantes (opcional):                                  │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Juan Pérez (Admin), María Cliente, Pedro Diseñador    │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Archivo Adjunto (opcional):                                │
│ [📎 Subir archivo] (fotos, PDFs, emails, etc.)             │
│                                                            │
│ [✓] Visible para el cliente                                │
│ (Desmarcar si es nota interna que cliente no debe ver)     │
│                                                            │
│ [💾 Crear Minuta] [❌ Cancelar]                            │
└────────────────────────────────────────────────────────────┘
```

**Ejemplos de Uso:**
```
TIPO: DECISIÓN
Título: "Cliente eligió acabado mate para gabinetes"
Descripción: "Después de ver muestras..."
Visible: ✓ Sí

TIPO: APROBACIÓN
Título: "Ciudad aprobó inspección de electrical rough-in"
Descripción: "Inspector visitó Aug 23, todo pasó..."
Adjunto: inspection_report.pdf
Visible: ✓ Sí

TIPO: PROBLEMA
Título: "Detectado leak en tubería principal"
Descripción: "Plomero encontró leak durante instalación..."
Visible: ✗ No (nota interna, no alarmar cliente todavía)

TIPO: HITO
Título: "Completado 50% del proyecto"
Descripción: "Celebrando medio camino..."
Visible: ✓ Sí

TIPO: LLAMADA
Título: "Llamada con cliente sobre delay de materiales"
Participantes: "Admin, Cliente, Supplier Rep"
Descripción: "Discutimos opciones para acelerar entrega..."
Visible: ✓ Sí
```

**Mejoras Identificadas:**
- ✅ Modelo completo con tipos de evento
- ✅ Control de visibilidad cliente
- ✅ Attachments support
- ⚠️ Falta: Templates de minutas por tipo
- ⚠️ Falta: Notificaciones automáticas a cliente
- ⚠️ Falta: Vinculación con Change Orders, Tasks, etc.
- ⚠️ Falta: Firma digital del cliente

---

### 📌 FUNCIÓN 14.2 - Timeline de Proyecto (Lista de Minutas)

**Vista: project_minutes_list**
```python
@login_required
def project_minutes_list(request, project_id):
    """Lista todas las minutas de un proyecto (timeline)"""
    project = get_object_or_404(Project, id=project_id)
    
    # Admin ve todo, Cliente solo ve lo marcado como visible
    from core.models import ProjectMinute
    if request.user.is_staff or request.user.is_superuser:
        minutes = ProjectMinute.objects.filter(project=project)
    else:
        minutes = ProjectMinute.objects.filter(
            project=project, 
            visible_to_client=True
        )
    
    minutes = minutes.select_related('created_by').order_by('-event_date')
    
    # Filtros
    event_type = request.GET.get('type')
    if event_type:
        minutes = minutes.filter(event_type=event_type)
    
    return render(request, 'core/project_minutes_list.html', {
        'project': project,
        'minutes': minutes,
        'event_types': ProjectMinute.EVENT_TYPE_CHOICES,
    })
```

**Interfaz de Timeline:**
```
┌────────────────────────────────────────────────────────────┐
│ 📅 TIMELINE - VILLA MODERNA                                │
│ [+ Nueva Minuta]                                           │
├────────────────────────────────────────────────────────────┤
│ Filtrar: [Todos ▼] [🔍 Buscar...]                          │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 📌 AGOSTO 2025                                             │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🎯 HITO | Aug 25, 2025 2:30 PM                         │ │
│ │ Completado 50% del proyecto                            │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Celebrando medio camino. Todas las paredes de drywall │ │
│ │ completadas, electrical rough-in aprobado.             │ │
│ │                                                        │ │
│ │ 👤 Por: Admin | 👁️ Visible para cliente               │ │
│ │ [Ver Detalles]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✅ APROBACIÓN | Aug 23, 2025 10:15 AM                  │ │
│ │ Ciudad aprobó inspección electrical rough-in           │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Inspector visitó Aug 23, todo pasó sin problemas.     │ │
│ │ Podemos proceder con drywall.                         │ │
│ │                                                        │ │
│ │ 📎 inspection_report.pdf                               │ │
│ │ 👤 Por: Admin | 👁️ Visible para cliente               │ │
│ │ [Ver Detalles]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 💬 DECISIÓN | Aug 20, 2025 2:30 PM                     │ │
│ │ Cliente aprobó cambio de color en sala                 │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Cliente revisó muestras y decidió cambiar de          │ │
│ │ "Warm Beige" a "Cool Gray"...                         │ │
│ │                                                        │ │
│ │ 👥 Participantes: Admin, María Cliente, Pedro         │ │
│ │ 👤 Por: Admin | 👁️ Visible para cliente               │ │
│ │ [Ver Detalles]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📞 LLAMADA | Aug 18, 2025 11:00 AM                     │ │
│ │ Discusión sobre delay de materiales                    │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Supplier confirmó que materiales llegarán Aug 22...   │ │
│ │                                                        │ │
│ │ 👥 Participantes: Admin, Cliente, Supplier            │ │
│ │ 👤 Por: Admin | 👁️ Visible para cliente               │ │
│ │ [Ver Detalles]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ 📌 JULIO 2025                                              │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🎯 HITO | Jul 30, 2025                                 │ │
│ │ Inicio oficial del proyecto                            │ │
│ │ ...                                                    │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Cargar más...]                                            │
└────────────────────────────────────────────────────────────┘
```

**Vista de Cliente:**
```
CLIENTE VE:
├─ Solo minutas con visible_to_client=True
├─ Timeline cronológico
├─ Decisiones que afectan proyecto
├─ Aprobaciones oficiales
├─ Hitos alcanzados
└─ Comunicaciones importantes

CLIENTE NO VE:
├─ Notas internas (visible_to_client=False)
├─ Problemas no resueltos
├─ Discusiones internas del equipo
└─ Information sensitive
```

**Filtrado por Tipo:**
```
[Filtrar: Decisiones ▼]

Resultados:
• Cliente aprobó cambio de color en sala (Aug 20)
• Selección de fixtures para baño (Aug 10)
• Cambio de layout en cocina (Jul 28)
• Aprobación de presupuesto inicial (Jul 15)

[Filtrar: Hitos ▼]

Resultados:
• Completado 50% del proyecto (Aug 25)
• Rough-in completado (Aug 15)
• Demolición completada (Aug 5)
• Inicio oficial del proyecto (Jul 30)
```

**Mejoras Identificadas:**
- ✅ Timeline funcional con filtros
- ✅ Control de visibilidad por rol
- ✅ Ordenado cronológicamente
- ⚠️ Falta: Búsqueda de texto completo
- ⚠️ Falta: Vista de calendario
- ⚠️ Falta: Export a PDF (reporte del proyecto)
- ⚠️ Falta: Agrupación por mes mejorada

---

### 📌 FUNCIÓN 14.3 - Ver Detalle de Minuta

**Vista: project_minute_detail**
```python
@login_required
def project_minute_detail(request, minute_id):
    """Ver detalles de una minuta"""
    from core.models import ProjectMinute
    minute = get_object_or_404(ProjectMinute, id=minute_id)
    
    # Verificar permisos
    if not (request.user.is_staff or 
            request.user.is_superuser or 
            minute.visible_to_client):
        messages.error(request, "No tienes permisos para ver esta minuta.")
        return redirect('project_minutes_list', project_id=minute.project.id)
    
    return render(request, 'core/project_minute_detail.html', {
        'minute': minute,
    })
```

**Interfaz de Detalle:**
```
┌────────────────────────────────────────────────────────────┐
│ 📝 MINUTA: CLIENTE APROBÓ CAMBIO DE COLOR EN SALA         │
├────────────────────────────────────────────────────────────┤
│ Proyecto: Villa Moderna                                    │
│ Tipo: 💬 Decisión                                          │
│ Fecha del Evento: Aug 20, 2025 - 2:30 PM                   │
│ Registrado por: Admin (Juan Pérez)                         │
│ Creado: Aug 20, 2025 - 3:15 PM                             │
├────────────────────────────────────────────────────────────┤
│ 📄 DESCRIPCIÓN COMPLETA:                                   │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Cliente revisó las muestras de color junto con el     │ │
│ │ diseñador y decidió cambiar el color de la sala       │ │
│ │ principal de "Warm Beige" (Sherwin Williams SW 7537)  │ │
│ │ a "Cool Gray" (Sherwin Williams SW 7047).             │ │
│ │                                                        │ │
│ │ Razón del cambio:                                      │ │
│ │ Cliente prefiere un tono más neutral que combine      │ │
│ │ mejor con los muebles modernos que planea comprar.    │ │
│ │                                                        │ │
│ │ Impacto:                                               │ │
│ │ - Requiere repintar área ya pintada (200 sq ft)       │ │
│ │ - Costo adicional: $450 (material + labor)            │ │
│ │ - Delay estimado: 2 días                               │ │
│ │                                                        │ │
│ │ Cliente confirmó que está dispuesto a absorber el     │ │
│ │ costo adicional y acepta el delay.                    │ │
│ │                                                        │ │
│ │ PRÓXIMOS PASOS:                                        │ │
│ │ 1. Crear Change Order #003 por $450                   │ │
│ │ 2. Ordenar nuevo paint (Cool Gray)                    │ │
│ │ 3. Reprogramar pintor para próxima semana             │ │
│ │ 4. Actualizar schedule                                │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ 👥 PARTICIPANTES:                                          │
│ • Juan Pérez (Admin/PM)                                    │
│ • María González (Cliente)                                 │
│ • Pedro Martínez (Diseñador)                               │
│                                                            │
│ 📎 ARCHIVOS ADJUNTOS:                                      │
│ • color_samples_comparison.jpg (245 KB)                    │
│ • client_approval_email.pdf (128 KB)                       │
│                                                            │
│ 👁️ VISIBILIDAD: Visible para el cliente                   │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ 🔗 ITEMS RELACIONADOS:                                     │
│ • Change Order #003 - Color Change Living Room ($450)      │
│ • Task: Repaint Living Room                                │
│ • Schedule: Painting - Living Room (actualizado)           │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ [✏️ Editar] [🗑️ Eliminar] [🔙 Volver al Timeline]         │
└────────────────────────────────────────────────────────────┘
```

**Uso en Client Portal:**
```
Cliente accede a su portal:
├─ Ve timeline de su proyecto
├─ Solo ve minutas marcadas como visibles
├─ Puede ver detalles completos
├─ Puede descargar attachments
└─ Puede comentar (futuro)

Transparencia:
✅ Cliente sabe qué está pasando
✅ Decisiones documentadas
✅ Expectativas claras
✅ Confianza mejorada
```

**Mejoras Identificadas:**
- ✅ Vista detallada completa
- ✅ Verificación de permisos
- ✅ Attachments accesibles
- ⚠️ Falta: Vinculación automática con Change Orders/Tasks
- ⚠️ Falta: Sistema de comentarios
- ⚠️ Falta: Edición inline (actualmente no implementada)
- ⚠️ Falta: Historial de ediciones
- ⚠️ Falta: Email notification automática al crear
- ⚠️ Falta: PDF export de minuta individual

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 14**

### Mejoras CRÍTICAS:
1. 🔴 **Vinculación Automática con Otros Módulos**
   - Link minutas con Change Orders
   - Link minutas con Tasks
   - Link minutas con Schedule items
   - Auto-create minute cuando se aprueba CO

2. 🔴 **Sistema de Notificaciones**
   - Email automático a cliente cuando nueva minuta
   - Notificar participantes mencionados
   - Digest semanal de minutas

### Mejoras Importantes:
3. ⚠️ Templates de minutas por tipo de evento
4. ⚠️ Firma digital del cliente en minutas
5. ⚠️ Búsqueda de texto completo
6. ⚠️ Vista de calendario
7. ⚠️ Export timeline completo a PDF
8. ⚠️ Sistema de comentarios en minutas
9. ⚠️ Edición de minutas (con historial)
10. ⚠️ Attachments múltiples mejorado
11. ⚠️ Rich text editor para descripción
12. ⚠️ Tags/categorías adicionales
13. ⚠️ Recordatorios de follow-up actions
14. ⚠️ Integration con email (importar emails como minutas)

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)
- ✅ Módulo 12: Planes Diarios (14/14) ⭐ CRÍTICO
- ✅ Módulo 13: SOPs/Plantillas (5/5)
- ✅ Módulo 14: Minutas/Timeline (3/3)

**Total documentado: 143/250+ funciones (57%)** 🎉

**Pendientes:**
- ⏳ Módulos 16-27: 106+ funciones

---

## ✅ **MÓDULO 15: RFIs, ISSUES & RISKS** (6/6 COMPLETO)

### 📌 FUNCIÓN 15.1 - Crear RFI (Request for Information)

**Modelo RFI:**
```python
class RFI(models.Model):
    """
    Request for Information - Preguntas que requieren clarificación
    Durante construcción surgen dudas sobre especificaciones, diseño, etc.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, 
                                related_name='rfis')
    number = models.PositiveIntegerField()  # Auto-incrementa por proyecto
    question = models.TextField()
    answer = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('answered', 'Answered'),
            ('closed', 'Closed')
        ],
        default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('project', 'number')
        ordering = ['-created_at']
```

**Propósito:**
```
RFI = REQUEST FOR INFORMATION

Uso típico:
├─ Especificaciones no claras en planos
├─ Dudas sobre materiales a usar
├─ Consultas sobre cambios del cliente
├─ Preguntas técnicas durante construcción
└─ Clarificaciones antes de proceder

Beneficios:
├─ Documentación de decisiones
├─ Evita asumir incorrectamente
├─ Protección legal (registro de preguntas)
├─ Comunicación estructurada
└─ Tracking de respuestas
```

**Vista de Creación:**
```python
@login_required
def rfi_list_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = RFIForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        # Auto-incrementa número
        number = (project.rfis.aggregate(m=models.Max('number'))['m'] or 0) + 1
        rfi = form.save(commit=False)
        rfi.project = project
        rfi.number = number
        rfi.save()
        return redirect('rfi_list', project_id=project.id)
    
    rfis = project.rfis.all()
    return render(request, 'core/rfi_list.html', {
        'project': project,
        'rfis': rfis,
        'form': form
    })
```

**Interfaz:**
```
┌────────────────────────────────────────────────────────────┐
│ ❓ RFIs - VILLA MODERNA                                    │
│ [+ Nuevo RFI]                                              │
├────────────────────────────────────────────────────────────┤
│ CREAR NUEVO RFI:                                           │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Pregunta/Consulta:                                     │ │
│ │ ┌──────────────────────────────────────────────────────┐│
│ │ │ Los planos muestran "hardwood flooring" en sala,   ││
│ │ │ pero el cliente mencionó que quiere "engineered    ││
│ │ │ hardwood". ¿Cuál procedemos a instalar?            ││
│ │ │ ¿Hay diferencia en presupuesto?                    ││
│ │ └──────────────────────────────────────────────────────┘│
│ │                                                        │ │
│ │ [Crear RFI]                                            │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ RFIS EXISTENTES:                                           │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟢 RFI #003 | OPEN                                     │ │
│ │ Clarificación sobre tipo de hardwood flooring          │ │
│ │ Creado: Aug 25, 2025 9:15 AM                           │ │
│ │ [Ver] [Responder]                                      │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✅ RFI #002 | ANSWERED                                 │ │
│ │ ¿Qué color de grout usar en baño?                      │ │
│ │ Pregunta: Aug 23 | Respondido: Aug 24                  │ │
│ │ [Ver Respuesta]                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔒 RFI #001 | CLOSED                                   │ │
│ │ Especificaciones de electrical outlets                 │ │
│ │ [Ver Detalles]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Auto-incremento de número por proyecto
- ✅ Estados: Open, Answered, Closed
- ⚠️ Falta: Asignar RFI a persona específica
- ⚠️ Falta: Deadline para respuesta
- ⚠️ Falta: Priority levels
- ⚠️ Falta: Attachments (fotos, planos)
- ⚠️ Falta: Email notification automática

---

### 📌 FUNCIÓN 15.2 - Responder RFI

**Vista de Respuesta:**
```python
@login_required
def rfi_answer_view(request, rfi_id):
    rfi = get_object_or_404(RFI, pk=rfi_id)
    form = RFIAnswerForm(request.POST or None, instance=rfi)
    
    if request.method == 'POST' and form.is_valid():
        ans = form.save(commit=False)
        if ans.answer and ans.status == 'open':
            ans.status = 'answered'
            ans.answered_at = timezone.now()
        ans.save()
        return redirect('rfi_list', project_id=rfi.project_id)
    
    return render(request, 'core/rfi_answer.html', {
        'rfi': rfi,
        'form': form
    })
```

**Interfaz de Respuesta:**
```
┌────────────────────────────────────────────────────────────┐
│ ❓ RESPONDER RFI #003                                      │
│ Proyecto: Villa Moderna                                    │
├────────────────────────────────────────────────────────────┤
│ PREGUNTA:                                                  │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Los planos muestran "hardwood flooring" en sala,       │ │
│ │ pero el cliente mencionó que quiere "engineered        │ │
│ │ hardwood". ¿Cuál procedemos a instalar?                │ │
│ │ ¿Hay diferencia en presupuesto?                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Creado: Aug 25, 2025 9:15 AM                               │
│ Status: 🟢 OPEN                                            │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ RESPUESTA:                                                 │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Hablé con el cliente. Confirma que quiere engineered  │ │
│ │ hardwood, no solid hardwood.                           │ │
│ │                                                        │ │
│ │ Especificaciones:                                      │ │
│ │ - Producto: Bruce Engineered Oak 3/8" x 5"            │ │
│ │ - Color: Natural                                       │ │
│ │ - Finish: Low-gloss polyurethane                       │ │
│ │                                                        │ │
│ │ Impacto en presupuesto:                                │ │
│ │ Engineered es $2.50/sqft vs solid $4.00/sqft           │ │
│ │ AHORRO: $375 en 250 sqft                               │ │
│ │                                                        │ │
│ │ Proceder con engineered hardwood según especificado.   │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Status: [Answered ▼]                                       │
│ • Open                                                     │
│ • Answered ✓                                               │
│ • Closed                                                   │
│                                                            │
│ [💾 Guardar Respuesta] [❌ Cancel]                         │
└────────────────────────────────────────────────────────────┘
```

**Workflow de RFI:**
```
1. PM/Employee crea RFI (Status: OPEN)
   └─> Notifica a Admin y/o Cliente

2. Admin/Cliente responde
   └─> Status: ANSWERED
   └─> answered_at timestamp

3. PM confirma que clarificación es suficiente
   └─> Status: CLOSED
   └─> Trabajo procede según respuesta

Estado OPEN = Bloqueando trabajo
Estado ANSWERED = Puede proceder
Estado CLOSED = Completamente resuelto
```

**Mejoras Identificadas:**
- ✅ Form de respuesta funcional
- ✅ Auto-update status a ANSWERED
- ✅ Timestamp de respuesta
- ⚠️ Falta: Notificación al creador del RFI
- ⚠️ Falta: Threading (múltiples idas y vueltas)
- ⚠️ Falta: Vincular con Change Orders si aplica

---

### 📌 FUNCIÓN 15.3 - Crear Issue (Problema)

**Modelo Issue:**
```python
class Issue(models.Model):
    """
    Problemas encontrados durante construcción
    Tracking de issues hasta resolución
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, 
                                related_name='issues')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High')
        ],
        default='medium'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved')
        ],
        default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
```

**Propósito:**
```
ISSUES = PROBLEMAS/DEFECTOS

Tipos de Issues:
├─ Defectos de construcción
├─ Materiales defectuosos
├─ Trabajo mal ejecutado
├─ Problemas estructurales
├─ Safety concerns
└─ Cualquier problema que requiere fix

Severidad:
├─ LOW: Cosmético, puede esperar
├─ MEDIUM: Debe arreglarse pronto
└─ HIGH: Crítico, bloquea progreso
```

**Vista de Creación:**
```python
@login_required
def issue_list_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = IssueForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        issue = form.save(commit=False)
        issue.project = project
        issue.save()
        return redirect('issue_list', project_id=project.id)
    
    issues = project.issues.all()
    return render(request, 'core/issue_list.html', {
        'project': project,
        'issues': issues,
        'form': form
    })
```

**Interfaz:**
```
┌────────────────────────────────────────────────────────────┐
│ ⚠️ ISSUES - VILLA MODERNA                                  │
│ [+ Reportar Issue]                                         │
├────────────────────────────────────────────────────────────┤
│ FILTROS: [Todos ▼] [Alta Severidad ▼] [Open ▼]            │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 HIGH | IN PROGRESS                                  │ │
│ │ Leak detectado en tubería principal                    │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Plomero encontró leak durante instalación de kitchen  │ │
│ │ sink. Requiere reemplazar sección de 6 pies.          │ │
│ │                                                        │ │
│ │ Reportado: Aug 25, 9:00 AM                             │ │
│ │ Asignado a: Pedro (Plomero)                            │ │
│ │ [Ver Detalles] [Marcar Resuelto]                       │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟡 MEDIUM | OPEN                                       │ │
│ │ Drywall tape visible en esquina                        │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Necesita capa adicional de mud y lijado.              │ │
│ │                                                        │ │
│ │ Reportado: Aug 24, 3:00 PM                             │ │
│ │ [Asignar] [Marcar en Progreso]                         │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✅ LOW | RESOLVED                                      │ │
│ │ Pintura con pequeño imperfecto                         │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Touch-up aplicado y aprobado.                          │ │
│ │                                                        │ │
│ │ Reportado: Aug 20 | Resuelto: Aug 22                   │ │
│ │ [Ver Detalles]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Severidad levels (low, medium, high)
- ✅ Estados de workflow
- ⚠️ Falta: Asignación a empleado específico
- ⚠️ Falta: Fotos del issue
- ⚠️ Falta: Due date para resolución
- ⚠️ Falta: Cost impact tracking
- ⚠️ Falta: Vinculación con Tasks

---

### 📌 FUNCIÓN 15.4 - Tracking de Issues

**Dashboard de Issues:**
```
┌────────────────────────────────────────────────────────────┐
│ ⚠️ DASHBOARD DE ISSUES - TODOS LOS PROYECTOS              │
├────────────────────────────────────────────────────────────┤
│ RESUMEN:                                                   │
│ 🔴 High Severity: 3 open                                   │
│ 🟡 Medium Severity: 8 open                                 │
│ 🟢 Low Severity: 12 open                                   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Total: 23 open issues                                      │
│                                                            │
│ ISSUES CRÍTICOS (HIGH):                                    │
│ 1. Villa Moderna - Leak en tubería (IN PROGRESS)           │
│ 2. Casa Norte - Problema estructural (OPEN) ⚠️             │
│ 3. Office Complex - Electrical hazard (IN PROGRESS)        │
│                                                            │
│ [Ver Todos los Issues] [Reporte de Issues]                 │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ⚠️ Falta: Dashboard de issues global
- ⚠️ Falta: Alertas de issues críticos sin resolver
- ⚠️ Falta: SLA tracking (tiempo de resolución)
- ⚠️ Falta: Estadísticas (issues por proyecto, por tipo)

---

### 📌 FUNCIÓN 15.5 - Crear Risk (Riesgo)

**Modelo Risk:**
```python
class Risk(models.Model):
    """
    Risk Management - Identificar y mitigar riesgos del proyecto
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, 
                                related_name='risks')
    title = models.CharField(max_length=150)
    probability = models.PositiveSmallIntegerField(
        help_text="1-100"
    )  # % de que ocurra
    impact = models.PositiveSmallIntegerField(
        help_text="1-100"
    )  # Severidad si ocurre
    mitigation = models.TextField(
        blank=True,
        help_text="Plan para mitigar el riesgo"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('identified', 'Identified'),
            ('mitigating', 'Mitigating'),
            ('realized', 'Realized'),
            ('closed', 'Closed')
        ],
        default='identified'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def score(self):
        """Risk Score = Probability × Impact"""
        return (self.probability or 0) * (self.impact or 0)
```

**Propósito:**
```
RISK MANAGEMENT:

Identificar riesgos ANTES de que ocurran:
├─ Weather delays
├─ Material shortages
├─ Labor availability
├─ Budget overruns
├─ Scope creep
├─ Permitting delays
└─ Client indecision

Risk Score = Probability × Impact
├─ Score > 5000: CRÍTICO
├─ Score 2000-5000: ALTO
├─ Score 500-2000: MEDIO
└─ Score < 500: BAJO
```

**Vista de Creación:**
```python
@login_required
def risk_list_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = RiskForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        risk = form.save(commit=False)
        risk.project = project
        risk.save()
        return redirect('risk_list', project_id=project.id)
    
    risks = project.risks.all()
    return render(request, 'core/risk_list.html', {
        'project': project,
        'risks': risks,
        'form': form
    })
```

**Interfaz:**
```
┌────────────────────────────────────────────────────────────┐
│ 🎲 RISK REGISTER - VILLA MODERNA                           │
│ [+ Identificar Nuevo Riesgo]                               │
├────────────────────────────────────────────────────────────┤
│ CREAR NUEVO RIESGO:                                        │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Título: [Delay en entrega de custom cabinets]          │ │
│ │                                                        │ │
│ │ Probabilidad (%): [60] ███████░░░ 60%                  │ │
│ │ (¿Qué tan probable es que ocurra?)                     │ │
│ │                                                        │ │
│ │ Impacto (1-100): [80] ████████░░ 80                    │ │
│ │ (¿Qué tan grave si ocurre?)                            │ │
│ │                                                        │ │
│ │ Risk Score: 4,800 🔴 ALTO                              │ │
│ │                                                        │ │
│ │ Plan de Mitigación:                                    │ │
│ │ ┌──────────────────────────────────────────────────────┐│
│ │ │ 1. Ordenar cabinets con 2 semanas de buffer        ││
│ │ │ 2. Identificar proveedor alternativo               ││
│ │ │ 3. Mantener contacto semanal con fabricante        ││
│ │ │ 4. Tener plan B con stock cabinets si necesario    ││
│ │ └──────────────────────────────────────────────────────┘│
│ │                                                        │ │
│ │ [Crear Riesgo]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ RIESGOS IDENTIFICADOS:                                     │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 SCORE: 4,800 | MITIGATING                           │ │
│ │ Delay en entrega de custom cabinets                    │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Prob: 60% | Impact: 80                                 │ │
│ │ Mitigación: Ordenar con 2 semanas de buffer...        │ │
│ │ [Ver Plan] [Actualizar Status]                         │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟡 SCORE: 1,500 | IDENTIFIED                           │ │
│ │ Posible weather delay durante exterior painting        │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Prob: 30% | Impact: 50                                 │ │
│ │ Mitigación: Programar pintura en temporada seca...    │ │
│ │ [Iniciar Mitigación]                                   │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✅ SCORE: 2,400 | CLOSED                               │ │
│ │ Budget overrun en electrical work                      │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Prob: 40% | Impact: 60                                 │ │
│ │ REALIZADO: No ocurrió, trabajo completado en budget.  │ │
│ │ [Ver Detalles]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Risk Matrix:**
```
IMPACT ↑
100 │ 🟡  🟡  🔴  🔴  🔴
 80 │ 🟡  🟡  🟡  🔴  🔴
 60 │ 🟢  🟡  🟡  🟡  🔴
 40 │ 🟢  🟢  🟡  🟡  🟡
 20 │ 🟢  🟢  🟢  🟡  🟡
  0 └─────────────────→ PROBABILITY
    0   20  40  60  80  100

🔴 = High Risk (Score > 5000)
🟡 = Medium Risk (Score 500-5000)
🟢 = Low Risk (Score < 500)
```

**Mejoras Identificadas:**
- ✅ Risk scoring funcional
- ✅ Estados de lifecycle
- ⚠️ Falta: Risk matrix visualization
- ⚠️ Falta: Asignación de owner
- ⚠️ Falta: Review dates
- ⚠️ Falta: Actual cost si risk se realiza
- ⚠️ Falta: Templates de risks comunes

---

### 📌 FUNCIÓN 15.6 - Risk Management Dashboard

**Dashboard de Riesgos:**
```
┌────────────────────────────────────────────────────────────┐
│ 🎲 RISK DASHBOARD - TODOS LOS PROYECTOS                   │
├────────────────────────────────────────────────────────────┤
│ TOP 5 RIESGOS MÁS CRÍTICOS:                                │
│                                                            │
│ 1. 🔴 Office Complex - Material shortage (Score: 6,400)    │
│    Prob: 80% | Impact: 80 | Status: MITIGATING            │
│                                                            │
│ 2. 🔴 Villa Moderna - Cabinet delay (Score: 4,800)         │
│    Prob: 60% | Impact: 80 | Status: MITIGATING            │
│                                                            │
│ 3. 🔴 Casa Norte - Budget overrun (Score: 4,500)           │
│    Prob: 50% | Impact: 90 | Status: IDENTIFIED ⚠️          │
│                                                            │
│ 4. 🟡 Remodel Home - Weather delay (Score: 2,000)          │
│    Prob: 40% | Impact: 50 | Status: MITIGATING            │
│                                                            │
│ 5. 🟡 Villa Moderna - Labor shortage (Score: 1,800)        │
│    Prob: 30% | Impact: 60 | Status: IDENTIFIED            │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ ESTADÍSTICAS:                                              │
│ Total Risks: 18                                            │
│ • High Risk: 3                                             │
│ • Medium Risk: 8                                           │
│ • Low Risk: 7                                              │
│                                                            │
│ Realized Risks (este mes): 2                               │
│ Mitigated Successfully: 5                                  │
│                                                            │
│ [Ver Risk Matrix] [Reporte Mensual]                        │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ⚠️ Falta: Risk dashboard global
- ⚠️ Falta: Risk matrix visualization
- ⚠️ Falta: Estadísticas de risks realized
- ⚠️ Falta: Alertas proactivas de high risks

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 15**

### Mejoras CRÍTICAS:
1. 🔴 **Asignación y Notificaciones**
   - Asignar RFIs/Issues/Risks a personas específicas
   - Email notifications automáticas
   - Alertas de items críticos sin resolver
   - SLA tracking

2. 🔴 **Attachments y Documentación**
   - Fotos para Issues
   - Archivos adjuntos para RFIs
   - Before/After photos
   - Reference documents

3. 🔴 **Integration con Otros Módulos**
   - Link Issues → Tasks (auto-create task)
   - Link RFIs → Change Orders
   - Link Risks → Budget impact
   - Timeline integration

### Mejoras Importantes:
4. ⚠️ Priority levels para RFIs
5. ⚠️ Deadlines y due dates
6. ⚠️ Threading/comments en RFIs
7. ⚠️ Risk matrix visualization
8. ⚠️ Dashboard global de Issues/Risks
9. ⚠️ Templates de risks comunes
10. ⚠️ Cost impact tracking
11. ⚠️ Risk owner assignment
12. ⚠️ Review dates para risks
13. ⚠️ Estadísticas y reporting
14. ⚠️ Mobile access para field reporting

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)
- ✅ Módulo 12: Planes Diarios (14/14) ⭐ CRÍTICO
- ✅ Módulo 13: SOPs/Plantillas (5/5)
- ✅ Módulo 14: Minutas/Timeline (3/3)
- ✅ Módulo 15: RFIs, Issues & Risks (6/6)

**Total documentado: 149/250+ funciones (60%)** 🎉 ¡60% DEL SISTEMA!

**Pendientes:**
- ⏳ Módulos 17-27: 102+ funciones

---

## ✅ **MÓDULO 16: SOLICITUDES (MATERIAL & CLIENTE)** (4/4 COMPLETO)

### 📌 FUNCIÓN 16.1 - Crear Solicitud de Cliente (Client Request)

**Modelo ClientRequest:**
```python
class ClientRequest(models.Model):
    """
    Solicitudes del cliente para cambios/extras
    Pueden convertirse en Change Orders
    """
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("approved", "Aprobada"),
        ("converted", "Convertida a CO"),
        ("rejected", "Rechazada"),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, 
                                related_name="client_requests")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                   null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                             default="pending")
    change_order = models.ForeignKey('ChangeOrder', on_delete=models.SET_NULL, 
                                    null=True, blank=True,
                                    related_name='origin_requests')
```

**Propósito:**
```
SOLICITUDES DEL CLIENTE:

Workflow típico:
1. Cliente ve proyecto y tiene idea
2. Cliente crea solicitud (o PM la crea por él)
3. PM revisa y costea la solicitud
4. PM presenta costo al cliente
5. Cliente aprueba → convierte a Change Order
6. Cliente rechaza → solicitud cerrada

Beneficios:
├─ Cliente puede expresar ideas fácilmente
├─ PM tiene registro de todas las solicitudes
├─ Tracking de qué se aprobó vs qué no
├─ Conversión fácil a Change Order
└─ Portal transparente para cliente
```

**Vista de Creación:**
```python
@login_required
def client_request_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        
        if not title:
            messages.error(request, 'Título es requerido')
        else:
            from core.models import ClientRequest
            ClientRequest.objects.create(
                project=project,
                title=title,
                description=description,
                created_by=request.user
            )
            messages.success(request, 'Solicitud creada')
            return redirect('client_requests_list', project_id=project.id)
    
    return render(request, 'core/client_request_form.html', {
        'project': project
    })
```

**Interfaz (Client Portal):**
```
┌────────────────────────────────────────────────────────────┐
│ 💡 SOLICITAR CAMBIO O EXTRA - VILLA MODERNA                │
├────────────────────────────────────────────────────────────┤
│ ¿Tiene alguna idea para mejorar su proyecto?               │
│ Descríbala aquí y le cotizaremos el costo.                 │
│                                                            │
│ Título: [Agregar nicho en ducha del baño principal]        │
│                                                            │
│ Descripción detallada:                                     │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Me gustaría agregar un nicho empotrado en la ducha    │ │
│ │ del baño principal para colocar shampoos y jabones.   │ │
│ │                                                        │ │
│ │ Dimensiones aproximadas: 12" ancho x 6" alto          │ │
│ │ Ubicación: Pared lateral de la ducha                  │ │
│ │                                                        │ │
│ │ Preferiblemente con acabado en tile matching.         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ 📷 Fotos de referencia (opcional):                         │
│ [📤 Subir fotos]                                           │
│                                                            │
│ [✉️ Enviar Solicitud] [❌ Cancelar]                        │
│                                                            │
│ ℹ️ Su contractor revisará esta solicitud y le enviará     │
│ una cotización en 24-48 horas.                             │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Creación simple y directa
- ✅ Link con Change Order
- ⚠️ Falta: Upload de fotos de referencia
- ⚠️ Falta: Estimación preliminar de costo
- ⚠️ Falta: Prioridad (nice-to-have vs must-have)
- ⚠️ Falta: Deadline deseado

---

### 📌 FUNCIÓN 16.2 - Lista de Solicitudes de Cliente

**Vista de Lista:**
```python
@login_required
def client_requests_list(request, project_id=None):
    from core.models import ClientRequest
    
    if project_id:
        project = get_object_or_404(Project, id=project_id)
        qs = ClientRequest.objects.filter(project=project).order_by('-created_at')
    else:
        project = None
        qs = ClientRequest.objects.all().select_related('project').order_by('-created_at')
    
    return render(request, 'core/client_requests_list.html', {
        'project': project,
        'requests': qs
    })
```

**Interfaz (Admin View):**
```
┌────────────────────────────────────────────────────────────┐
│ 💡 SOLICITUDES DE CLIENTES - TODAS                         │
│ [Filtrar por: Todos ▼] [Buscar...]                         │
├────────────────────────────────────────────────────────────┤
│ PENDIENTES (3):                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟡 PENDING | Villa Moderna                             │ │
│ │ Agregar nicho en ducha del baño principal              │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Cliente: María González                                │ │
│ │ Creado: Aug 25, 2025 10:30 AM                          │ │
│ │                                                        │ │
│ │ [Costear] [Aprobar] [Rechazar] [Convertir a CO]       │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟡 PENDING | Casa Norte                                │ │
│ │ Cambiar color de pintura en comedor                    │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Cliente: Pedro Martínez                                │ │
│ │ Creado: Aug 24, 2025 3:15 PM                           │ │
│ │ [Ver Detalles]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ APROBADAS (2):                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✅ APPROVED | Office Complex                           │ │
│ │ Agregar electrical outlet adicional en sala de juntas  │ │
│ │ Costo cotizado: $250                                   │ │
│ │ [Convertir a CO]                                       │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ CONVERTIDAS A CO (5):                                      │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔄 CONVERTED → CO #008 | Villa Moderna                 │ │
│ │ Upgrade a granite countertops                          │ │
│ │ Convertido: Aug 20, 2025                               │ │
│ │ [Ver Change Order]                                     │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ RECHAZADAS (2):                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ❌ REJECTED | Remodel Home                             │ │
│ │ Extender deck 10 pies más                              │ │
│ │ Razón: Fuera de presupuesto del cliente               │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Interfaz (Client Portal):**
```
┌────────────────────────────────────────────────────────────┐
│ 💡 MIS SOLICITUDES - VILLA MODERNA                         │
│ [+ Nueva Solicitud]                                        │
├────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟡 EN REVISIÓN                                         │ │
│ │ Agregar nicho en ducha del baño principal              │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Enviado: Hace 2 horas                                  │ │
│ │ Status: Su contractor está revisando esta solicitud   │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✅ APROBADA Y COSTEADA                                 │ │
│ │ Upgrade a granite countertops                          │ │
│ │ ──────────────────────────────────────────────────────│ │
│ │ Costo: $2,850                                          │ │
│ │ Status: Convertida a Change Order #008                 │ │
│ │ [Ver Change Order] [Aprobar y Firmar]                  │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Lista funcional con filtrado
- ✅ Estados claros
- ⚠️ Falta: Comentarios/conversación en solicitud
- ⚠️ Falta: Cotización inline (antes de CO)
- ⚠️ Falta: Timeline de la solicitud
- ⚠️ Falta: Notificaciones de cambios de status

---

### 📌 FUNCIÓN 16.3 - Convertir Solicitud a Change Order

**Vista de Conversión:**
```python
@login_required
def client_request_convert_to_co(request, request_id):
    from core.models import ClientRequest
    cr = get_object_or_404(ClientRequest, id=request_id)
    
    # Verificar si ya fue convertida
    if cr.change_order:
        messages.info(request, 
                     f'Esta solicitud ya fue convertida al CO #{cr.change_order.id}.')
        return redirect('client_requests_list', project_id=cr.project.id)
    
    if request.method == 'POST':
        description = request.POST.get('description') or cr.description or cr.title
        amount_str = request.POST.get('amount') or '0'
        
        try:
            amt = Decimal(amount_str)
        except Exception:
            amt = Decimal('0')
        
        # Crear Change Order
        co = ChangeOrder.objects.create(
            project=cr.project,
            description=description,
            amount=amt,
            status='pending'
        )
        
        # Vincular solicitud con CO
        cr.change_order = co
        cr.status = 'converted'
        cr.save()
        
        messages.success(request, f'Solicitud convertida al CO #{co.id}.')
        return redirect('changeorder_detail', changeorder_id=co.id)
    
    return render(request, 'core/client_request_convert.html', {
        'req': cr
    })
```

**Interfaz de Conversión:**
```
┌────────────────────────────────────────────────────────────┐
│ 🔄 CONVERTIR SOLICITUD A CHANGE ORDER                      │
│ Proyecto: Villa Moderna                                    │
├────────────────────────────────────────────────────────────┤
│ SOLICITUD ORIGINAL:                                        │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Título: Agregar nicho en ducha del baño principal      │ │
│ │                                                        │ │
│ │ Descripción:                                           │ │
│ │ Me gustaría agregar un nicho empotrado en la ducha    │ │
│ │ del baño principal para colocar shampoos y jabones.   │ │
│ │ Dimensiones: 12" x 6", pared lateral, tile matching.  │ │
│ │                                                        │ │
│ │ Creado por: María González (Cliente)                  │ │
│ │ Fecha: Aug 25, 2025                                    │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ CREAR CHANGE ORDER:                                        │
│                                                            │
│ Descripción para CO:                                       │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Agregar nicho empotrado en ducha del baño principal.  │ │
│ │                                                        │ │
│ │ Especificaciones:                                      │ │
│ │ - Dimensiones: 12" ancho x 6" alto x 4" profundidad   │ │
│ │ - Ubicación: Pared lateral de ducha                   │ │
│ │ - Material: Frame de metal, backer board             │ │
│ │ - Acabado: Tile matching ducha (porcelain)            │ │
│ │ - Incluye waterproofing completo                      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Monto del Change Order: $[450.00]                          │
│                                                            │
│ Desglose:                                                  │
│ • Materiales: $120                                         │
│ • Labor (4 hrs @ $65/hr): $260                             │
│ • Overhead & profit (15%): $70                             │
│ ────────────────────────────────                           │
│ TOTAL: $450                                                │
│                                                            │
│ [🔄 Crear Change Order] [❌ Cancelar]                      │
│                                                            │
│ ℹ️ Al crear el CO, se enviará al cliente para aprobación  │
│ y firma electrónica.                                       │
└────────────────────────────────────────────────────────────┘
```

**Workflow Completo:**
```
CLIENTE → SOLICITUD → COSTEO → CHANGE ORDER → APROBACIÓN

1. Cliente crea solicitud
   └─> Status: PENDING

2. PM revisa y costea
   └─> Calcula materiales + labor + profit

3. PM convierte a Change Order
   └─> Solicitud.status = CONVERTED
   └─> Solicitud.change_order = CO#008
   └─> CO.status = PENDING

4. Cliente recibe notificación
   └─> Ve CO en su portal
   └─> Puede aprobar/rechazar

5. Cliente aprueba CO
   └─> CO.status = APPROVED
   └─> Trabajo procede

6. Trabajo completado
   └─> CO.status = COMPLETED
   └─> Cliente facturado
```

**Mejoras Identificadas:**
- ✅ Conversión funcional
- ✅ Vinculación bidireccional (Request ↔ CO)
- ⚠️ Falta: Cotización previa (antes de crear CO formal)
- ⚠️ Falta: Approval inline del cliente en solicitud
- ⚠️ Falta: Templates de pricing común
- ⚠️ Falta: Photos/attachments preservation

---

### 📌 FUNCIÓN 16.4 - Solicitudes de Material (Material Requests)

**Modelo MaterialRequest:**
```python
class MaterialRequest(models.Model):
    """
    Solicitudes de material de empleados en campo
    PM/Admin ordena materiales basado en estas solicitudes
    """
    NEEDED_WHEN_CHOICES = [
        ("now", "Ahora (emergencia)"),
        ("tomorrow", "Mañana"),
        ("next_week", "Siguiente semana"),
        ("date", "Fecha específica"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("submitted", "Enviada"),
        ("ordered", "Ordenada"),
        ("fulfilled", "Entregada"),
        ("cancelled", "Cancelada"),
        ("purchased_lead", "Compra directa (líder)"),
    ]
    
    project = models.ForeignKey("Project", on_delete=models.CASCADE, 
                                related_name="material_requests")
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                     null=True, blank=True)
    needed_when = models.CharField(max_length=20, 
                                   choices=NEEDED_WHEN_CHOICES,
                                   default="now")
    needed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                             default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Modelo MaterialRequestItem:**
```python
class MaterialRequestItem(models.Model):
    """Items individuales dentro de solicitud de material"""
    CATEGORY_CHOICES = [
        ("paint", "Pintura"),
        ("primer", "Primer"),
        ("stain", "Stain"),
        ("lacquer", "Laca/Clear"),
        ("thinner", "Thinner/Solvente"),
        ("tape", "Tape"),
        ("plastic", "Plástico"),
        ("masking_paper", "Papel enmascarar"),
        ("floor_paper", "Papel para piso"),
        ("drop_cloth", "Tela/manta protección"),
        ("brush", "Brocha"),
        ("roller_cover", "Rodillo (cover)"),
        ("roller_frame", "Rodillo (frame)"),
        ("tray", "Charola"),
        ("sandpaper", "Lija"),
        ("caulk", "Caulk/Sellador"),
        # ... muchas más categorías
    ]
    
    material_request = models.ForeignKey(MaterialRequest, 
                                        on_delete=models.CASCADE,
                                        related_name='items')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    brand = models.CharField(max_length=100, blank=True)
    product_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)  # gal, qt, roll, box, etc.
    notes = models.TextField(blank=True)
```

**Propósito:**
```
SOLICITUDES DE MATERIAL:

Escenario típico:
1. Empleado en sitio ve que falta material
2. Crea solicitud desde móvil/tablet
3. Especifica urgencia (now, tomorrow, next week)
4. PM ve solicitud en dashboard
5. PM ordena material
6. Material llega a sitio
7. Solicitud marcada como fulfilled

Beneficios:
├─ Empleados pueden pedir sin llamar
├─ PM tiene registro de todas las solicitudes
├─ Tracking de qué se ordenó cuándo
├─ Evita delays por falta de material
└─ Inventory planning mejorado
```

**Interfaz (Employee Mobile):**
```
┌────────────────────────────────────────────────────────────┐
│ 📦 SOLICITAR MATERIALES                                    │
│ Proyecto: Villa Moderna                                    │
├────────────────────────────────────────────────────────────┤
│ ⏰ Cuándo necesitas el material:                           │
│ ( ) Ahora (emergencia)                                     │
│ (•) Mañana                                                 │
│ ( ) Próxima semana                                         │
│ ( ) Fecha específica: [___________]                        │
│                                                            │
│ ITEMS SOLICITADOS:                                         │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 1. Paint - Interior                                    │ │
│ │    Marca: Sherwin Williams                             │ │
│ │    Producto: Emerald Interior - White                  │ │
│ │    Cantidad: [3] Galones                               │ │
│ │    [×]                                                 │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 2. Roller Covers                                       │ │
│ │    Cantidad: [6] Piezas                                │ │
│ │    Tamaño: 9"                                          │ │
│ │    [×]                                                 │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [+ Agregar Item]                                           │
│                                                            │
│ Notas adicionales:                                         │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Necesitamos paint urgente para terminar living room   │ │
│ │ mañana. Solo quedan 1/2 galón.                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [📤 Enviar Solicitud]                                      │
└────────────────────────────────────────────────────────────┘
```

**Dashboard PM:**
```
┌────────────────────────────────────────────────────────────┐
│ 📦 SOLICITUDES DE MATERIAL - PENDIENTES                    │
├────────────────────────────────────────────────────────────┤
│ 🔴 URGENTE - AHORA (2):                                    │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Villa Moderna | Juan Pérez                             │ │
│ │ • Paint - Sherwin Williams Emerald (3 gal)             │ │
│ │ • Roller covers 9" (6 pcs)                             │ │
│ │ Creado: Hace 1 hora                                    │ │
│ │ [Ordenar] [Ver Detalles]                               │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ 🟡 MAÑANA (5):                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Casa Norte | Pedro López                               │ │
│ │ • Caulk (4 tubes)                                      │ │
│ │ • Sandpaper 120 grit (1 pack)                          │ │
│ │ [Ordenar]                                              │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ 🟢 PRÓXIMA SEMANA (3):                                     │
│ [Ver todas...]                                             │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Modelo completo con items
- ✅ Urgencia levels
- ✅ Status workflow
- ⚠️ Falta: Vistas implementadas (solo modelo existe)
- ⚠️ Falta: Mobile app para empleados
- ⚠️ Falta: Integration con inventory
- ⚠️ Falta: Auto-ordering desde vendors
- ⚠️ Falta: Cost tracking de solicitudes
- ⚠️ Falta: Approval workflow si costo > threshold

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 16**

### Mejoras CRÍTICAS:
1. 🔴 **Material Requests - Implementación Completa**
   - Vistas de creación y lista
   - Mobile app para empleados
   - Dashboard de urgencias
   - Integration con inventory

2. 🔴 **Client Requests - Mejoras**
   - Cotización inline (antes de CO)
   - Conversación/comments
   - Photo attachments
   - Approval directo en solicitud

3. 🔴 **Notificaciones**
   - Email cuando nueva solicitud
   - SMS para urgentes
   - Push notifications en app
   - Status updates automáticos

### Mejoras Importantes:
4. ⚠️ Templates de pricing para solicitudes comunes
5. ⚠️ Timeline de solicitud (audit trail)
6. ⚠️ Prioridad levels en client requests
7. ⚠️ Deadline tracking
8. ⚠️ Cost impact analysis
9. ⚠️ Integration con vendors (auto-order)
10. ⚠️ Analytics de solicitudes (patterns, frecuencia)
11. ⚠️ Approval workflow por monto
12. ⚠️ Bulk ordering de material requests

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)
- ✅ Módulo 12: Planes Diarios (14/14) ⭐ CRÍTICO
- ✅ Módulo 13: SOPs/Plantillas (5/5)
- ✅ Módulo 14: Minutas/Timeline (3/3)
- ✅ Módulo 15: RFIs, Issues & Risks (6/6)
- ✅ Módulo 16: Solicitudes (Material & Cliente) (4/4)

**Total documentado: 153/250+ funciones (61%)** 🎉

**Pendientes:**
- ⏳ Módulos 18-27: 97+ funciones

---

## ✅ **MÓDULO 17: FOTOS & FLOOR PLANS** (5/5 COMPLETO)

### 📌 FUNCIÓN 17.1 - Subir Fotos del Sitio (Site Photos)

**Modelo SitePhoto:**
```python
class SitePhoto(models.Model):
    """
    Fotos del progreso del proyecto con anotaciones de colores/acabados
    Permite tracking visual y aprobaciones de colores
    """
    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, 
                                related_name="site_photos")
    room = models.CharField(max_length=120, blank=True)
    wall_ref = models.CharField(max_length=120, blank=True, 
                                help_text="Pared o ubicación")
    image = models.ImageField(upload_to="site_photos/")
    
    # Color/acabado aplicado
    approved_color_id = models.IntegerField(
        null=True, blank=True, db_index=True,
        help_text="ID de color aprobado (opcional)"
    )
    color_text = models.CharField(max_length=120, blank=True)
    brand = models.CharField(max_length=120, blank=True)
    finish = models.CharField(max_length=120, blank=True)
    gloss = models.CharField(max_length=120, blank=True)
    special_finish = models.BooleanField(default=False)
    coats = models.PositiveSmallIntegerField(default=1)
    
    # Anotaciones visuales sobre la imagen
    annotations = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                   null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Propósito:**
```
FOTOS DE PROGRESO:
├─ Documentación visual del proyecto
├─ Before/After photos
├─ Aprobación de colores aplicados
├─ Registro de acabados
├─ Tracking de número de coats
└─ Comunicación visual con cliente

ANOTACIONES:
├─ Marcar áreas específicas en la foto
├─ Notas sobre trabajo realizado
├─ Touch-ups necesarios
└─ Aprobaciones de cliente
```

**Vista de Creación:**
```python
@login_required
def site_photo_create(request, project_id):
    from core.models import Project
    from core.forms import SitePhotoForm
    project = get_object_or_404(Project, pk=project_id)
    
    if request.method == "POST":
        form = SitePhotoForm(request.POST, request.FILES, project=project)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.project = project
            obj.created_by = request.user
            try:
                obj.annotations = json.loads(
                    form.cleaned_data.get("annotations") or "{}"
                )
            except Exception:
                obj.annotations = {}
            obj.save()
            messages.success(request, "Foto y anotaciones guardadas.")
            return redirect("site_photo_list", project_id=project.id)
    else:
        form = SitePhotoForm(project=project)
    
    return render(request, "core/site_photo_form.html", {
        "project": project,
        "form": form
    })
```

**Interfaz:**
```
┌────────────────────────────────────────────────────────────┐
│ 📷 SUBIR FOTO DEL SITIO - VILLA MODERNA                    │
├────────────────────────────────────────────────────────────┤
│ Foto: [📤 Elegir archivo...]                               │
│                                                            │
│ Ubicación:                                                 │
│ Cuarto/Área: [Living Room]                                 │
│ Pared/Referencia: [Pared Norte]                            │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ DETALLES DE COLOR/ACABADO (opcional):                      │
│                                                            │
│ Color: [Cool Gray SW 7047]                                 │
│ Marca: [Sherwin Williams ▼]                                │
│ Acabado: [Eggshell ▼]                                      │
│ Gloss Level: [Semi-Gloss ▼]                                │
│                                                            │
│ [✓] Acabado especial                                       │
│ Número de coats aplicados: [2]                             │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ Notas:                                                     │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Segunda coat aplicada hoy. Color se ve excelente,     │ │
│ │ cliente muy contento. Pequeño touch-up necesario en   │ │
│ │ esquina superior derecha.                             │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [💾 Guardar Foto] [❌ Cancelar]                            │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Upload funcional con metadata
- ✅ Annotations JSON support
- ✅ Color tracking
- ⚠️ Falta: Anotaciones visuales en la imagen (markup)
- ⚠️ Falta: Comparación before/after
- ⚠️ Falta: Organización por fecha/fase
- ⚠️ Falta: Aprobación del cliente inline

---

### 📌 FUNCIÓN 17.2 - Galería de Fotos del Sitio

**Vista de Lista:**
```python
@login_required
def site_photo_list(request, project_id):
    from core.models import Project, SitePhoto
    project = get_object_or_404(Project, pk=project_id)
    photos = SitePhoto.objects.filter(project=project).order_by("-created_at")
    return render(request, "core/site_photo_list.html", {
        "project": project,
        "photos": photos
    })
```

**Interfaz de Galería:**
```
┌────────────────────────────────────────────────────────────┐
│ 📷 GALERÍA DE FOTOS - VILLA MODERNA                        │
│ [+ Subir Nueva Foto]                                       │
├────────────────────────────────────────────────────────────┤
│ Filtrar por: [Todos los cuartos ▼] [Todas las fechas ▼]    │
│ Vista: [📷 Grid] [📋 Lista]                                │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ HOY - Aug 25, 2025 (4 fotos)                               │
│ ┌─────────┬─────────┬─────────┬─────────┐                 │
│ │  ┌───┐  │  ┌───┐  │  ┌───┐  │  ┌───┐  │                 │
│ │  │ 📷│  │  │ 📷│  │  │ 📷│  │  │ 📷│  │                 │
│ │  │   │  │  │   │  │  │   │  │  │   │  │                 │
│ │  └───┘  │  └───┘  │  └───┘  │  └───┘  │                 │
│ │ Living  │ Kitchen │ Bathroom│ Bedroom │                 │
│ │ Rm N    │ E Wall  │ Shower  │ 1 Closet│                 │
│ │ 3:45 PM │ 2:30 PM │ 11:15AM │ 10:00AM │                 │
│ └─────────┴─────────┴─────────┴─────────┘                 │
│                                                            │
│ AYER - Aug 24, 2025 (7 fotos)                              │
│ ┌─────────┬─────────┬─────────┬─────────┐                 │
│ │  📷     │  📷     │  📷     │  📷     │                 │
│ │ ...                                    │                 │
│ └─────────┴─────────┴─────────┴─────────┘                 │
│                                                            │
│ ESTA SEMANA (23 fotos)                                     │
│ [Ver todas...]                                             │
└────────────────────────────────────────────────────────────┘

Foto Individual:
┌────────────────────────────────────────────────────────────┐
│ [←] Living Room - Pared Norte                              │
├────────────────────────────────────────────────────────────┤
│              ┌──────────────────────┐                      │
│              │                      │                      │
│              │     [Foto Grande]    │                      │
│              │                      │                      │
│              └──────────────────────┘                      │
│                                                            │
│ 📅 Aug 25, 2025 3:45 PM                                    │
│ 👤 Por: Juan Pérez                                         │
│                                                            │
│ 🎨 COLOR:                                                  │
│ Cool Gray SW 7047 | Sherwin Williams                       │
│ Acabado: Eggshell | Gloss: Semi-Gloss                      │
│ Coats aplicados: 2 ✓✓                                      │
│                                                            │
│ 📝 NOTAS:                                                  │
│ Segunda coat aplicada hoy. Color se ve excelente,          │
│ cliente muy contento. Pequeño touch-up necesario en        │
│ esquina superior derecha.                                  │
│                                                            │
│ [✏️ Editar] [🗑️ Eliminar] [📤 Compartir con Cliente]      │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Galería funcional ordenada por fecha
- ⚠️ Falta: Filtrado por cuarto/área
- ⚠️ Falta: Slideshow mode
- ⚠️ Falta: Lightbox para ver fotos grandes
- ⚠️ Falta: Download múltiple (ZIP)
- ⚠️ Falta: Tags/categorías

---

### 📌 FUNCIÓN 17.3 - Subir Floor Plan

**Modelo FloorPlan:**
```python
class FloorPlan(models.Model):
    """
    Planos de planta con sistema de pins para marcar ubicaciones
    Permite comunicación visual precisa
    """
    project = models.ForeignKey('Project', on_delete=models.CASCADE, 
                                related_name='floor_plans')
    name = models.CharField(
        max_length=120,
        help_text='Nivel o descripción: Planta Baja, Nivel 2, etc.'
    )
    image = models.ImageField(upload_to='floor_plans/')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                   null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ('project', 'name')
```

**Vista de Creación:**
```python
@login_required
def floor_plan_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    profile = getattr(request.user, 'profile', None)
    
    if not (request.user.is_staff or 
            (profile and profile.role in ['project_manager','client'])):
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = FloorPlanForm(request.POST, request.FILES)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.project = project
            inst.created_by = request.user
            inst.save()
            messages.success(request, 'Plano subido.')
            return redirect('floor_plan_list', project_id=project_id)
    else:
        form = FloorPlanForm(initial={'project': project})
    
    return render(request, 'core/floor_plan_form.html', {
        'form': form,
        'project': project,
    })
```

**Interfaz:**
```
┌────────────────────────────────────────────────────────────┐
│ 📐 SUBIR FLOOR PLAN - VILLA MODERNA                        │
├────────────────────────────────────────────────────────────┤
│ Nombre del Plano: [Planta Baja]                            │
│ (Ej: Planta Baja, Segundo Piso, Basement, etc.)           │
│                                                            │
│ Archivo del Plano: [📤 Elegir archivo...]                  │
│ Formatos aceptados: JPG, PNG, PDF                          │
│                                                            │
│ ℹ️ TIPS:                                                   │
│ • Asegúrate que el plano sea legible                       │
│ • Resolución recomendada: mínimo 1500px                    │
│ • Puedes agregar pins después de subirlo                   │
│                                                            │
│ [📤 Subir Plano] [❌ Cancelar]                             │
└────────────────────────────────────────────────────────────┘
```

**Lista de Floor Plans:**
```
┌────────────────────────────────────────────────────────────┐
│ 📐 FLOOR PLANS - VILLA MODERNA                             │
│ [+ Subir Nuevo Plano]                                      │
├────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📋 PLANTA BAJA                                         │ │
│ │ ┌─────────────────┐                                    │ │
│ │ │   [Thumbnail]   │ 12 pins marcados                   │ │
│ │ └─────────────────┘ Subido: Aug 20, 2025               │ │
│ │                                                        │ │
│ │ [👁️ Ver Plano] [📍 Agregar Pin] [✏️ Editar]            │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📋 SEGUNDO PISO                                        │ │
│ │ ┌─────────────────┐                                    │ │
│ │ │   [Thumbnail]   │ 8 pins marcados                    │ │
│ │ └─────────────────┘ Subido: Aug 20, 2025               │ │
│ │                                                        │ │
│ │ [👁️ Ver Plano] [📍 Agregar Pin]                        │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Upload funcional
- ✅ Unique constraint (project + name)
- ⚠️ Falta: PDF to image conversion
- ⚠️ Falta: Zoom y pan en vista
- ⚠️ Falta: Version control de planos
- ⚠️ Falta: Comparación de versiones

---

### 📌 FUNCIÓN 17.4 - Agregar Pin al Floor Plan

**Modelo PlanPin:**
```python
class PlanPin(models.Model):
    """
    Pins marcadores en floor plans para notas, touch-ups, colores, etc.
    Coordenadas normalizadas 0..1 para responsiveness
    """
    PIN_TYPES = [
        ('note', 'Nota'),
        ('touchup', 'Touch-up'),
        ('color', 'Color'),
        ('alert', 'Alerta'),
        ('damage', 'Daño'),
    ]
    
    plan = models.ForeignKey(FloorPlan, on_delete=models.CASCADE, 
                            related_name='pins')
    # Coordenadas normalizadas 0..1 relativas al ancho/alto de la imagen
    x = models.DecimalField(max_digits=6, decimal_places=4, help_text='0..1')
    y = models.DecimalField(max_digits=6, decimal_places=4, help_text='0..1')
    
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    pin_type = models.CharField(max_length=20, choices=PIN_TYPES, 
                                default='note')
    
    # Links opcionales
    color_sample = models.ForeignKey('ColorSample', null=True, blank=True, 
                                    on_delete=models.SET_NULL,
                                    related_name='pins')
    linked_task = models.ForeignKey('Task', null=True, blank=True, 
                                   on_delete=models.SET_NULL,
                                   related_name='pins')
    
    # Trayectoria multipunto (para rutas, ej: "paint this wall")
    path_points = models.JSONField(
        default=list, blank=True,
        help_text='Lista de puntos conectados: [{x:0.1,y:0.2,label:"A"}]'
    )
```

**Vista de Agregar Pin:**
```python
@login_required
def floor_plan_add_pin(request, plan_id):
    from core.models import FloorPlan, PlanPin, ColorSample, Task
    plan = get_object_or_404(FloorPlan, id=plan_id)
    
    if request.method == 'POST':
        form = PlanPinForm(request.POST)
        try:
            x = Decimal(request.POST.get('x'))
            y = Decimal(request.POST.get('y'))
        except Exception:
            messages.error(request, 'Coordenadas inválidas.')
            return redirect('floor_plan_detail', plan_id=plan.id)
        
        # Trayectoria multipunto si existe
        is_multipoint = request.POST.get('is_multipoint') == 'true'
        path_points_json = request.POST.get('path_points', '[]')
        try:
            path_points = json.loads(path_points_json) if is_multipoint else []
        except Exception:
            path_points = []
        
        if form.is_valid():
            pin = form.save(commit=False)
            pin.plan = plan
            pin.x = x
            pin.y = y
            pin.is_multipoint = is_multipoint
            pin.path_points = path_points
            pin.created_by = request.user
            pin.save()
            
            # Crear Task automáticamente si es touch-up
            if form.cleaned_data.get('create_task') and \
               pin.pin_type in ['touchup','color']:
                task = Task.objects.create(
                    project=plan.project,
                    title=pin.title or 'Touch-up plano',
                    description=pin.description,
                    status='Pendiente',
                )
                pin.linked_task = task
                pin.save()
            
            messages.success(request, 'Pin agregado.')
            return redirect('floor_plan_detail', plan_id=plan.id)
```

**Interfaz Interactiva:**
```
┌────────────────────────────────────────────────────────────┐
│ 📐 FLOOR PLAN: PLANTA BAJA - VILLA MODERNA                 │
│ [+ Agregar Pin] [🔍 Zoom] [📏 Medir] [💾 Guardar]          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│    ╔═══════════════════════════════════════════════╗      │
│    ║                 [PLANO]                       ║      │
│    ║                                               ║      │
│    ║    📍Living Rm    🔴Touch-up     💡Color     ║      │
│    ║         ↓             ↓            ↓         ║      │
│    ║    ┌──────────┬────────────┬──────────┐      ║      │
│    ║    │  Bedroom │  Bathroom  │ Kitchen  │      ║      │
│    ║    │    1     │            │          │      ║      │
│    ║    ├──────────┴────────────┴──────────┤      ║      │
│    ║    │         Living Room             │      ║      │
│    ║    │                                  │      ║      │
│    ║    └──────────────────────────────────┘      ║      │
│    ║                                               ║      │
│    ╚═══════════════════════════════════════════════╝      │
│                                                            │
│ LEYENDA:                                                   │
│ 📍 = Nota general                                          │
│ 🔴 = Touch-up necesario                                    │
│ 💡 = Aprobación de color                                   │
│ ⚠️ = Alerta/Problema                                       │
│ 🔨 = Daño reportado                                        │
└────────────────────────────────────────────────────────────┘

Crear Pin:
┌────────────────────────────────────────────────────────────┐
│ ➕ AGREGAR PIN AL PLANO                                    │
│ (Haz click en el plano para marcar ubicación)              │
├────────────────────────────────────────────────────────────┤
│ Ubicación seleccionada: Living Room (x:0.45, y:0.62)       │
│                                                            │
│ Tipo de Pin: [Touch-up ▼]                                  │
│ • Nota                                                     │
│ • Touch-up ✓                                               │
│ • Color                                                    │
│ • Alerta                                                   │
│ • Daño                                                     │
│                                                            │
│ Título: [Esquina con imperfección]                         │
│                                                            │
│ Descripción:                                               │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Pequeña imperfección en esquina donde se une pared    │ │
│ │ norte con oeste. Requiere touch-up de paint.          │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [✓] Crear Task automáticamente                            │
│                                                            │
│ Vincular con:                                              │
│ Color Sample: [Cool Gray SW 7047 ▼] (opcional)             │
│                                                            │
│ [💾 Agregar Pin] [❌ Cancelar]                             │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Pins con coordenadas normalizadas
- ✅ Múltiples tipos de pin
- ✅ Auto-create Task para touch-ups
- ✅ Multipoint paths support
- ⚠️ Falta: Drag & drop para reposicionar
- ⚠️ Falta: Pin clustering cuando muchos pins
- ⚠️ Falta: Filtrar pins por tipo
- ⚠️ Falta: Timeline de pins (ver histórico)

---

### 📌 FUNCIÓN 17.5 - Ver Floor Plan con Pins

**Vista Detallada:**
```python
@login_required
def floor_plan_detail(request, plan_id):
    from core.models import FloorPlan, PlanPin, ColorSample, Task
    plan = get_object_or_404(FloorPlan, id=plan_id)
    pins = plan.pins.select_related('color_sample','linked_task').all()
    color_samples = plan.project.color_samples.filter(
        status__in=['approved','review']
    ).order_by('-created_at')[:50]
    
    return render(request, 'core/floor_plan_detail.html', {
        'plan': plan,
        'pins': pins,
        'color_samples': color_samples,
        'project': plan.project,
    })

@login_required
def pin_detail_ajax(request, pin_id):
    """Return JSON details for a pin to show in a popover."""
    from core.models import PlanPin
    pin = get_object_or_404(
        PlanPin.objects.select_related('linked_task','color_sample'),
        id=pin_id
    )
    
    data = {
        'id': pin.id,
        'title': getattr(pin, 'title', f"Pin #{pin.id}"),
        'description': getattr(pin, 'description', ''),
        'type': getattr(pin, 'pin_type', ''),
        'task': None,
        'color_sample': None,
        'links': {},
    }
    
    if pin.linked_task_id:
        data['task'] = {
            'id': pin.linked_task_id,
            'title': getattr(pin.linked_task, 'title', ''),
            'status': getattr(pin.linked_task, 'status', ''),
        }
        data['links']['task'] = reverse('task_detail', 
                                       args=[pin.linked_task_id])
    
    if pin.color_sample_id:
        data['color_sample'] = {
            'id': pin.color_sample_id,
            'name': getattr(pin.color_sample, 'name', ''),
            'brand': getattr(pin.color_sample, 'brand', ''),
            'status': getattr(pin.color_sample, 'status', ''),
        }
        data['links']['color_sample'] = reverse('color_sample_detail', 
                                               args=[pin.color_sample_id])
    
    return JsonResponse(data)
```

**Interfaz con Popover:**
```
┌────────────────────────────────────────────────────────────┐
│ 📐 PLANTA BAJA - VILLA MODERNA                             │
├────────────────────────────────────────────────────────────┤
│           ╔════════════════════════════════╗               │
│           ║      [PLANO CON PINS]          ║               │
│           ║                                ║               │
│           ║    📍 ← (hover para ver info)  ║               │
│           ║       ┌──────────────────┐     ║               │
│           ║       │ 🔴 Touch-up      │     ║               │
│           ║       │ Esquina con      │     ║               │
│           ║       │ imperfección     │     ║               │
│           ║       │                  │     ║               │
│           ║       │ Task: #045       │     ║               │
│           ║       │ Status: Pendiente│     ║               │
│           ║       │                  │     ║               │
│           ║       │ [Ver Task]       │     ║               │
│           ║       └──────────────────┘     ║               │
│           ╚════════════════════════════════╝               │
│                                                            │
│ PINS EN ESTE PLANO (12):                                   │
│ 🔴 Touch-ups: 5                                            │
│ 💡 Colores: 4                                              │
│ 📍 Notas: 2                                                │
│ ⚠️ Alertas: 1                                              │
│                                                            │
│ [+ Agregar Pin] [🖨️ Imprimir] [📤 Compartir]              │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Vista interactiva con pins
- ✅ AJAX popover para detalles
- ✅ Links a Tasks y Color Samples
- ⚠️ Falta: Comentarios en pins
- ⚠️ Falta: Marcar pin como completado
- ⚠️ Falta: Notifications cuando nuevo pin
- ⚠️ Falta: Export plan con pins to PDF

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 17**

### Mejoras CRÍTICAS:
1. 🔴 **Anotaciones Visuales**
   - Markup tools en fotos (círculos, flechas, texto)
   - Highlighting de áreas específicas
   - Before/After comparisons
   - Approval workflow visual

2. 🔴 **Floor Plan Interactivity**
   - Zoom y pan suave
   - Drag & drop pins
   - Real-time collaboration
   - Mobile-friendly touch controls

3. 🔴 **Organization & Search**
   - Filtrado por cuarto/fecha/tipo
   - Tags y categorías
   - Full-text search en notas
   - Smart albums (auto-grouping)

### Mejoras Importantes:
4. ⚠️ PDF support para floor plans
5. ⚠️ Version control de planos
6. ⚠️ Lightbox/slideshow mode
7. ⚠️ Bulk download (ZIP)
8. ⚠️ Pin clustering
9. ⚠️ Timeline de pins
10. ⚠️ Comentarios en pins
11. ⚠️ Pin completion tracking
12. ⚠️ Export plan to PDF con pins
13. ⚠️ Notifications de nuevos pins
14. ⚠️ Integration con client portal

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)
- ✅ Módulo 12: Planes Diarios (14/14) ⭐ CRÍTICO
- ✅ Módulo 13: SOPs/Plantillas (5/5)
- ✅ Módulo 14: Minutas/Timeline (3/3)
- ✅ Módulo 15: RFIs, Issues & Risks (6/6)
- ✅ Módulo 16: Solicitudes (Material & Cliente) (4/4)
- ✅ Módulo 17: Fotos & Floor Plans (5/5)

**Total documentado: 158/250+ funciones (63%)** 🎉

**Pendientes:**
- ⏳ Módulos 19-27: 94+ funciones

---

## ✅ **MÓDULO 18: INVENTORY (INVENTARIO)** (3/3 COMPLETO)

### 📌 FUNCIÓN 18.1 - Ver Inventory de Proyecto

**Modelo InventoryItem:**
```python
class InventoryItem(models.Model):
    """Items trackables en inventario"""
    CATEGORY_CHOICES = [
        ("MATERIAL", "Material"),
        ("PINTURA", "Pintura"),
        ("ESCALERA", "Escaleras"),
        ("LIJADORA", "Lijadoras / Power"),
        ("SPRAY", "Sprayadoras / Tips"),
        ("HERRAMIENTA", "Herramientas"),
        ("OTRO", "Otro"),
    ]
    
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    unit = models.CharField(max_length=20, default="pcs")
    is_equipment = models.BooleanField(default=False)  # reutilizable
    track_serial = models.BooleanField(default=False)
    default_threshold = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    active = models.BooleanField(default=True)
    no_threshold = models.BooleanField(default=False)
```

**Modelo InventoryLocation:**
```python
class InventoryLocation(models.Model):
    """Ubicaciones de inventario: storage central o proyecto específico"""
    name = models.CharField(max_length=120)
    project = models.ForeignKey("core.Project", null=True, blank=True, 
                               on_delete=models.CASCADE,
                               related_name="inventory_locations")
    is_storage = models.BooleanField(default=False)  # Storage central
```

**Modelo ProjectInventory:**
```python
class ProjectInventory(models.Model):
    """Stock de un item en una ubicación específica"""
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE,
                                related_name="stocks")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    threshold_override = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    
    class Meta:
        unique_together = ("item", "location")
    
    def threshold(self):
        return self.threshold_override or self.item.default_threshold
    
    @property
    def is_below(self):
        """Verifica si está bajo el threshold"""
        th = self.threshold()
        return th is not None and self.quantity < th
```

**Vista de Inventory:**
```python
@login_required
def inventory_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    storage = InventoryLocation.objects.filter(is_storage=True).first()
    
    # Obtener o crear ubicación principal del proyecto
    loc, _ = InventoryLocation.objects.get_or_create(
        project=project,
        name="Principal",
        defaults={"is_storage": False}
    )
    
    # Stock en esta ubicación
    stocks = (ProjectInventory.objects
              .filter(location=loc)
              .select_related("item")
              .order_by("item__category", "item__name"))
    
    # Items bajo threshold
    low = [s for s in stocks if s.is_below]
    
    return render(request, "core/inventory_view.html", {
        "project": project,
        "stocks": stocks,
        "low": low,
        "storage": storage,
    })
```

**Interfaz:**
```
┌────────────────────────────────────────────────────────────┐
│ 📦 INVENTARIO - VILLA MODERNA                              │
│ Ubicación: Principal                                       │
│ [➡️ Mover Items] [📊 Historial] [⚙️ Configurar]            │
├────────────────────────────────────────────────────────────┤
│ ⚠️ ITEMS BAJO THRESHOLD (3):                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 Paint - Interior White                              │ │
│ │    Stock: 0.5 gal | Threshold: 2 gal                   │ │
│ │    [Pedir más]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟡 Roller Covers 9"                                    │ │
│ │    Stock: 2 pcs | Threshold: 5 pcs                     │ │
│ │    [Pedir más]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ INVENTARIO COMPLETO:                                       │
│                                                            │
│ 🎨 PINTURA (5 items):                                     │
│ • Interior White ............ 0.5 gal 🔴                   │
│ • Primer .................... 3 gal ✅                     │
│ • Exterior Gray ............. 1.5 gal ✅                   │
│                                                            │
│ 🔧 HERRAMIENTAS (8 items):                                │
│ • Roller Covers 9" .......... 2 pcs 🟡                    │
│ • Brushes 2" ................ 8 pcs ✅                     │
│ • Spray Tips 517 ............ 4 pcs ✅                     │
│                                                            │
│ 📦 MATERIALES (12 items):                                 │
│ • Caulk White ............... 12 tubes ✅                  │
│ • Sandpaper 120 ............. 3 packs ✅                   │
│                                                            │
│ [Ver Todos] [Exportar]                                     │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Stock tracking por ubicación
- ✅ Threshold alerts
- ✅ Multi-ubicación support
- ⚠️ Falta: Barcode scanning
- ⚠️ Falta: Auto-reorder cuando bajo threshold
- ⚠️ Falta: Cost tracking (valor del inventory)
- ⚠️ Falta: Expiration dates para materiales

---

### 📌 FUNCIÓN 18.2 - Mover Inventory (Transfers, Receipts, Issues)

**Modelo InventoryMovement:**
```python
class InventoryMovement(models.Model):
    """Registro de movimientos de inventario"""
    TYPE_CHOICES = [
        ("RECEIVE", "Entrada compra"),
        ("ISSUE", "Salida a uso / consumo"),
        ("TRANSFER", "Traslado"),
        ("RETURN", "Regreso a storage"),
        ("ADJUST", "Ajuste manual"),
        ("CONSUME", "Consumo registrado"),
    ]
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    from_location = models.ForeignKey(
        InventoryLocation, null=True, blank=True,
        related_name="moves_out", on_delete=models.SET_NULL
    )
    to_location = models.ForeignKey(
        InventoryLocation, null=True, blank=True,
        related_name="moves_in", on_delete=models.SET_NULL
    )
    movement_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expense = models.ForeignKey(
        "core.Expense", null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_movements"
    )
    
    def apply(self):
        """Aplica el efecto del movimiento en stock"""
        if self.movement_type in ("RECEIVE", "RETURN"):
            if self.to_location:
                stock, _ = ProjectInventory.objects.get_or_create(
                    item=self.item,
                    location=self.to_location
                )
                stock.quantity += self.quantity
                stock.save()
        
        elif self.movement_type in ("ISSUE", "CONSUME"):
            if self.from_location:
                stock, _ = ProjectInventory.objects.get_or_create(
                    item=self.item,
                    location=self.from_location
                )
                stock.quantity -= self.quantity
                if stock.quantity < 0:
                    stock.quantity = 0
                stock.save()
        
        elif self.movement_type == "TRANSFER":
            if self.from_location:
                s_from, _ = ProjectInventory.objects.get_or_create(
                    item=self.item,
                    location=self.from_location
                )
                s_from.quantity -= self.quantity
                if s_from.quantity < 0:
                    s_from.quantity = 0
                s_from.save()
            
            if self.to_location:
                s_to, _ = ProjectInventory.objects.get_or_create(
                    item=self.item,
                    location=self.to_location
                )
                s_to.quantity += self.quantity
                s_to.save()
```

**Vista de Movimiento:**
```python
@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def inventory_move_view(request, project_id):
    from core.models import InventoryItem, InventoryLocation, InventoryMovement
    project = get_object_or_404(Project, pk=project_id)
    
    # Asegurar storage y ubicación principal
    storage = InventoryLocation.objects.filter(is_storage=True).first()
    if not storage:
        storage = InventoryLocation.objects.create(
            name="Main Storage",
            is_storage=True
        )
    
    proj_loc, _ = InventoryLocation.objects.get_or_create(
        project=project,
        name="Principal",
        defaults={"is_storage": False}
    )
    
    form = InventoryMovementForm(request.POST or None)
    
    # Filtrar ubicaciones
    from_qs = InventoryLocation.objects.filter(
        Q(is_storage=True) | Q(project=project)
    ).order_by("-is_storage", "name")
    
    to_qs = InventoryLocation.objects.filter(
        Q(is_storage=True) | Q(project__isnull=False)
    ).order_by("-is_storage", "project__name", "name")
    
    form.fields["from_location"].queryset = from_qs
    form.fields["to_location"].queryset = to_qs
    form.fields["item"].queryset = InventoryItem.objects.filter(
        active=True
    ).order_by("category", "name")
    
    if request.method == "POST" and form.is_valid():
        item = form.cleaned_data["item"]
        mtype = form.cleaned_data["movement_type"]
        qty = form.cleaned_data["quantity"]
        from_loc = form.cleaned_data.get("from_location")
        to_loc = form.cleaned_data.get("to_location")
        note = form.cleaned_data.get("note") or ""
        
        # Validar stock suficiente para salidas
        if mtype in ("ISSUE", "CONSUME", "TRANSFER"):
            stock = ProjectInventory.objects.filter(
                item=item,
                location=from_loc
            ).first()
            if not stock or stock.quantity < qty:
                form.add_error(
                    "quantity",
                    f"Stock insuficiente (disponible: {float(stock.quantity) if stock else 0})"
                )
        
        if not form.errors:
            move = InventoryMovement.objects.create(
                item=item,
                movement_type=mtype,
                quantity=qty,
                from_location=from_loc,
                to_location=to_loc,
                note=note,
                created_by=request.user,
            )
            move.apply()
            
            # Opción de crear expense asociado
            if form.cleaned_data.get("add_expense"):
                next_url = reverse("inventory_history", args=[project.id])
                create_url = f"{reverse('expense_create')}?project_id={project.id}&next={next_url}&ref=inv_move_{move.id}"
                messages.info(request, "Ahora registra el gasto del ticket.")
                return redirect(create_url)
            
            messages.success(request, "Movimiento aplicado.")
            return redirect("inventory_view", project_id=project.id)
    
    return render(request, "core/inventory_move.html", {
        "project": project,
        "form": form
    })
```

**Interfaz de Movimiento:**
```
┌────────────────────────────────────────────────────────────┐
│ ➡️ MOVER INVENTORY - VILLA MODERNA                         │
├────────────────────────────────────────────────────────────┤
│ Tipo de Movimiento: [Transfer ▼]                           │
│ • RECEIVE - Entrada de compra                              │
│ • ISSUE - Salida a uso                                     │
│ • TRANSFER - Traslado entre ubicaciones ✓                  │
│ • RETURN - Regreso a storage                               │
│ • CONSUME - Consumo registrado                             │
│ • ADJUST - Ajuste manual                                   │
│                                                            │
│ Item: [Paint - Interior White ▼]                           │
│                                                            │
│ Desde: [Main Storage ▼]                                    │
│ Stock disponible: 15 gal                                   │
│                                                            │
│ Hacia: [Villa Moderna - Principal ▼]                       │
│                                                            │
│ Cantidad: [3] gal                                          │
│                                                            │
│ Notas:                                                     │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Transfer para trabajo de esta semana                   │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [✓] Crear gasto asociado después                          │
│                                                            │
│ [➡️ Ejecutar Movimiento] [❌ Cancelar]                     │
└────────────────────────────────────────────────────────────┘

Resultado:
✅ Movimiento aplicado
• Main Storage: 15 gal → 12 gal (-3)
• Villa Moderna: 0.5 gal → 3.5 gal (+3)
```

**Tipos de Movimiento:**
```
RECEIVE (Entrada):
├─ Compra nueva de material
├─ Solo requiere: to_location
└─ Aumenta stock en destino

ISSUE (Salida):
├─ Material sale a uso/proyecto
├─ Requiere: from_location
└─ Disminuye stock en origen

TRANSFER (Traslado):
├─ Mover entre ubicaciones
├─ Requiere: from_location y to_location
├─ Disminuye en origen
└─ Aumenta en destino

RETURN (Regreso):
├─ Material no usado regresa a storage
├─ Similar a RECEIVE
└─ Aumenta stock en storage

CONSUME (Consumo):
├─ Material usado/consumido
├─ Registra uso real
└─ Disminuye stock

ADJUST (Ajuste):
├─ Corrección manual
├─ Inventario físico
└─ Ajusta discrepancias
```

**Mejoras Identificadas:**
- ✅ 6 tipos de movimiento
- ✅ Validación de stock suficiente
- ✅ Integration con Expenses
- ✅ apply() method actualiza stocks
- ⚠️ Falta: Bulk movements
- ⚠️ Falta: Approval workflow para movements grandes
- ⚠️ Falta: Reservations (hold stock sin mover)
- ⚠️ Falta: Serial number tracking

---

### 📌 FUNCIÓN 18.3 - Historial de Inventory

**Vista de Historial:**
```python
@login_required
@staff_required
def inventory_history_view(request, project_id):
    from core.models import InventoryLocation, InventoryMovement, InventoryItem
    project = get_object_or_404(Project, pk=project_id)
    
    # Ubicaciones relacionadas con este proyecto
    loc_qs = InventoryLocation.objects.filter(
        Q(project=project) | Q(is_storage=True)
    )
    
    # Filtros
    item_id = request.GET.get("item")
    mtype = request.GET.get("type")
    
    # Movimientos relacionados
    qs = (InventoryMovement.objects
          .filter(Q(from_location__in=loc_qs) | Q(to_location__in=loc_qs))
          .select_related("item", "from_location", "to_location", "created_by")
          .order_by("-created_at"))
    
    if item_id:
        qs = qs.filter(item_id=item_id)
    if mtype:
        qs = qs.filter(movement_type=mtype)
    
    items = InventoryItem.objects.filter(active=True).order_by("name")
    
    return render(request, "core/inventory_history.html", {
        "project": project,
        "movements": qs[:100],  # Últimos 100
        "items": items,
        "selected_item": item_id,
        "selected_type": mtype,
        "movement_types": InventoryMovement.TYPE_CHOICES,
    })
```

**Interfaz de Historial:**
```
┌────────────────────────────────────────────────────────────┐
│ 📊 HISTORIAL DE INVENTORY - VILLA MODERNA                  │
├────────────────────────────────────────────────────────────┤
│ Filtrar por:                                               │
│ Item: [Todos ▼]  Tipo: [Todos ▼]  Fecha: [Últimos 30 días]│
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ HOY - Aug 25, 2025                                         │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 3:45 PM | ➡️ TRANSFER                                  │ │
│ │ Paint - Interior White | 3 gal                         │ │
│ │ Main Storage → Villa Moderna - Principal               │ │
│ │ Nota: Transfer para trabajo de esta semana            │ │
│ │ Por: Admin                                             │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 10:30 AM | 📦 RECEIVE                                  │ │
│ │ Roller Covers 9" | 12 pcs                              │ │
│ │ → Main Storage                                         │ │
│ │ Nota: Compra Home Depot                                │ │
│ │ 💰 Gasto asociado: $45.00                              │ │
│ │ Por: Admin                                             │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ AYER - Aug 24, 2025                                        │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 4:15 PM | 🔽 CONSUME                                   │ │
│ │ Caulk White | 4 tubes                                  │ │
│ │ Villa Moderna - Principal →                            │ │
│ │ Nota: Usado en bathroom                                │ │
│ │ Por: Juan Pérez                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 2:00 PM | ↩️ RETURN                                    │ │
│ │ Paint - Exterior Gray | 0.5 gal                        │ │
│ │ Villa Moderna - Principal → Main Storage               │ │
│ │ Nota: Material no usado, regresa a storage             │ │
│ │ Por: Admin                                             │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ESTA SEMANA (15 movimientos)                               │
│ [Ver todos...]                                             │
│                                                            │
│ [📊 Reporte] [📥 Exportar] [🔄 Refresh]                    │
└────────────────────────────────────────────────────────────┘
```

**Resumen de Movimientos:**
```
ESTA SEMANA:
┌─────────────────────────────────────────────────┐
│ Tipo         │ Cantidad │ Valor Aprox.         │
├──────────────┼──────────┼──────────────────────┤
│ RECEIVE      │ 8        │ $1,245               │
│ TRANSFER     │ 12       │ -                    │
│ CONSUME      │ 18       │ -                    │
│ RETURN       │ 3        │ -                    │
│ ADJUST       │ 2        │ -                    │
├──────────────┼──────────┼──────────────────────┤
│ TOTAL        │ 43       │ $1,245 entradas      │
└─────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Historial completo con filtros
- ✅ Link a expense asociado
- ✅ Audit trail de quién y cuándo
- ⚠️ Falta: Reporte de consumption por proyecto
- ⚠️ Falta: Cost analysis (valor usado vs comprado)
- ⚠️ Falta: Variance analysis (expected vs actual)
- ⚠️ Falta: Export to Excel/PDF

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 18**

### Mejoras CRÍTICAS:
1. 🔴 **Cost Tracking**
   - Valor del inventory actual
   - Cost of goods sold (COGS)
   - Variance analysis
   - Budget impact

2. 🔴 **Automation**
   - Auto-reorder cuando bajo threshold
   - Email alerts para low stock
   - Integration con vendors
   - Barcode scanning

3. 🔴 **Advanced Features**
   - Serial number tracking
   - Lot/batch tracking
   - Expiration dates
   - Reservations/holds

### Mejoras Importantes:
4. ⚠️ Bulk movements
5. ⚠️ Approval workflow
6. ⚠️ Physical inventory count (cycle counts)
7. ⚠️ Consumption reports
8. ⚠️ Forecast demand
9. ⚠️ Multi-warehouse support
10. ⚠️ Integration con purchase orders
11. ⚠️ Mobile app para inventory
12. ⚠️ Analytics dashboard

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)
- ✅ Módulo 12: Planes Diarios (14/14) ⭐ CRÍTICO
- ✅ Módulo 13: SOPs/Plantillas (5/5)
- ✅ Módulo 14: Minutas/Timeline (3/3)
- ✅ Módulo 15: RFIs, Issues & Risks (6/6)
- ✅ Módulo 16: Solicitudes (Material & Cliente) (4/4)
- ✅ Módulo 17: Fotos & Floor Plans (5/5)
- ✅ Módulo 18: Inventory (3/3)

**Total documentado: 161/250+ funciones (64%)** 🎉

**Pendientes:**
- ⏳ Módulos 20-27: 88+ funciones

---

## ✅ **MÓDULO 19: COLOR SAMPLES & DESIGN CHAT** (6/6 COMPLETO)

### 📌 FUNCIÓN 19.1 - Catálogo de Muestras de Color

**Modelo ColorSample:**
```python
class ColorSample(models.Model):
    """Muestras de color para aprobación del cliente"""
    STATUS_CHOICES = [
        ('proposed', 'Propuesto'),
        ('review', 'En Revisión'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('archived', 'Archivado'),
    ]
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE,
                               related_name='color_samples')
    code = models.CharField(max_length=60, blank=True,
                           help_text='SW xxxx, Milesi xxx, etc.')
    name = models.CharField(max_length=120, blank=True)
    brand = models.CharField(max_length=120, blank=True)
    finish = models.CharField(max_length=120, blank=True)
    gloss = models.CharField(max_length=50, blank=True)
    version = models.PositiveIntegerField(default=1,
                                         help_text='Incrementa cuando se sube una variante')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                             default='proposed')
    sample_image = models.ImageField(upload_to='color_samples/',
                                     null=True, blank=True)
    reference_photo = models.ImageField(upload_to='color_samples/ref/',
                                       null=True, blank=True)
    notes = models.TextField(blank=True)
    client_notes = models.TextField(blank=True)
    annotations = models.JSONField(default=dict, blank=True,
                                  help_text='Marcadores y comentarios sobre la imagen (JSON)')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, blank=True,
                                  related_name='color_samples_created')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True,
                                   related_name='color_samples_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    parent_sample = models.ForeignKey('self', null=True, blank=True,
                                     on_delete=models.SET_NULL,
                                     related_name='variants')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'brand', 'code']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-increment version if derived from parent
        if self.parent_sample and self.version == 1:
            siblings = ColorSample.objects.filter(parent_sample=self.parent_sample)
            max_v = siblings.aggregate(m=models.Max('version'))['m'] or 1
            self.version = max_v + 1
        
        # Marcar approved_at si status aprobado
        if self.status == 'approved' and not self.approved_at:
            self.approved_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def approve(self, user):
        """Aprobar muestra"""
        self.status = 'approved'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'approved_by', 'approved_at'])
    
    def reject(self, user, note=None):
        """Rechazar muestra con nota opcional"""
        self.status = 'rejected'
        if note:
            self.notes = (self.notes + '\nRechazado: ' + note).strip()
        self.save(update_fields=['status', 'notes'])
```

**Vista de Catálogo:**
```python
@login_required
def color_sample_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    samples = (project.color_samples
               .select_related('created_by')
               .all()
               .order_by('-created_at'))
    
    # Filtros
    brand = request.GET.get('brand')
    if brand:
        samples = samples.filter(brand__icontains=brand)
    
    status = request.GET.get('status')
    if status:
        samples = samples.filter(status=status)
    
    return render(request, 'core/color_sample_list.html', {
        'project': project,
        'samples': samples,
        'filter_brand': brand,
        'filter_status': status,
    })
```

**Interfaz de Catálogo:**
```
┌────────────────────────────────────────────────────────────┐
│ 🎨 CATÁLOGO DE COLORES - VILLA MODERNA                     │
│ [➕ Nueva Muestra] [📋 Aprobados] [📊 Reporte]             │
├────────────────────────────────────────────────────────────┤
│ Filtrar: Marca: [Todos ▼] Status: [Todos ▼] [🔍]          │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ ✅ APROBADOS (3):                                          │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [IMAGEN]  SW 7005 - Pure White (v1)                    │ │
│ │           Sherwin Williams | Eggshell                  │ │
│ │           ✓ Aprobado por Admin - Aug 20, 2025          │ │
│ │           [Ver Detalles]                               │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [IMAGEN]  Milesi 203 - Walnut Stain (v2)               │ │
│ │           Milesi | Semi-Transparent                    │ │
│ │           ✓ Aprobado por Cliente - Aug 22, 2025        │ │
│ │           Variante de v1 (tonos más oscuros)           │ │
│ │           [Ver Detalles]                               │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ 🔄 EN REVISIÓN (2):                                        │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [IMAGEN]  BM 2124-70 - Cloud White                     │ │
│ │           Benjamin Moore | Matte                       │ │
│ │           🟡 Esperando aprobación cliente              │ │
│ │           Notas: "Muestra para dormitorio principal"   │ │
│ │           [Revisar] [Aprobar] [Rechazar]               │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ 📝 PROPUESTOS (4):                                         │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [IMAGEN]  SW 6244 - Naval                              │ │
│ │           Sherwin Williams | Semi-Gloss                │ │
│ │           📌 Propuesto por Designer - Hoy              │ │
│ │           [Mover a Revisión]                           │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ❌ RECHAZADOS (1): [Ver todos]                             │
│                                                            │
│ ESTADÍSTICAS:                                              │
│ • Total muestras: 10                                       │
│ • Marcas: Sherwin Williams (4), Benjamin Moore (3),       │
│   Milesi (2), Farrow & Ball (1)                           │
│ • Tiempo promedio aprobación: 2.3 días                    │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Version control con parent_sample
- ✅ Annotations JSON para markup
- ✅ Dual images (sample + reference)
- ⚠️ Falta: Side-by-side comparison tool
- ⚠️ Falta: Color matching con fotos del proyecto
- ⚠️ Falta: AI color suggestions
- ⚠️ Falta: Export palette to Paint Store

---

### 📌 FUNCIÓN 19.2 - Crear y Editar Muestra

**Vista de Creación:**
```python
@login_required
def color_sample_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    profile = getattr(request.user, 'profile', None)
    
    # Permisos: staff, client, PM
    if not (request.user.is_staff or 
            (profile and profile.role in ['client','project_manager'])):
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ColorSampleForm(request.POST, request.FILES)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.project = project
            inst.created_by = request.user
            inst.save()
            messages.success(request, 'Muestra creada.')
            return redirect('color_sample_list', project_id=project_id)
    else:
        form = ColorSampleForm(initial={'project': project})
    
    return render(request, 'core/color_sample_form.html', {
        'form': form,
        'project': project,
    })
```

**Interfaz de Creación:**
```
┌────────────────────────────────────────────────────────────┐
│ ➕ NUEVA MUESTRA DE COLOR - VILLA MODERNA                  │
├────────────────────────────────────────────────────────────┤
│ Información Básica:                                        │
│ Código: [SW 7005____________]                              │
│ Nombre: [Pure White_________]                              │
│ Marca:  [Sherwin Williams___] [▼ Marcas comunes]          │
│                                                            │
│ Acabado:                                                   │
│ Finish: [Eggshell___________]                              │
│ Gloss:  [20% sheen__________]                              │
│                                                            │
│ Imágenes:                                                  │
│ Muestra:    [📁 Subir archivo]                             │
│             ┌──────────────────┐                           │
│             │  [PREVIEW]       │                           │
│             └──────────────────┘                           │
│                                                            │
│ Referencia: [📁 Subir archivo]                             │
│             ┌──────────────────┐                           │
│             │  [PREVIEW]       │                           │
│             └──────────────────┘                           │
│                                                            │
│ Notas Internas (Staff):                                    │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Sugerencia para dormitorio principal.                  │ │
│ │ Color neutro cálido, combina con piso de madera.       │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Notas para Cliente:                                        │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Este tono complementa la iluminación natural.          │ │
│ │ Recomendado para espacios amplios.                     │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Opciones Avanzadas:                                        │
│ [✓] Basado en muestra anterior: [Ninguno ▼]               │
│     (Si seleccionas, auto-incrementa versión)             │
│                                                            │
│ Status inicial: [● Propuesto] [○ En Revisión]             │
│                                                            │
│ [💾 Crear Muestra] [❌ Cancelar]                           │
└────────────────────────────────────────────────────────────┘
```

**Workflow de Versiones:**
```
Variantes de Color:
┌───────────────────────────────────────────────┐
│ Original: SW 7005 Pure White (v1)             │
│ ├─ Variant: SW 7005 Pure White (v2)           │
│ │  Nota: "Tono ligeramente más cálido"        │
│ │  Status: rejected                           │
│ └─ Variant: SW 7005 Pure White (v3)           │
│    Nota: "Ajuste final aprobado por cliente"  │
│    Status: approved ✓                         │
└───────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Version tracking automático
- ✅ Dual notes (staff + client)
- ✅ Flexible status workflow
- ⚠️ Falta: Batch upload de múltiples muestras
- ⚠️ Falta: Templates de marcas comunes (preset brands/finishes)
- ⚠️ Falta: Color picker integration
- ⚠️ Falta: Material calculator (cuántos galones necesarios)

---

### 📌 FUNCIÓN 19.3 - Detalle de Muestra con Anotaciones

**Vista de Detalle:**
```python
@login_required
def color_sample_detail(request, sample_id):
    from core.models import ColorSample
    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
    
    return render(request, 'core/color_sample_detail.html', {
        'sample': sample,
        'project': project,
    })
```

**Interfaz de Detalle:**
```
┌────────────────────────────────────────────────────────────┐
│ 🎨 SW 7005 - PURE WHITE (v1)                               │
│ Sherwin Williams | Eggshell | 20% sheen                    │
│ [⬅️ Volver] [✏️ Editar] [📋 Crear Variante] [🗑️ Archivar] │
├────────────────────────────────────────────────────────────┤
│ STATUS: ✅ APROBADO                                         │
│ • Aprobado por: Admin                                      │
│ • Fecha: Aug 20, 2025 3:45 PM                              │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ MUESTRA DE COLOR:                                          │
│ ┌────────────────────────────────────────────────────────┐ │
│ │                                                        │ │
│ │              [COLOR SAMPLE IMAGE]                      │ │
│ │                                                        │ │
│ │  📌 Annotation 1: "Perfecto para esta zona"           │ │
│ │     (Cliente - Aug 19, 2025)                           │ │
│ │                                                        │ │
│ │  💬 Annotation 2: "Confirmar con este acabado"        │ │
│ │     (PM - Aug 19, 2025)                                │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│ [🖊️ Agregar Anotación]                                     │
│                                                            │
│ FOTO DE REFERENCIA:                                        │
│ ┌────────────────────────────────────────────────────────┐ │
│ │                                                        │ │
│ │            [REFERENCE PHOTO - LIVING ROOM]             │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 📝 NOTAS INTERNAS (Staff):                                 │
│ Sugerencia para dormitorio principal.                     │
│ Color neutro cálido, combina con piso de madera.          │
│                                                            │
│ 💬 NOTAS PARA CLIENTE:                                     │
│ Este tono complementa la iluminación natural.             │
│ Recomendado para espacios amplios.                        │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ HISTORIAL:                                                 │
│ • Aug 20, 2025 3:45 PM - Aprobado por Admin                │
│ • Aug 19, 2025 2:30 PM - Movido a 'En Revisión' por PM    │
│ • Aug 18, 2025 10:15 AM - Creado por Designer             │
│                                                            │
│ VARIANTES:                                                 │
│ • v2 (Rechazada) - "Tono más oscuro" [Ver]                │
│ • v3 (En revisión) - "Ajuste final" [Ver]                 │
│                                                            │
│ [📤 Exportar Info] [📧 Enviar a Cliente]                   │
└────────────────────────────────────────────────────────────┘
```

**Annotations JSON Format:**
```json
{
  "annotations": [
    {
      "id": "ann_1",
      "x": 0.35,
      "y": 0.42,
      "text": "Perfecto para esta zona",
      "user": "Cliente",
      "timestamp": "2025-08-19T14:30:00Z",
      "type": "comment"
    },
    {
      "id": "ann_2",
      "x": 0.65,
      "y": 0.58,
      "text": "Confirmar con este acabado",
      "user": "PM",
      "timestamp": "2025-08-19T15:45:00Z",
      "type": "question"
    }
  ]
}
```

**Mejoras Identificadas:**
- ✅ Interactive annotations
- ✅ Version history tracking
- ✅ Dual image display
- ⚠️ Falta: Real-time annotation collaboration
- ⚠️ Falta: AR preview (visualize on walls)
- ⚠️ Falta: Light simulation (morning/afternoon/evening)
- ⚠️ Falta: Color harmony analysis

---

### 📌 FUNCIÓN 19.4 - Revisar y Aprobar Muestras

**Vista de Revisión:**
```python
@login_required
def color_sample_review(request, sample_id):
    from core.models import ColorSample
    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
    profile = getattr(request.user, 'profile', None)
    
    # Permisos: clients, PM, designers pueden mover a 'review'
    # Solo staff puede aprobar/rechazar
    if not (request.user.is_staff or 
            (profile and profile.role in ['client','project_manager','designer'])):
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ColorSampleReviewForm(request.POST, instance=sample)
        if form.is_valid():
            old_status = sample.status
            inst = form.save(commit=False)
            requested_status = inst.status
            
            # Validar transición de estado
            if requested_status in ['approved','rejected'] and not request.user.is_staff:
                messages.error(request, 'Solo el staff puede aprobar o rechazar colores.')
            else:
                if requested_status == 'approved' and not inst.approved_by:
                    inst.approved_by = request.user
                inst.save()
                
                # Notificaciones
                from core.notifications import notify_color_review, notify_color_approved
                if requested_status == 'approved':
                    notify_color_approved(inst, request.user)
                elif old_status != requested_status:
                    notify_color_review(inst, request.user)
                
                messages.success(request, f'Estado actualizado a {inst.get_status_display()}')
            
            return redirect('color_sample_detail', sample_id=sample.id)
    else:
        form = ColorSampleReviewForm(instance=sample)
    
    return render(request, 'core/color_sample_review.html', {
        'form': form,
        'sample': sample,
        'project': project,
    })
```

**Interfaz de Revisión:**
```
┌────────────────────────────────────────────────────────────┐
│ 🔍 REVISAR MUESTRA - SW 7005 PURE WHITE                    │
│ Villa Moderna                                              │
├────────────────────────────────────────────────────────────┤
│ [IMAGEN DE MUESTRA]                                        │
│                                                            │
│ Status Actual: 🟡 En Revisión                              │
│                                                            │
│ Cambiar Status a:                                          │
│ [○ Propuesto]                                              │
│ [● En Revisión]                                            │
│ [○ Aprobado]     ⚠️ Solo staff                             │
│ [○ Rechazado]    ⚠️ Solo staff                             │
│ [○ Archivado]                                              │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ Actualizar Notas:                                          │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Notas Internas (Staff):                                │ │
│ │ [Texto existente...]                                   │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Notas para Cliente:                                    │ │
│ │ [Texto existente...]                                   │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [💾 Guardar Cambios] [❌ Cancelar]                         │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 📧 NOTIFICACIONES:                                         │
│ Al aprobar/rechazar, se notificará a:                      │
│ • Cliente del proyecto                                     │
│ • Project Manager                                          │
│ • Designer (si aplica)                                     │
└────────────────────────────────────────────────────────────┘
```

**Workflow de Estados:**
```
Estado de Muestra:
┌─────────────────────────────────────────────┐
│ proposed (Propuesto)                        │
│   ↓ Cliente/PM/Designer pueden mover a →   │
│ review (En Revisión)                        │
│   ↓ Solo STAFF puede aprobar/rechazar →    │
│ approved (Aprobado) ✓                       │
│     O                                       │
│ rejected (Rechazado) ❌                     │
│   ↓ Cualquiera puede archivar →            │
│ archived (Archivado) 📦                     │
└─────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Role-based workflow control
- ✅ Notification system integration
- ✅ Audit trail (who approved/rejected)
- ⚠️ Falta: Approval delegation
- ⚠️ Falta: Batch approve/reject
- ⚠️ Falta: Conditional approval (client + PM both required)
- ⚠️ Falta: Approval deadline tracking

---

### 📌 FUNCIÓN 19.5 - Quick Actions (AJAX Approve/Reject)

**Vista AJAX:**
```python
@login_required
def color_sample_quick_action(request, sample_id):
    """Quick approve/reject color sample (staff only, AJAX)."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    
    sample = get_object_or_404(ColorSample, id=sample_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            sample.status = 'approved'
            sample.approved_by = request.user
            sample.save()
            from core.notifications import notify_color_approved
            notify_color_approved(sample, request.user)
            return JsonResponse({
                'success': True,
                'status': 'approved',
                'display': 'Aprobado'
            })
        
        elif action == 'reject':
            sample.status = 'rejected'
            sample.save()
            return JsonResponse({
                'success': True,
                'status': 'rejected',
                'display': 'Rechazado'
            })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
```

**UI de Quick Actions:**
```
En lista de muestras (Staff view):
┌────────────────────────────────────────────────────────────┐
│ 🔄 EN REVISIÓN:                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [IMAGEN]  BM 2124-70 - Cloud White                     │ │
│ │           Benjamin Moore | Matte                       │ │
│ │           🟡 Esperando aprobación                      │ │
│ │                                                        │ │
│ │           [✅ Aprobar] [❌ Rechazar] [👁️ Ver Detalle]  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Acción ejecutada sin recargar página, actualiza badge]   │
└────────────────────────────────────────────────────────────┘
```

**JavaScript Example:**
```javascript
function quickApprove(sampleId) {
    fetch(`/color-sample/${sampleId}/quick-action/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'action=approve'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar UI sin recargar
            updateStatusBadge(sampleId, data.status, data.display);
            showNotification('Color aprobado exitosamente');
        }
    });
}
```

**Mejoras Identificadas:**
- ✅ Fast approval workflow
- ✅ No page reload required
- ✅ Staff-only protection
- ⚠️ Falta: Undo action
- ⚠️ Falta: Bulk quick actions
- ⚠️ Falta: Quick approve con nota
- ⚠️ Falta: Mobile swipe gestures

---

### 📌 FUNCIÓN 19.6 - Design Chat Colaborativo

**Modelo DesignChatMessage:**
```python
class DesignChatMessage(models.Model):
    """Chat de diseño para colaboración en color y estilo"""
    project = models.ForeignKey('Project', on_delete=models.CASCADE,
                               related_name='design_messages')
    user = models.ForeignKey(User, on_delete=models.SET_NULL,
                            null=True, blank=True)
    message = models.TextField()
    image = models.ImageField(upload_to='design_chat/',
                             null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    pinned = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
```

**Vista de Design Chat:**
```python
@login_required
def design_chat(request, project_id):
    """Chat colaborativo de diseño (simple poll)."""
    from core.models import DesignChatMessage
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        msg = request.POST.get('message','').strip()
        image = request.FILES.get('image')
        
        if msg or image:
            DesignChatMessage.objects.create(
                project=project,
                user=request.user,
                message=msg,
                image=image
            )
            return redirect('design_chat', project_id=project.id)
    
    messages_qs = (project.design_messages
                   .select_related('user')[:200])
    
    return render(request, 'core/design_chat.html', {
        'project': project,
        'messages': messages_qs,
    })
```

**Interfaz de Design Chat:**
```
┌────────────────────────────────────────────────────────────┐
│ 💬 DESIGN CHAT - VILLA MODERNA                             │
│ [🔄 Refresh] [📌 Pinned (2)]                               │
├────────────────────────────────────────────────────────────┤
│ 📌 MENSAJES FIJADOS:                                       │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Designer - Aug 18, 2025 10:30 AM                       │ │
│ │ Paleta de colores aprobada:                            │ │
│ │ [IMAGEN DE PALETA]                                     │ │
│ │ SW 7005 (Principal) + BM 2124-70 (Acentos)            │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ CONVERSACIÓN:                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Cliente - Hoy 3:45 PM                                  │ │
│ │ Me gusta el tono blanco, pero ¿podemos ver             │ │
│ │ una opción ligeramente más cálida?                     │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Designer - Hoy 4:10 PM                                 │ │
│ │ Claro! Te comparto estas opciones:                     │ │
│ │ [IMAGEN 1] [IMAGEN 2] [IMAGEN 3]                       │ │
│ │ La primera tiene undertones beige sutiles.             │ │
│ │ [📌 Fijar]                                             │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ PM - Hoy 4:25 PM                                       │ │
│ │ Tenemos muestra de la opción 1 en el proyecto.        │ │
│ │ ¿Quieres que la coloquemos en la pared para verla     │ │
│ │ con luz natural?                                       │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Cliente - Hoy 4:30 PM                                  │ │
│ │ ¡Sí por favor! Pasaré mañana a las 10am.              │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Ver 45 mensajes anteriores]                               │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ ENVIAR MENSAJE:                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Escribe tu mensaje aquí...                            │ │
│ └────────────────────────────────────────────────────────┘ │
│ [📎 Adjuntar Imagen] [📤 Enviar]                           │
└────────────────────────────────────────────────────────────┘
```

**Participantes Típicos:**
```
Design Chat Roles:
┌──────────────────────────────────────────┐
│ 👤 Cliente                               │
│    - Comparte preferencias              │
│    - Aprueba opciones finales           │
│                                          │
│ 🎨 Designer                              │
│    - Propone paletas                    │
│    - Sube muestras visuales             │
│    - Explica opciones                   │
│                                          │
│ 👷 Project Manager                       │
│    - Coordina visitas al sitio          │
│    - Confirma availability de muestras  │
│    - Timeline de decisiones             │
│                                          │
│ 👨‍💼 Admin/Owner                           │
│    - Supervisión general                │
│    - Aprobaciones finales               │
└──────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Simple polling-based chat
- ✅ Image attachments
- ✅ Pinned messages
- ⚠️ Falta: WebSocket real-time updates
- ⚠️ Falta: Read receipts
- ⚠️ Falta: @mention notifications
- ⚠️ Falta: Thread/reply system
- ⚠️ Falta: Search in chat history
- ⚠️ Falta: Rich text formatting
- ⚠️ Falta: Emoji reactions

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 19**

### Mejoras CRÍTICAS:
1. 🔴 **Visual Tools**
   - AR preview (visualize colors on actual walls)
   - Light simulation (different times of day)
   - Side-by-side comparison tool
   - Color matching con fotos existentes

2. 🔴 **Collaboration Enhancement**
   - Real-time chat (WebSocket)
   - @mention notifications
   - Read receipts
   - Thread/reply system

3. 🔴 **Workflow Optimization**
   - Batch operations (approve/reject múltiples)
   - Approval delegation
   - Deadline tracking
   - Undo actions

### Mejoras Importantes:
4. ⚠️ AI color suggestions based on style
5. ⚠️ Export palette to paint stores
6. ⚠️ Material calculator (gallons needed)
7. ⚠️ Color harmony analysis
8. ⚠️ Templates de marcas comunes
9. ⚠️ Batch upload múltiples muestras
10. ⚠️ Conditional approval (client + PM required)
11. ⚠️ Mobile swipe gestures para quick actions
12. ⚠️ Rich text formatting en chat
13. ⚠️ Search in chat history
14. ⚠️ Emoji reactions

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)
- ✅ Módulo 12: Planes Diarios (14/14) ⭐ CRÍTICO
- ✅ Módulo 13: SOPs/Plantillas (5/5)
- ✅ Módulo 14: Minutas/Timeline (3/3)
- ✅ Módulo 15: RFIs, Issues & Risks (6/6)
- ✅ Módulo 16: Solicitudes (Material & Cliente) (4/4)
- ✅ Módulo 17: Fotos & Floor Plans (5/5)
- ✅ Módulo 18: Inventory (3/3)
- ✅ Módulo 19: Color Samples & Design Chat (6/6)

**Total documentado: 167/250+ funciones (67%)** 🎉

**Pendientes:**
- ⏳ Módulos 21-27: 85+ funciones

---

## ✅ **MÓDULO 20: COMMUNICATION (CHAT & COMMENTS)** (3/3 COMPLETO)

### 📌 FUNCIÓN 20.1 - Project Chat con Canales

**Modelo ChatChannel:**
```python
class ChatChannel(models.Model):
    """Canales de chat por proyecto (grupo, directo, etc.)"""
    CHANNEL_TYPES = [
        ('group', 'Grupo'),
        ('direct', 'Directo'),
    ]
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE,
                               related_name='chat_channels')
    name = models.CharField(max_length=120)
    channel_type = models.CharField(max_length=10, choices=CHANNEL_TYPES,
                                   default='group')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='chat_channels',
                                         blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('project', 'name')
        ordering = ['name']
```

**Modelo ChatMessage:**
```python
class ChatMessage(models.Model):
    """Mensajes dentro de un canal de chat"""
    channel = models.ForeignKey(ChatChannel, on_delete=models.CASCADE,
                               related_name='messages')
    user = models.ForeignKey(User, on_delete=models.SET_NULL,
                            null=True, blank=True)
    message = models.TextField(blank=True)
    image = models.ImageField(upload_to='project_chat/',
                             null=True, blank=True)
    link_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

**Vista de Chat:**
```python
def _ensure_default_channels(project, user):
    """Asegurar canales default: Grupo y Directo"""
    group, _ = ChatChannel.objects.get_or_create(
        project=project,
        name='Grupo',
        defaults={
            'channel_type': 'group',
            'is_default': True,
            'created_by': user
        }
    )
    
    direct, _ = ChatChannel.objects.get_or_create(
        project=project,
        name='Directo',
        defaults={
            'channel_type': 'direct',
            'is_default': True,
            'created_by': user
        }
    )
    
    # Añadir participantes automáticos
    if user and not group.participants.filter(id=user.id).exists():
        group.participants.add(user)
    if user and not direct.participants.filter(id=user.id).exists():
        direct.participants.add(user)
    
    # Incluir cliente si existe
    if project.client:
        try:
            cu = User.objects.get(username=project.client)
            group.participants.add(cu)
            direct.participants.add(cu)
        except User.DoesNotExist:
            pass
    
    return group, direct

@login_required
def project_chat_room(request, project_id, channel_id):
    project = get_object_or_404(Project, id=project_id)
    channel = get_object_or_404(ChatChannel, id=channel_id, project=project)
    
    # Access control
    if not (request.user.is_staff or 
            channel.participants.filter(id=request.user.id).exists()):
        messages.error(request, 'No tienes acceso a este chat.')
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'invite':
            username = (request.POST.get('username') or '').strip()
            try:
                u = User.objects.get(username=username)
                channel.participants.add(u)
                messages.success(request, f'{username} invitado.')
                return redirect('project_chat_room',
                              project_id=project.id,
                              channel_id=channel.id)
            except User.DoesNotExist:
                messages.error(request, 'Usuario no encontrado.')
        
        elif action == 'send':
            text = (request.POST.get('message') or '').strip()
            link_url = (request.POST.get('link_url') or '').strip()
            image = request.FILES.get('image')
            
            if not text and not image and not link_url:
                messages.error(request, 'Mensaje vacío.')
            else:
                ChatMessage.objects.create(
                    channel=channel,
                    user=request.user,
                    message=text,
                    link_url=link_url,
                    image=image
                )
                return redirect('project_chat_room',
                              project_id=project.id,
                              channel_id=channel.id)

    messages_list = (channel.messages
                     .select_related('user')[:200])
    channels = project.chat_channels.all().order_by('name')
    
    return render(request, 'core/project_chat_room.html', {
        'project': project,
        'channel': channel,
        'channels': channels,
        'messages': messages_list,
    })
```

**Interfaz de Chat:**
```
┌────────────────────────────────────────────────────────────┐
│ 💬 PROJECT CHAT - VILLA MODERNA                            │
├──────────┬─────────────────────────────────────────────────┤
│ CANALES  │ # Grupo (12 participantes)                      │
│          │ [🔄 Refresh] [➕ Invitar] [⚙️]                   │
│ # Grupo  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ @ Direct │                                                 │
│ ───────  │ Admin - Hoy 3:45 PM                             │
│          │ Equipo de pintura reporta que terminarán hoy.  │
│ [➕ New] │                                                 │
│          │ ┌─────────────────────────────────────────────┐ │
│          │ │ Juan PM - Hoy 3:50 PM                       │ │
│          │ │ Perfecto! Mañana empezamos con pisos.       │ │
│          │ └─────────────────────────────────────────────┘ │
│          │                                                 │
│          │ Cliente - Hoy 4:10 PM                           │
│          │ [IMAGEN: foto del progreso]                    │
│          │ ¿A qué hora puedo pasar mañana a ver avance?   │
│          │                                                 │
│          │ ┌─────────────────────────────────────────────┐ │
│          │ │ Juan PM - Hoy 4:15 PM                       │ │
│          │ │ Después de las 2pm es ideal, equipo         │ │
│          │ │ estará trabajando en living room.           │ │
│          │ │ 🔗 Link: calendario.kibray.com/visit-villa  │ │
│          │ └─────────────────────────────────────────────┘ │
│          │                                                 │
│          │ [Ver 48 mensajes anteriores...]                │
│          │                                                 │
│          │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│          │ ENVIAR MENSAJE:                                 │
│          │ ┌───────────────────────────────────────────┐   │
│          │ │ Escribe mensaje...                        │   │
│          │ └───────────────────────────────────────────┘   │
│          │ [📎 Imagen] [🔗 Link] [📤 Enviar]              │
└──────────┴─────────────────────────────────────────────────┘
```

**Tipos de Canales:**
```
Canales Default por Proyecto:
┌───────────────────────────────────────────┐
│ # Grupo (group)                           │
│   • Todos los participantes del proyecto  │
│   • PM, Cliente, Empleados asignados      │
│   • Comunicación general                  │
│   • Auto-creado al acceder al proyecto    │
│                                           │
│ @ Directo (direct)                        │
│   • Comunicación 1-on-1                   │
│   • PM ↔ Cliente                          │
│   • Auto-creado al acceder al proyecto    │
│                                           │
│ Canales Personalizados:                   │
│   • Crear según necesidad                 │
│   • Ej: "Diseño", "Logística", etc.      │
│   • Gestión manual de participantes       │
└───────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Multi-canal support
- ✅ Participant management
- ✅ Media sharing (images, links)
- ⚠️ Falta: WebSocket real-time updates
- ⚠️ Falta: Read receipts
- ⚠️ Falta: Typing indicators
- ⚠️ Falta: Message reactions
- ⚠️ Falta: Thread replies
- ⚠️ Falta: Search/filter messages
- ⚠️ Falta: File attachments (PDFs, docs)
- ⚠️ Falta: Voice messages
- ⚠️ Falta: Video calls integration

---

### 📌 FUNCIÓN 20.2 - Comentarios de Proyecto

**Modelo Comment:**
```python
class Comment(models.Model):
    """
    Comentarios en proyectos, pueden estar asociados a tareas específicas.
    Permiten adjuntar imágenes para comunicación visual.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                               related_name='comments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to="comments/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Relacionar comentario con tarea si aplica
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments',
        help_text="Tarea relacionada si este comentario es sobre una tarea específica"
    )

    class Meta:
        ordering = ['-created_at']
```

**Vista de Agregar Comentario:**
```python
@login_required
def agregar_comentario(request, project_id):
    """
    Permite a clientes y staff agregar comentarios con imágenes.
    Útil para comunicación continua y documentación visual.
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Verificar acceso
    profile = getattr(request.user, 'profile', None)
    from core.models import ClientProjectAccess
    has_access = ClientProjectAccess.objects.filter(
        user=request.user,
        project=project
    ).exists()
    
    if profile and profile.role == 'client':
        if not (has_access or project.client == request.user.username):
            messages.error(request, "No tienes acceso a este proyecto.")
            return redirect('dashboard_client')
    elif not request.user.is_staff and not has_access:
        messages.error(request, "Acceso denegado.")
        return redirect('dashboard')
    
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        image = request.FILES.get("image")
        
        if not text and not image:
            messages.error(request, "Debes agregar texto o imagen.")
            return redirect('client_project_view', project_id=project_id)
        
        Comment.objects.create(
            project=project,
            user=request.user,
            text=text or "Imagen adjunta",
            image=image
        )
        
        messages.success(request, "Comentario agregado exitosamente.")
        return redirect('client_project_view', project_id=project_id)
    
    return render(request, "core/agregar_comentario.html", {
        'project': project
    })
```

**Interfaz de Comentarios:**
```
┌────────────────────────────────────────────────────────────┐
│ 💬 COMENTARIOS - VILLA MODERNA                             │
│ [➕ Agregar Comentario]                                     │
├────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 👤 Cliente - Hoy 4:30 PM                               │ │
│ │ Me encanta cómo está quedando el dormitorio principal. │ │
│ │ El color se ve perfecto con la luz natural.           │ │
│ │ [IMAGEN: foto del dormitorio]                          │ │
│ │ [↩️ Responder] [👍 2] [📌]                             │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 👷 Admin - Hoy 3:15 PM                                 │ │
│ │ Update: Terminamos capa 2 de pintura en living room.  │ │
│ │ Mañana aplicamos capa final.                          │ │
│ │ [↩️ Responder] [👍 1]                                  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔧 Empleado Juan - Ayer 2:45 PM                        │ │
│ │ [IMAGEN: detalle de moldura]                           │ │
│ │ ¿Aplicamos sellador aquí antes de pintar?             │ │
│ │ [↩️ Responder] [✅]                                    │ │
│ │                                                        │ │
│ │   └─ 👷 Admin - Ayer 3:00 PM                          │ │
│ │      Sí, aplica sellador primero. Gracias por        │ │
│ │      preguntar.                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Ver 24 comentarios anteriores...]                         │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ AGREGAR COMENTARIO:                                        │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Escribe tu comentario aquí...                         │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│ [📎 Adjuntar Imagen] [📤 Publicar]                         │
└────────────────────────────────────────────────────────────┘
```

**Comentarios en Tareas:**
```
Comentario específico de tarea:
┌────────────────────────────────────────────────────────────┐
│ 📋 TAREA: Pintar habitación principal                      │
│ Status: En Progreso | Asignado: Juan                       │
├────────────────────────────────────────────────────────────┤
│ COMENTARIOS DE LA TAREA:                                   │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 👷 Admin - 10:30 AM                                    │ │
│ │ Recordar usar SW 7005 Pure White                      │ │
│ │ [📎 Comment attachments/color_ref.jpg]                │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔧 Juan - 2:15 PM                                      │ │
│ │ Primera capa terminada. Aplicaré segunda mañana.      │ │
│ │ [IMAGEN: progreso actual]                             │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [➕ Agregar Comentario]                                     │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Simple comment system
- ✅ Image attachments
- ✅ Task-specific comments
- ⚠️ Falta: Thread/reply nesting
- ⚠️ Falta: @mentions
- ⚠️ Falta: Reactions/likes
- ⚠️ Falta: Edit/delete comments
- ⚠️ Falta: Pin important comments
- ⚠️ Falta: Comment notifications
- ⚠️ Falta: Rich text formatting
- ⚠️ Falta: File attachments (not just images)

---

### 📌 FUNCIÓN 20.3 - Notificaciones de Comunicación

**Modelo Notification:**
```python
class Notification(models.Model):
    """Sistema de notificaciones para eventos importantes"""
    NOTIFICATION_TYPES = [
        ('task_created', 'Tarea creada'),
        ('task_assigned', 'Tarea asignada'),
        ('task_completed', 'Tarea completada'),
        ('color_review', 'Color en revisión'),
        ('color_approved', 'Color aprobado'),
        ('color_rejected', 'Color rechazado'),
        ('damage_reported', 'Daño reportado'),
        ('chat_message', 'Mensaje en chat'),
        ('comment_added', 'Comentario agregado'),
        ('estimate_approved', 'Estimación aprobada'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                            related_name='notifications')
    notification_type = models.CharField(max_length=30,
                                        choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    
    # Relación genérica opcional (project, task, color_sample, etc.)
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.IntegerField(null=True, blank=True)
    
    link_url = models.CharField(max_length=255, blank=True,
                               help_text='URL para redirigir al hacer clic')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def mark_read(self):
        """Marcar notificación como leída"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
```

**Helper Functions para Notificaciones:**
```python
# En core/notifications.py (extracto)

def notify_color_review(color_sample, changed_by):
    """Notificar cuando una muestra entra en revisión"""
    project = color_sample.project
    
    # Notificar al cliente
    if project.client:
        try:
            client_user = User.objects.get(username=project.client)
            Notification.objects.create(
                user=client_user,
                notification_type='color_review',
                title=f'Color en revisión: {color_sample.name or color_sample.code}',
                message=f'Nueva muestra de color requiere tu revisión en {project.name}',
                related_object_type='ColorSample',
                related_object_id=color_sample.id,
                link_url=f'/color-sample/{color_sample.id}/'
            )
        except User.DoesNotExist:
            pass
    
    # Notificar a PM y designer
    for role in ['project_manager', 'designer']:
        users = Profile.objects.filter(role=role).values_list('user', flat=True)
        for user_id in users:
            Notification.objects.create(
                user_id=user_id,
                notification_type='color_review',
                title=f'Color en revisión: {color_sample.name or color_sample.code}',
                message=f'{changed_by.username} movió muestra a revisión en {project.name}',
                link_url=f'/color-sample/{color_sample.id}/'
            )

def notify_color_approved(color_sample, approved_by):
    """Notificar aprobación de color"""
    project = color_sample.project
    
    # Notificar a todos los involucrados
    recipients = set()
    
    # Cliente
    if project.client:
        try:
            recipients.add(User.objects.get(username=project.client))
        except User.DoesNotExist:
            pass
    
    # Creador de la muestra
    if color_sample.created_by:
        recipients.add(color_sample.created_by)
    
    # PM y designer
    for role in ['project_manager', 'designer']:
        users = User.objects.filter(profile__role=role)
        recipients.update(users)
    
    # Remover el que aprobó
    recipients.discard(approved_by)
    
    for user in recipients:
        Notification.objects.create(
            user=user,
            notification_type='color_approved',
            title=f'✅ Color aprobado: {color_sample.name or color_sample.code}',
            message=f'{approved_by.username} aprobó la muestra en {project.name}',
            related_object_type='ColorSample',
            related_object_id=color_sample.id,
            link_url=f'/color-sample/{color_sample.id}/'
        )

def notify_chat_message(chat_message, channel):
    """Notificar nuevo mensaje en chat"""
    sender = chat_message.user
    
    # Notificar a todos los participantes excepto el sender
    for participant in channel.participants.exclude(id=sender.id):
        Notification.objects.create(
            user=participant,
            notification_type='chat_message',
            title=f'💬 Nuevo mensaje en {channel.name}',
            message=f'{sender.username}: {chat_message.message[:50]}...',
            related_object_type='ChatMessage',
            related_object_id=chat_message.id,
            link_url=f'/project/{channel.project_id}/chat/{channel.id}/'
        )
```

**Interfaz de Notificaciones:**
```
┌────────────────────────────────────────────────────────────┐
│ 🔔 NOTIFICACIONES (5 nuevas)                               │
│ [Marcar todas como leídas] [⚙️ Configuración]              │
├────────────────────────────────────────────────────────────┤
│ NUEVAS:                                                    │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 💬 Nuevo mensaje en Grupo                           │ │
│ │    Juan PM: "Equipo terminará hoy"                     │ │
│ │    Villa Moderna - Hace 5 min                          │ │
│ │    [Ver Chat] [✓ Marcar leída]                         │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 ✅ Color aprobado: SW 7005 Pure White               │ │
│ │    Admin aprobó la muestra en Villa Moderna            │ │
│ │    Hace 1 hora                                         │ │
│ │    [Ver Muestra] [✓ Marcar leída]                      │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 📋 Tarea asignada: Pintar habitación                │ │
│ │    Te asignaron una nueva tarea                        │ │
│ │    Ocean View Condo - Hace 2 horas                     │ │
│ │    [Ver Tarea] [✓ Marcar leída]                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ANTERIORES:                                                │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✔️ 💬 Nuevo comentario agregado                        │ │
│ │    Cliente agregó comentario en Villa Moderna          │ │
│ │    Ayer 4:30 PM                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✔️ 📊 Estimación aprobada                              │ │
│ │    Cliente aprobó estimado #EST-024                    │ │
│ │    Ayer 2:15 PM                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Ver todas (25)] [Configurar preferencias]                 │
└────────────────────────────────────────────────────────────┘
```

**Configuración de Notificaciones:**
```
Preferencias de Notificación:
┌────────────────────────────────────────────────────────────┐
│ Tipo de Notificación        | Email | Push | En App       │
├─────────────────────────────┼───────┼──────┼─────────────┤
│ Chat messages               │  ☐    │  ☑   │  ☑           │
│ Comentarios                 │  ☑    │  ☑   │  ☑           │
│ Tareas asignadas            │  ☑    │  ☑   │  ☑           │
│ Tareas completadas          │  ☐    │  ☐   │  ☑           │
│ Color review/approval       │  ☑    │  ☑   │  ☑           │
│ Damage reports              │  ☑    │  ☑   │  ☑           │
│ Estimados aprobados         │  ☑    │  ☐   │  ☑           │
│ Facturas                    │  ☑    │  ☐   │  ☑           │
├─────────────────────────────┴───────┴──────┴─────────────┤
│ Frecuencia de Emails:                                     │
│ ○ Inmediato  ● Diario  ○ Semanal  ○ Nunca                │
│                                                           │
│ Horario silencioso: [22:00] a [08:00]                    │
│                                                           │
│ [💾 Guardar Preferencias]                                 │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Multi-type notification system
- ✅ Generic relations para objetos
- ✅ Read/unread tracking
- ⚠️ Falta: Email notifications
- ⚠️ Falta: Push notifications
- ⚠️ Falta: User preferences por tipo
- ⚠️ Falta: Notification batching (digest)
- ⚠️ Falta: Silent hours
- ⚠️ Falta: Priority levels
- ⚠️ Falta: Notification archive
- ⚠️ Falta: Snooze notifications
- ⚠️ Falta: Desktop notifications

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 20**

### Mejoras CRÍTICAS:
1. 🔴 **Real-Time Communication**
   - WebSocket implementation para chat
   - Typing indicators
   - Read receipts
   - Online status indicators
   - Delivery confirmations

2. 🔴 **Notification System Enhancement**
   - Email notifications
   - Push notifications (mobile/desktop)
   - User preferences por tipo
   - Silent hours / Do Not Disturb
   - Batching/digest mode

3. 🔴 **Advanced Chat Features**
   - Thread/reply system
   - Message reactions/emojis
   - @mention notifications
   - Search/filter messages
   - File attachments (PDFs, docs, etc.)

### Mejoras Importantes:
4. ⚠️ Voice messages en chat
5. ⚠️ Video call integration
6. ⚠️ Screen sharing
7. ⚠️ Comment editing/deletion
8. ⚠️ Pin important messages/comments
9. ⚠️ Rich text formatting (bold, italic, links)
10. ⚠️ Message translation (multi-language)
11. ⚠️ Notification snooze
12. ⚠️ Priority notification levels
13. ⚠️ Notification archive
14. ⚠️ Scheduled messages
15. ⚠️ Auto-delete old messages

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)
- ✅ Módulo 12: Planes Diarios (14/14) ⭐ CRÍTICO
- ✅ Módulo 13: SOPs/Plantillas (5/5)
- ✅ Módulo 14: Minutas/Timeline (3/3)
- ✅ Módulo 15: RFIs, Issues & Risks (6/6)
- ✅ Módulo 16: Solicitudes (Material & Cliente) (4/4)
- ✅ Módulo 17: Fotos & Floor Plans (5/5)
- ✅ Módulo 18: Inventory (3/3)
- ✅ Módulo 19: Color Samples & Design Chat (6/6)
- ✅ Módulo 20: Communication (Chat & Comments) (3/3)

**Total documentado: 170/250+ funciones (68%)** 🎉

**Pendientes:**
- ⏳ Módulos 22-27: 79+ funciones

---

## ✅ **MÓDULO 21: DASHBOARDS (ADMIN, PM, EMPLOYEE, CLIENT, DESIGNER, SUPERINTENDENT)** (6/6 COMPLETO)

### 📌 FUNCIÓN 21.1 - Dashboard Admin (Command Center)

**Vista dashboard_admin:**
```python
@login_required
def dashboard_admin(request):
    """Dashboard completo para Admin con todas las métricas, alertas y aprobaciones"""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Acceso solo para Admin/Staff.")
        return redirect('dashboard')
    
    # === MÉTRICAS FINANCIERAS ===
    total_income = Income.objects.aggregate(t=Sum("amount"))["t"] or Decimal('0')
    total_expense = Expense.objects.aggregate(t=Sum("amount"))["t"] or Decimal('0')
    net_profit = total_income - total_expense
    
    # === ALERTAS CRÍTICAS ===
    # 1. TimeEntries sin CO asignar
    unassigned_time_count = TimeEntry.objects.filter(
        change_order__isnull=True
    ).count()
    unassigned_time_hours = TimeEntry.objects.filter(
        change_order__isnull=True
    ).aggregate(total=Sum('hours_worked'))['total'] or Decimal('0')
    
    # 2. Solicitudes Cliente pendientes
    pending_client_requests = ClientRequest.objects.filter(
        status='pending'
    ).count()
    
    # 3. Nómina pendiente (periodos aprobados pero no pagados)
    pending_payroll = PayrollPeriod.objects.filter(
        status='approved'
    ).exclude(records__payments__isnull=False).distinct().count()
    
    # 4. Facturas pendientes de pago
    pending_invoices = Invoice.objects.filter(
        status__in=['SENT', 'VIEWED', 'APPROVED', 'PARTIAL']
    ).count()
    pending_invoice_amount = Invoice.objects.filter(
        status__in=['SENT', 'VIEWED', 'APPROVED', 'PARTIAL']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # 5. COs pendientes de aprobación
    pending_cos = ChangeOrder.objects.filter(status='pending').count()
    
    # === PROYECTOS CON ALERTAS EV ===
    today = timezone.localdate()
    projects_with_alerts = []
    
    for project in Project.objects.filter(end_date__isnull=True).order_by('name'):
        try:
            metrics = compute_project_ev(project, as_of=today)
            alerts = []
            
            # SPI < 0.9: retraso en cronograma
            if metrics and metrics.get('SPI') and metrics['SPI'] < 0.9:
                alerts.append(('danger', f"Retraso crítico (SPI: {metrics['SPI']})"))
            elif metrics and metrics.get('SPI') and metrics['SPI'] < 1.0:
                alerts.append(('warning', f"Leve retraso (SPI: {metrics['SPI']})"))
            
            # CPI < 0.9: sobrecosto
            if metrics and metrics.get('CPI') and metrics['CPI'] < 0.9:
                alerts.append(('danger', f"Sobrecosto crítico (CPI: {metrics['CPI']})"))
            elif metrics and metrics.get('CPI') and metrics['CPI'] < 1.0:
                alerts.append(('warning', f"Leve sobrecosto (CPI: {metrics['CPI']})"))
            
            # Presupuesto casi agotado
            if project.budget_total > 0:
                remaining_pct = (project.budget_remaining / project.budget_total) * 100
                if remaining_pct < 10:
                    alerts.append(('danger', 
                                  f"Presupuesto crítico ({remaining_pct:.1f}% restante)"))
                elif remaining_pct < 20:
                    alerts.append(('warning', 
                                  f"Presupuesto bajo ({remaining_pct:.1f}% restante)"))
            
            if alerts:
                projects_with_alerts.append({
                    'project': project,
                    'alerts': alerts,
                    'metrics': metrics
                })
        except Exception:
            pass
    
    # === APROBACIONES PENDIENTES ===
    pending_cos_list = ChangeOrder.objects.filter(
        status='pending'
    ).select_related('project')[:10]
    
    # Context completo
    context = {
        # Financiero
        'total_income': total_income,
        'total_expense': total_expense,
        'net_profit': net_profit,
        
        # Alertas
        'unassigned_time_count': unassigned_time_count,
        'unassigned_time_hours': unassigned_time_hours,
        'pending_client_requests': pending_client_requests,
        'pending_payroll': pending_payroll,
        'pending_invoices': pending_invoices,
        'pending_invoice_amount': pending_invoice_amount,
        'pending_cos': pending_cos,
        
        # Proyectos
        'projects_with_alerts': projects_with_alerts,
        'pending_cos_list': pending_cos_list,
    }
    
    return render(request, "core/dashboard_admin.html", context)
```

**Interfaz Dashboard Admin:**
```
┌────────────────────────────────────────────────────────────┐
│ 📊 ADMIN DASHBOARD - COMMAND CENTER                        │
│ Usuario: Admin | Fecha: Aug 25, 2025                       │
├────────────────────────────────────────────────────────────┤
│ 💰 FINANZAS GLOBALES:                                      │
│ ┌──────────────┬──────────────┬──────────────┐             │
│ │ Ingresos     │ Gastos       │ Ganancia     │             │
│ │ $245,000     │ $178,500     │ $66,500      │             │
│ │ 100%         │ 72.9%        │ 27.1%        │             │
│ └──────────────┴──────────────┴──────────────┘             │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 🚨 ALERTAS CRÍTICAS (7):                                   │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 Tiempo sin CO: 48 horas (12 entradas) [ASIGNAR]    │ │
│ │ 🔴 Facturas pendientes: 8 ($125,400) [VER]            │ │
│ │ 🟡 Nómina por pagar: 2 periodos [VER]                 │ │
│ │ 🟡 Solicitudes cliente: 5 pendientes [REVISAR]        │ │
│ │ 🟡 Change Orders: 3 sin aprobar [APROBAR]             │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ ⚠️ PROYECTOS CON ALERTAS EV (3):                          │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 VILLA MODERNA                                       │ │
│ │    • Sobrecosto crítico (CPI: 0.85)                   │ │
│ │    • Presupuesto crítico (8% restante)                │ │
│ │    EV: $45,200 | AC: $53,100 | Varianza: -$7,900     │ │
│ │    [Ver Detalles] [Plan de Acción]                    │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟡 OCEAN VIEW CONDO                                    │ │
│ │    • Leve retraso (SPI: 0.92)                         │ │
│ │    EV: $28,400 | PV: $30,870 | Varianza: -$2,470     │ │
│ │    [Ver Detalles]                                      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 📋 APROBACIONES PENDIENTES:                                │
│ • CO-045: Villa Moderna - Molduras adicionales ($2,400)   │
│ • CO-046: Beach House - Cambio de color ($800)            │
│ • CO-047: Downtown Loft - Textura extra ($1,200)          │
│ [Ver Todas (3)] [Aprobar en Lote]                         │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 🔗 ACCIONES RÁPIDAS:                                       │
│ [Asignar Tiempo] [Revisar Solicitudes] [Aprobar COs]      │
│ [Procesar Nómina] [Gestionar Facturas] [Reportes]         │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Comprehensive financial overview
- ✅ Multi-level alerts (crítico/warning)
- ✅ EV metrics per project
- ✅ Quick access to pending approvals
- ⚠️ Falta: Real-time data updates
- ⚠️ Falta: Customizable widgets
- ⚠️ Falta: Drill-down analytics
- ⚠️ Falta: Export dashboard to PDF
- ⚠️ Falta: Trend graphs (revenue over time)
- ⚠️ Falta: Predictive analytics (forecast)

---

### 📌 FUNCIÓN 21.2 - Dashboard PM (Operational Center)

**Vista dashboard_pm:**
```python
@login_required
def dashboard_pm(request):
    """Dashboard operacional para PM: materiales, planning, issues, tiempo sin CO"""
    if not request.user.is_staff:
        messages.error(request, "Acceso solo para PM/Staff.")
        return redirect("dashboard_employee")

    # Language preference handling
    show_language_prompt = False
    prof = getattr(request.user, 'profile', None)
    if prof:
        if getattr(prof, 'language', None):
            if request.session.get('lang') != prof.language:
                request.session['lang'] = prof.language
                translation.activate(prof.language)
        else:
            show_language_prompt = True

    today = timezone.localdate()
    
    # === ALERTAS OPERACIONALES ===
    unassigned_time_count = TimeEntry.objects.filter(
        change_order__isnull=True
    ).count()
    pending_materials = MaterialRequest.objects.filter(
        status__in=['pending', 'submitted']
    ).count()
    open_issues = Issue.objects.filter(
        status__in=['open', 'in_progress']
    ).count()
    open_rfis = RFI.objects.filter(status='open').count()
    today_plans = DailyPlan.objects.filter(date=today).count()
    
    # === MATERIALES PENDIENTES (top 10) ===
    pending_materials_list = MaterialRequest.objects.filter(
        status__in=['pending', 'submitted']
    ).select_related('project', 'requested_by').order_by('-created_at')[:10]
    
    # === ISSUES ACTIVOS (top 10) ===
    active_issues = Issue.objects.filter(
        status__in=['open', 'in_progress']
    ).select_related('project').order_by('-created_at')[:10]
    
    # === RFIs ABIERTOS ===
    active_rfis = RFI.objects.filter(
        status='open'
    ).select_related('project').order_by('-created_at')[:10]
    
    # === TIEMPO HOY POR PROYECTO ===
    entries_today = TimeEntry.objects.filter(
        date=today
    ).select_related('employee', 'project')
    hours_by_project = {}
    for entry in entries_today:
        if entry.project:
            proj_name = entry.project.name
            if proj_name not in hours_by_project:
                hours_by_project[proj_name] = Decimal('0')
            hours_by_project[proj_name] += Decimal(entry.hours_worked or 0)
    
    # === PROYECTOS CON PROGRESO ===
    active_projects = Project.objects.filter(
        end_date__isnull=True
    ).order_by('name')
    project_summary = []
    for project in active_projects:
        try:
            metrics = compute_project_ev(project, as_of=today)
            progress_pct = 0
            if metrics and metrics.get('PV') and metrics['PV'] > 0:
                progress_pct = min(100, (metrics.get('EV', 0) / metrics['PV']) * 100)
        except Exception:
            progress_pct = 0
        
        project_summary.append({
            'project': project,
            'progress_pct': int(progress_pct),
            'hours_today': hours_by_project.get(project.name, 0),
        })

    context = {
        'unassigned_time_count': unassigned_time_count,
        'pending_materials': pending_materials,
        'open_issues': open_issues,
        'open_rfis': open_rfis,
        'today_plans': today_plans,
        'pending_materials_list': pending_materials_list,
        'active_issues': active_issues,
        'active_rfis': active_rfis,
        'project_summary': project_summary,
        'today': today,
        'show_language_prompt': show_language_prompt,
    }
    
    return render(request, "core/dashboard_pm.html", context)
```

**Interfaz Dashboard PM:**
```
┌────────────────────────────────────────────────────────────┐
│ 👷 PM DASHBOARD - OPERATIONAL CENTER                       │
│ Usuario: Juan PM | Fecha: Aug 25, 2025                     │
├────────────────────────────────────────────────────────────┤
│ 📊 ALERTAS OPERACIONALES:                                  │
│ ┌──────────────┬──────────────┬──────────────┬───────────┐ │
│ │ ⏱️ Sin CO    │ 📦 Materiales│ ⚠️ Issues    │ ❓ RFIs   │ │
│ │ 12 entradas  │ 4 pedidos    │ 3 abiertos   │ 2 abiertos│ │
│ │ [ASIGNAR]    │ [PROCESAR]   │ [REVISAR]    │ [RESPOND] │ │
│ └──────────────┴──────────────┴──────────────┴───────────┘ │
│                                                            │
│ 📅 DAILY PLANS HOY: 5 planes activos [VER TODOS]          │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 📦 MATERIALES PENDIENTES (4):                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 URGENTE: Paint - Interior White | Villa Moderna     │ │
│ │    Pedido por: Juan | Urgencia: NOW                    │ │
│ │    [Aprobar] [Comprar] [Detalle]                       │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟡 Roller Covers 9" | Ocean View Condo                 │ │
│ │    Pedido por: Mike | Urgencia: TOMORROW               │ │
│ │    [Aprobar] [Detalle]                                 │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ ⚠️ ISSUES ACTIVOS (3):                                     │
│ • ISS-012: Color no coincide con muestra (HIGH) - Villa   │
│ • ISS-013: Superficie irregular (MEDIUM) - Ocean View     │
│ • ISS-014: Falta material (LOW) - Beach House             │
│ [Ver Todos] [Crear Issue]                                 │
│                                                            │
│ ❓ RFIs ABIERTOS (2):                                      │
│ • RFI-008: ¿Acabado para molduras? - Villa Moderna        │
│ • RFI-009: Confirmación de color techo - Downtown Loft    │
│ [Responder] [Ver Todos]                                    │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 🏗️ PROYECTOS ACTIVOS:                                     │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Villa Moderna          | Progreso: 72% | Hoy: 16 hrs   │ │
│ │ [████████████░░░░░░]   | Budget: $45,200/$60,000      │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Ocean View Condo       | Progreso: 45% | Hoy: 8 hrs    │ │
│ │ [████████░░░░░░░░░░]   | Budget: $18,500/$40,000      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Ver Todos los Proyectos] [Reportes] [Planning]           │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Operational focus (materials, issues, RFIs)
- ✅ Today's work summary
- ✅ Quick actions for urgent items
- ⚠️ Falta: Gantt view of projects
- ⚠️ Falta: Team capacity planning
- ⚠️ Falta: Weather alerts (outdoor work)
- ⚠️ Falta: Material ETA tracking
- ⚠️ Falta: Mobile-optimized view

---

### 📌 FUNCIÓN 21.3 - Dashboard Employee (Daily Work)

**Vista dashboard_employee:**
```python
@login_required
def dashboard_employee(request):
    """Dashboard simple para empleados: qué hacer hoy, clock in/out, materiales"""
    employee = Employee.objects.filter(user=request.user).first()
    if not employee:
        messages.error(request, "Tu usuario no está vinculado a un empleado.")
        return render(request, "core/dashboard_employee.html", {"employee": None})

    today = timezone.localdate()
    now = timezone.localtime()
    
    # TimeEntry abierto (si está trabajando)
    open_entry = TimeEntry.objects.filter(
        employee=employee,
        end_time__isnull=True
    ).order_by("-date", "-start_time").first()
    
    # Touch-ups asignados
    my_touchups = Task.objects.filter(
        assigned_to=request.user,
        is_touchup=True,
        status__in=['Pendiente', 'En Progreso']
    ).select_related('project').order_by('-created_at')[:10]

    # === QUÉ HACER HOY (Daily Plan Activities) ===
    today_plans = DailyPlan.objects.filter(
        date=today,
        assigned_employees=employee
    ).select_related('project').prefetch_related('planned_activities')
    
    my_activities = []
    for plan in today_plans:
        for activity in plan.planned_activities.filter(is_completed=False):
            my_activities.append({
                'activity': activity,
                'project': plan.project,
            })
    
    # === SCHEDULE ASIGNADO HOY ===
    my_schedule = Schedule.objects.filter(
        assigned_to=request.user,
        start_datetime__date=today
    ).select_related('project').order_by('start_datetime')

    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "clock_in":
            if open_entry:
                messages.warning(request,
                               "Ya tienes una entrada abierta. Marca salida primero.")
                return redirect("dashboard_employee")
            form = ClockInForm(request.POST)
            if form.is_valid():
                TimeEntry.objects.create(
                    employee=employee,
                    project=form.cleaned_data["project"],
                    date=today,
                    start_time=now.time(),
                    end_time=None,
                    notes=form.cleaned_data.get("notes") or "",
                    cost_code=form.cleaned_data.get("cost_code"),
                )
                messages.success(request,
                               f"✓ Entrada registrada a las {now.strftime('%H:%M')}.")
                return redirect("dashboard_employee")
                
        elif action == "clock_out":
            if not open_entry:
                messages.warning(request, "No tienes una entrada abierta.")
                return redirect("dashboard_employee")
            open_entry.end_time = now.time()
            open_entry.save()
            messages.success(request,
                           f"✓ Salida registrada a las {now.strftime('%H:%M')}. "
                           f"Horas: {open_entry.hours_worked}")
            return redirect("dashboard_employee")

    # GET o POST inválido
    form = ClockInForm()
    
    # Historial reciente
    recent = TimeEntry.objects.filter(
        employee=employee
    ).order_by("-date", "-start_time")[:5]
    
    # Horas de la semana
    week_start = today - timedelta(days=today.weekday())
    week_entries = TimeEntry.objects.filter(
        employee=employee,
        date__gte=week_start,
        date__lte=today
    )
    week_hours = sum(entry.hours_worked or 0 for entry in week_entries)
    
    context = {
        'employee': employee,
        'open_entry': open_entry,
        'my_touchups': my_touchups,
        'my_activities': my_activities,
        'my_schedule': my_schedule,
        'form': form,
        'recent': recent,
        'week_hours': week_hours,
        'today': today,
    }
    
    return render(request, "core/dashboard_employee.html", context)
```

**Interfaz Dashboard Employee:**
```
┌────────────────────────────────────────────────────────────┐
│ 👷 EMPLOYEE DASHBOARD - QUÉ HACER HOY                      │
│ Usuario: Juan Pérez | Fecha: Aug 25, 2025                  │
├────────────────────────────────────────────────────────────┤
│ ⏱️ CLOCK IN/OUT:                                           │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ⏰ Ahora: 10:45 AM                                     │ │
│ │ Status: 🟢 TRABAJANDO                                  │ │
│ │ Entrada: 7:30 AM en Villa Moderna                     │ │
│ │ Horas acumuladas hoy: 3.25 hrs                        │ │
│ │                                                        │ │
│ │ [⏸️ CLOCK OUT]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Esta semana: 32.5 hrs (de 40 hrs esperadas)               │
│ [████████████████░░░░] 81%                                 │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 📋 QUÉ HACER HOY (5 actividades):                          │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ☐ PREP - Cubrir muebles y pisos                       │ │
│ │   Villa Moderna | 8:00 AM - 9:00 AM                   │ │
│ │   Materiales: Plastic covers, tape                     │ │
│ │   [✓ Marcar Completado] [Ver Detalle]                 │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ☑️ PAINT - Primera capa habitación principal          │ │
│ │   Villa Moderna | 9:00 AM - 12:00 PM                  │ │
│ │   Materiales: SW 7005 (2 gal), rollers, brushes       │ │
│ │   ✓ Completado a las 11:45 AM                         │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ☐ PAINT - Segunda capa habitación principal           │ │
│ │   Villa Moderna | 1:00 PM - 4:00 PM                   │ │
│ │   Materiales: SW 7005 (2 gal)                         │ │
│ │   [✓ Marcar Completado]                               │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 🔧 TOUCH-UPS ASIGNADOS (2):                                │
│ • Corregir goteo en pared living room - Villa Moderna     │
│ • Retocar esquina bathroom - Ocean View Condo             │
│ [Ver Todos]                                                │
│                                                            │
│ 📅 MI SCHEDULE HOY:                                        │
│ • 7:30 AM - 4:00 PM: Villa Moderna                        │
│                                                            │
│ 📊 HISTORIAL RECIENTE:                                     │
│ • Ayer: 8.0 hrs - Villa Moderna                           │
│ • Viernes: 7.5 hrs - Ocean View Condo                     │
│ • Jueves: 8.0 hrs - Villa Moderna                         │
│                                                            │
│ [Ver Historial Completo] [Reportar Problema]               │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Simple clock in/out
- ✅ Today's activities from daily plan
- ✅ Touch-ups tracking
- ✅ Week hours summary
- ⚠️ Falta: GPS location verification
- ⚠️ Falta: Photo upload for completed work
- ⚠️ Falta: Break time tracking
- ⚠️ Falta: Material request from dashboard
- ⚠️ Falta: Offline mode (PWA)

---

### 📌 FUNCIÓN 21.4 - Dashboard Cliente (Project Visibility)

**Vista dashboard_client:**
```python
@login_required
def dashboard_client(request):
    """Dashboard visual para clientes con progreso, fotos, facturas"""
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'client':
        messages.error(request, "Acceso solo para clientes.")
        return redirect('dashboard')
    
    # Proyectos del cliente
    from core.models import ClientProjectAccess
    access_projects = Project.objects.filter(
        client_accesses__user=request.user
    )
    legacy_projects = Project.objects.filter(
        client=request.user.username
    )
    projects = (
        access_projects.union(legacy_projects)
        .order_by('-start_date')
    )
    
    # Para cada proyecto, calcular métricas visuales
    project_data = []
    for project in projects:
        # Facturas
        invoices = project.invoices.all().order_by('-date_issued')[:5]
        total_invoiced = invoices.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')
        total_paid = invoices.aggregate(
            paid=Sum('amount_paid')
        )['paid'] or Decimal('0')
        
        # Progreso (usando EV si disponible)
        progress_pct = 0
        try:
            metrics = compute_project_ev(project)
            if metrics and metrics.get('PV') and metrics['PV'] > 0:
                progress_pct = min(100, (metrics.get('EV', 0) / metrics['PV']) * 100)
        except Exception:
            # Fallback: progreso basado en fechas
            if project.start_date and project.end_date:
                total_days = (project.end_date - project.start_date).days
                elapsed_days = (timezone.localdate() - project.start_date).days
                progress_pct = min(100,
                                 (elapsed_days / total_days * 100)
                                 ) if total_days > 0 else 0
        
        # Fotos recientes
        recent_photos = SitePhoto.objects.filter(
            project=project
        ).order_by('-created_at')[:6]
        
        # Schedule próximo
        next_schedule = Schedule.objects.filter(
            project=project,
            start_datetime__gte=timezone.now()
        ).order_by('start_datetime').first()
        
        # Solicitudes cliente
        client_requests = ClientRequest.objects.filter(
            project=project
        ).order_by('-created_at')[:5]
        
        project_data.append({
            'project': project,
            'invoices': invoices,
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'balance': total_invoiced - total_paid,
            'progress_pct': int(progress_pct),
            'recent_photos': recent_photos,
            'next_schedule': next_schedule,
            'client_requests': client_requests,
        })
    
    return render(request, "core/dashboard_client.html", {
        'project_data': project_data,
    })
```

**Interfaz Dashboard Cliente:**
```
┌────────────────────────────────────────────────────────────┐
│ 🏠 CLIENT DASHBOARD - MIS PROYECTOS                        │
│ Cliente: John Smith | Bienvenido                           │
├────────────────────────────────────────────────────────────┤
│ VILLA MODERNA:                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📊 PROGRESO: 72%                                       │ │
│ │ [████████████████░░░░] 72% completado                  │ │
│ │                                                        │ │
│ │ Inicio: Jul 1, 2025 | Fin estimado: Sep 15, 2025      │ │
│ │ Tiempo restante: 21 días                              │ │
│ │                                                        │ │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │ │
│ │                                                        │ │
│ │ 💰 FINANCIERO:                                         │ │
│ │ Total contratado: $60,000                             │ │
│ │ Facturado: $45,200                                    │ │
│ │ Pagado: $38,500                                       │ │
│ │ Balance pendiente: $6,700                             │ │
│ │ [💳 Pagar Ahora] [Ver Facturas]                       │ │
│ │                                                        │ │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │ │
│ │                                                        │ │
│ │ 📸 FOTOS RECIENTES (6):                                │ │
│ │ [IMG1] [IMG2] [IMG3] [IMG4] [IMG5] [IMG6]             │ │
│ │ [Ver Galería Completa (48 fotos)]                     │ │
│ │                                                        │ │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │ │
│ │                                                        │ │
│ │ 📅 PRÓXIMA VISITA:                                     │ │
│ │ Mañana - Aug 26, 2025 a las 2:00 PM                  │ │
│ │ "Final walkthrough habitaciones"                      │ │
│ │ [Confirmar] [Reagendar]                               │ │
│ │                                                        │ │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │ │
│ │                                                        │ │
│ │ 💬 MIS SOLICITUDES (2):                                │ │
│ │ • Cambiar color baño principal (PENDING)              │ │
│ │ • Agregar moldura living room (APPROVED → CO-045)     │ │
│ │ [Nueva Solicitud] [Ver Todas]                         │ │
│ │                                                        │ │
│ │ [💬 Chat con PM] [📊 Ver Detalles] [⚙️ Opciones]      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ OCEAN VIEW CONDO:                                          │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📊 PROGRESO: 45%                                       │ │
│ │ [████████████░░░░░░░░░░░░] 45% completado             │ │
│ │ ...                                                    │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Ver Todos mis Proyectos (2)]                              │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Visual progress tracking
- ✅ Photo gallery
- ✅ Invoice/payment summary
- ✅ Schedule visibility
- ✅ Request tracking
- ⚠️ Falta: 3D visualization/virtual tour
- ⚠️ Falta: Mobile app notifications
- ⚠️ Falta: Online payment integration
- ⚠️ Falta: Video updates from team
- ⚠️ Falta: Milestone celebrations

---

### 📌 FUNCIÓN 21.5 - Dashboard Designer (Creative View)

**Vista dashboard_designer:**
```python
@login_required
def dashboard_designer(request):
    """Dashboard for designers - read-only access to projects, plans,
    color samples, chat."""
    from django.db import models as db_models
    
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'designer':
        return HttpResponseForbidden("Acceso restringido a diseñadores")
    
    # Projects the designer is involved with
    projects = Project.objects.filter(
        db_models.Q(color_samples__isnull=False) |
        db_models.Q(design_documents__isnull=False) |
        db_models.Q(chat_channels__participants=request.user)
    ).distinct().order_by('-created_at')[:10]
    
    # Recent color samples
    color_samples = ColorSample.objects.filter(
        project__in=projects
    ).select_related('project').order_by('-created_at')[:15]
    
    # Floor plans
    plans = FloorPlan.objects.filter(
        project__in=projects
    ).select_related('project').order_by('-uploaded_at')[:10]
    
    # Recent schedules
    schedules = Schedule.objects.filter(
        project__in=projects
    ).select_related('project').order_by('-start_datetime')[:10]
    
    return render(request, 'core/dashboard_designer.html', {
        'projects': projects,
        'color_samples': color_samples,
        'plans': plans,
        'schedules': schedules,
    })
```

**Interfaz Dashboard Designer:**
```
┌────────────────────────────────────────────────────────────┐
│ 🎨 DESIGNER DASHBOARD                                      │
│ Designer: Maria Rodriguez                                  │
├────────────────────────────────────────────────────────────┤
│ 🎨 COLOR SAMPLES EN REVISIÓN (8):                          │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [IMG] SW 7005 - Pure White                             │ │
│ │       Villa Moderna | Propuesto ayer                   │ │
│ │       [Ver Detalle] [Chat con Cliente]                 │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [IMG] BM 2124-70 - Cloud White                         │ │
│ │       Ocean View Condo | En Revisión (2 días)          │ │
│ │       [Ver Detalle] [Subir Variante]                   │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Ver Todas (15)] [Crear Nueva Muestra]                     │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 📐 FLOOR PLANS RECIENTES (5):                              │
│ • Villa Moderna - Main Level (3 pins)                     │
│ • Ocean View Condo - Living Room (5 pins)                 │
│ • Beach House - Master Bedroom (2 pins)                   │
│ [Ver Todos] [Subir Nuevo Plan]                             │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 🏗️ MIS PROYECTOS (8):                                     │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Villa Moderna | Progreso: 72%                          │ │
│ │ • 5 color samples (3 aprobados)                        │ │
│ │ • 2 floor plans                                        │ │
│ │ • Última actividad: Hoy 10:30 AM                      │ │
│ │ [Design Chat] [Ver Proyecto]                           │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 📅 PRÓXIMAS VISITAS/MEETINGS:                              │
│ • Mañana 10:00 AM - Color selection @ Villa Moderna       │
│ • Viernes 2:00 PM - Final walkthrough @ Ocean View        │
│                                                            │
│ [Mi Calendario] [Crear Paleta] [Biblioteca de Colores]    │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Read-only project access
- ✅ Color sample workflow
- ✅ Floor plan management
- ⚠️ Falta: Mood board creation
- ⚠️ Falta: Color palette generator
- ⚠️ Falta: Design library/inspiration
- ⚠️ Falta: Client presentation mode
- ⚠️ Falta: AR visualization tools

---

### 📌 FUNCIÓN 21.6 - Dashboard Superintendent (Quality Control)

**Vista dashboard_superintendent:**
```python
@login_required
def dashboard_superintendent(request):
    """Dashboard for superintendents - manage damage reports,
    touch-ups, task assignments."""
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'superintendent':
        return HttpResponseForbidden("Acceso restringido a superintendentes")
    
    # Projects assigned to this superintendent
    project_ids = set()
    
    # Via damage reports
    damage_projects = DamageReport.objects.values_list(
        'project_id',
        flat=True
    ).distinct()
    project_ids.update(damage_projects)
    
    # Via assigned touch-ups
    touchup_projects = Task.objects.filter(
        assigned_to=request.user,
        is_touchup=True
    ).values_list('project_id', flat=True).distinct()
    project_ids.update(touchup_projects)
    
    projects = Project.objects.filter(
        id__in=project_ids
    ).order_by('-created_at')[:10]
    
    # Open damage reports
    damages = DamageReport.objects.filter(
        project__in=projects,
        status__in=['reported', 'in_repair']
    ).select_related('project', 'reported_by').order_by('-created_at')[:15]
    
    # Assigned touch-ups
    touchups = Task.objects.filter(
        assigned_to=request.user,
        is_touchup=True,
        status__in=['Pendiente', 'En Progreso']
    ).select_related('project').order_by('-created_at')[:15]
    
    # Unassigned touch-ups (for assignment)
    unassigned_touchups = Task.objects.filter(
        is_touchup=True,
        assigned_to__isnull=True,
        status='Pendiente'
    ).select_related('project').order_by('-created_at')[:10]
    
    return render(request, 'core/dashboard_superintendent.html', {
        'projects': projects,
        'damages': damages,
        'touchups': touchups,
        'unassigned_touchups': unassigned_touchups,
    })
```

**Interfaz Dashboard Superintendent:**
```
┌────────────────────────────────────────────────────────────┐
│ 🔍 SUPERINTENDENT DASHBOARD - QUALITY CONTROL              │
│ Superintendent: Mike Johnson                               │
├────────────────────────────────────────────────────────────┤
│ ⚠️ DAMAGE REPORTS ACTIVOS (5):                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 HIGH: Scratch on cabinet door                       │ │
│ │    Villa Moderna | Reportado por: Cliente             │ │
│ │    Status: IN_REPAIR | Hace 2 días                    │ │
│ │    [Ver Detalle] [Asignar Touch-up] [Resolver]        │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟡 MEDIUM: Paint drip on wall                          │ │
│ │    Ocean View Condo | Reportado por: PM               │ │
│ │    Status: REPORTED | Hace 1 hora                     │ │
│ │    [Ver Fotos (3)] [Asignar] [Detalle]                │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Ver Todos (5)] [Crear Reporte]                            │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 🔧 TOUCH-UPS ASIGNADOS A MÍ (8):                           │
│ • Corregir esquina bathroom - Villa Moderna (PENDIENTE)   │
│ • Retocar moldura - Ocean View Condo (EN PROGRESO)        │
│ • Limpiar exceso caulk - Beach House (PENDIENTE)          │
│ [Ver Todos] [Marcar Completado]                            │
│                                                            │
│ 🔧 TOUCH-UPS SIN ASIGNAR (3):                              │
│ • Pintura irregular pared - Downtown Loft                 │
│ • Color mismatch puerta - Villa Moderna                   │
│ • Falta sellador - Beach House                            │
│ [Asignar a Empleado] [Tomar Asignación]                    │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 🏗️ MIS PROYECTOS (8):                                     │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Villa Moderna                                          │ │
│ │ • 2 damages activos                                    │ │
│ │ • 3 touch-ups pendientes                               │ │
│ │ • Última inspección: Ayer                              │ │
│ │ [Inspeccionar] [Reportes] [Ver Detalle]               │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ 📊 ESTADÍSTICAS:                                           │
│ • Esta semana: 12 damages resueltos                       │
│ • Touch-ups completados: 24                               │
│ • Tasa de resolución: 94%                                 │
│                                                            │
│ [Programar Inspección] [Reporte Semanal] [Configuración]  │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Damage report tracking
- ✅ Touch-up assignment
- ✅ Quality control focus
- ⚠️ Falta: Inspection checklist system
- ⚠️ Falta: Quality metrics dashboard
- ⚠️ Falta: Photo comparison (before/after)
- ⚠️ Falta: Client approval workflow
- ⚠️ Falta: Warranty tracking

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 21**

### Mejoras CRÍTICAS:
1. 🔴 **Real-Time Updates**
   - WebSocket para datos en vivo
   - Auto-refresh dashboards
   - Live notifications
   - Activity streams

2. 🔴 **Customization**
   - Draggable widgets
   - User-defined layouts
   - Saved dashboard views
   - Role-based widget library

3. 🔴 **Analytics Enhancement**
   - Trend graphs (revenue, hours, costs)
   - Predictive analytics
   - Drill-down capabilities
   - Export to PDF/Excel

### Mejoras Importantes:
4. ⚠️ Mobile-optimized dashboards
5. ⚠️ Offline mode (PWA) for employees
6. ⚠️ GPS location verification
7. ⚠️ Weather alerts for outdoor work
8. ⚠️ 3D visualization for clients
9. ⚠️ Online payment integration
10. ⚠️ Video updates from team
11. ⚠️ AR visualization tools for designers
12. ⚠️ Mood board creation
13. ⚠️ Inspection checklist system
14. ⚠️ Quality metrics tracking
15. ⚠️ Photo comparison tools

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)
- ✅ Módulo 12: Planes Diarios (14/14) ⭐ CRÍTICO
- ✅ Módulo 13: SOPs/Plantillas (5/5)
- ✅ Módulo 14: Minutas/Timeline (3/3)
- ✅ Módulo 15: RFIs, Issues & Risks (6/6)
- ✅ Módulo 16: Solicitudes (Material & Cliente) (4/4)
- ✅ Módulo 17: Fotos & Floor Plans (5/5)
- ✅ Módulo 18: Inventory (3/3)
- ✅ Módulo 19: Color Samples & Design Chat (6/6)
- ✅ Módulo 20: Communication (Chat & Comments) (3/3)
- ✅ Módulo 21: Dashboards (Admin, PM, Employee, Client, Designer, Superintendent) (6/6) ⭐ CRÍTICO

**Total documentado: 176/250+ funciones (70%)** 🎉

**Pendientes:**
- ⏳ Módulos 23-27: 76+ funciones

---

## ✅ **MÓDULO 22: PAYROLL (NÓMINA SEMANAL)** (3/3 COMPLETO)

### 📌 FUNCIÓN 22.1 - Revisión y Aprobación Semanal de Nómina

**Modelo PayrollPeriod:**
```python
class PayrollPeriod(models.Model):
    """Período de nómina semanal para revisión y aprobación"""
    week_start = models.DateField()
    week_end = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Borrador'),
        ('under_review', 'En Revisión'),
        ('approved', 'Aprobado'),
        ('paid', 'Pagado'),
    ], default='draft')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-week_start']
        unique_together = ['week_start', 'week_end']

    def total_payroll(self):
        """Calcula el total de la nómina para todos los empleados"""
        return sum(record.total_pay for record in self.records.all())

    def total_paid(self):
        """Calcula cuánto se ha pagado de esta nómina"""
        return sum(payment.amount 
                  for record in self.records.all() 
                  for payment in record.payments.all())

    def balance_due(self):
        """Calcula cuánto falta por pagar"""
        return self.total_payroll() - self.total_paid()
```

**Modelo PayrollRecord:**
```python
class PayrollRecord(models.Model):
    """Registro individual de nómina por empleado por semana"""
    period = models.ForeignKey(PayrollPeriod, related_name='records',
                              on_delete=models.CASCADE, null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    week_start = models.DateField()
    week_end = models.DateField()
    
    # Campos calculados pero editables
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    adjusted_rate = models.DecimalField(max_digits=8, decimal_places=2,
                                       null=True, blank=True,
                                       help_text="Tasa ajustada para esta semana (override)")
    total_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Estado y notas
    reviewed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['week_start', 'employee__last_name']

    def effective_rate(self):
        """Retorna la tasa efectiva (ajustada o normal)"""
        return self.adjusted_rate if self.adjusted_rate else self.hourly_rate

    def calculate_total_pay(self):
        """Calcula el total a pagar"""
        return self.total_hours * self.effective_rate()

    def amount_paid(self):
        """Suma de todos los pagos hechos a este registro"""
        return sum(payment.amount for payment in self.payments.all())

    def balance_due(self):
        """Cantidad pendiente de pago"""
        return self.total_pay - self.amount_paid()
```

**Vista payroll_weekly_review:**
```python
@login_required
def payroll_weekly_review(request):
    """
    Vista para revisar y aprobar la nómina semanal.
    Muestra todos los empleados con sus horas trabajadas en la semana,
    permite editar horas y tasas, y crear registros de nómina.
    """
    profile = getattr(request.user, 'profile', None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        return redirect('dashboard')

    # Obtener parámetros de fecha (por defecto: semana actual)
    week_start_str = request.GET.get('week_start')
    if week_start_str:
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
    else:
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())  # Lunes

    week_end = week_start + timedelta(days=6)  # Domingo

    # Buscar o crear PayrollPeriod
    period, created = PayrollPeriod.objects.get_or_create(
        week_start=week_start,
        week_end=week_end,
        defaults={'created_by': request.user}
    )

    # Obtener todos los empleados activos
    employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')

    # Preparar datos de cada empleado
    employee_data = []
    for emp in employees:
        # Buscar o crear PayrollRecord
        record, rec_created = PayrollRecord.objects.get_or_create(
            period=period,
            employee=emp,
            week_start=week_start,
            week_end=week_end,
            defaults={
                'hourly_rate': emp.hourly_rate,
                'total_hours': Decimal('0.00'),
                'total_pay': Decimal('0.00')
            }
        )

        # Calcular horas reales desde TimeEntry
        time_entries = TimeEntry.objects.filter(
            employee=emp,
            date__range=(week_start, week_end)
        )
        
        calculated_hours = sum(
            Decimal(entry.hours_worked) if entry.hours_worked else Decimal('0.00') 
            for entry in time_entries
        )

        # Desglose por proyecto
        hours_by_project = {}
        for entry in time_entries:
            proj_name = entry.project.name if entry.project else "Sin Proyecto"
            if proj_name not in hours_by_project:
                hours_by_project[proj_name] = Decimal('0.00')
            hours_by_project[proj_name] += Decimal(entry.hours_worked or 0)

        # Desglose por CO
        hours_by_co = {}
        for entry in time_entries.filter(change_order__isnull=False):
            co_desc = f"CO #{entry.change_order.id}: {entry.change_order.description[:30]}"
            if co_desc not in hours_by_co:
                hours_by_co[co_desc] = Decimal('0.00')
            hours_by_co[co_desc] += Decimal(entry.hours_worked or 0)

        employee_data.append({
            'employee': emp,
            'record': record,
            'calculated_hours': calculated_hours,
            'hours_by_project': hours_by_project,
            'hours_by_co': hours_by_co,
            'time_entries': time_entries,
        })

    # POST: Actualizar registros
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_records':
            for emp_data in employee_data:
                record = emp_data['record']
                emp_id = str(record.employee.id)
                
                hours = request.POST.get(f'hours_{emp_id}')
                rate = request.POST.get(f'rate_{emp_id}')
                notes = request.POST.get(f'notes_{emp_id}', '')
                
                if hours:
                    record.total_hours = Decimal(hours)
                if rate:
                    record.adjusted_rate = Decimal(rate)
                
                record.total_pay = record.calculate_total_pay()
                record.notes = notes
                record.reviewed = True
                record.save()
            
            messages.success(request, "Registros de nómina actualizados correctamente.")
            return redirect('payroll_weekly_review')
        
        elif action == 'approve_period':
            period.status = 'approved'
            period.save()
            messages.success(request,
                           f"Nómina de la semana {week_start} - {week_end} aprobada.")
            return redirect('payroll_weekly_review')

    context = {
        'period': period,
        'week_start': week_start,
        'week_end': week_end,
        'employee_data': employee_data,
        'total_hours': sum(data['calculated_hours'] for data in employee_data),
        'total_payroll': period.total_payroll(),
        'total_paid': period.total_paid(),
        'balance_due': period.balance_due(),
    }
    
    return render(request, 'core/payroll_weekly_review.html', context)
```

**Interfaz de Revisión Semanal:**
```
┌────────────────────────────────────────────────────────────┐
│ 💰 PAYROLL WEEKLY REVIEW                                   │
│ Semana: Aug 18 - Aug 24, 2025                              │
│ [◀️ Semana Anterior] [Semana Siguiente ▶️]                 │
├────────────────────────────────────────────────────────────┤
│ Status: 🟡 DRAFT                                            │
│                                                            │
│ 📊 RESUMEN:                                                │
│ • Total Horas: 152.5 hrs                                   │
│ • Total Nómina: $3,812.50                                  │
│ • Pagado: $0.00                                            │
│ • Balance: $3,812.50                                       │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ EMPLEADOS (5):                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 👷 JUAN PÉREZ                                          │ │
│ │ ┌──────────────────────────────────────────────────┐   │ │
│ │ │ Horas Calculadas: 40.0 hrs                       │   │ │
│ │ │ Tasa: $25.00/hr (editable: [25.00])             │   │ │
│ │ │ Total: $1,000.00                                 │   │ │
│ │ │                                                  │   │ │
│ │ │ DESGLOSE POR PROYECTO:                           │   │ │
│ │ │ • Villa Moderna: 32.0 hrs                        │   │ │
│ │ │ • Ocean View Condo: 8.0 hrs                      │   │ │
│ │ │                                                  │   │ │
│ │ │ DESGLOSE POR CHANGE ORDER:                       │   │ │
│ │ │ • CO #45: Molduras adicionales - 16.0 hrs       │   │ │
│ │ │ • CO #46: Cambio de color - 8.0 hrs             │   │ │
│ │ │ • Sin CO: 16.0 hrs ⚠️                           │   │ │
│ │ │                                                  │   │ │
│ │ │ Horas Aprobadas: [40.0]                         │   │ │
│ │ │ Notas: [Semana completa, buen trabajo]          │   │ │
│ │ │                                                  │   │ │
│ │ │ [✓ Revisar] [Ver TimeEntries (20)]              │   │ │
│ │ └──────────────────────────────────────────────────┘   │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 👷 MIKE JOHNSON                                        │ │
│ │ Horas: 38.5 hrs | Tasa: $28.00 | Total: $1,078.00     │ │
│ │ [Ver Detalles ▼]                                       │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 👷 CARLOS RODRIGUEZ                                    │ │
│ │ Horas: 35.0 hrs | Tasa: $22.00 | Total: $770.00       │ │
│ │ ⚠️ Tiempo sin CO: 12.0 hrs                            │ │
│ │ [Ver Detalles ▼]                                       │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Ver Todos (5)] [Expandir Todos]                           │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ ⚠️ ALERTAS:                                                │
│ • 28.0 horas sin Change Order asignado                    │
│ • Juan Pérez trabajó 40.0 horas (máximo regular)          │
│                                                            │
│ [💾 Guardar Cambios] [✅ Aprobar Nómina] [📊 Exportar]     │
└────────────────────────────────────────────────────────────┘
```

**Workflow de Nómina:**
```
Flujo de Nómina Semanal:
┌───────────────────────────────────────────────┐
│ 1. DRAFT (Borrador)                           │
│    • Sistema crea automáticamente             │
│    • Calcula horas desde TimeEntry            │
│    • PM puede editar horas/tasas              │
│    ↓                                           │
│ 2. UNDER_REVIEW (En Revisión)                 │
│    • PM revisa cada empleado                  │
│    • Ajusta horas si necesario                │
│    • Asigna tiempo a Change Orders            │
│    ↓                                           │
│ 3. APPROVED (Aprobado)                        │
│    • PM aprueba período completo              │
│    • Bloquea edición de horas                 │
│    • Permite registrar pagos                  │
│    ↓                                           │
│ 4. PAID (Pagado)                               │
│    • Todos los pagos registrados              │
│    • Balance = $0                             │
│    • Cierra período                           │
└───────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Auto-cálculo de horas desde TimeEntry
- ✅ Desglose por proyecto y CO
- ✅ Editable hours y rates
- ✅ Workflow status
- ⚠️ Falta: Overtime calculation (>40 hrs)
- ⚠️ Falta: Holiday pay
- ⚠️ Falta: Deductions (taxes, insurance)
- ⚠️ Falta: Direct deposit integration
- ⚠️ Falta: PDF payslips generation
- ⚠️ Falta: Employee self-service portal

---

### 📌 FUNCIÓN 22.2 - Registrar Pagos de Nómina

**Modelo PayrollPayment:**
```python
class PayrollPayment(models.Model):
    """Registro de pagos parciales o completos de nómina"""
    payroll_record = models.ForeignKey(PayrollRecord,
                                      related_name='payments',
                                      on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=[
        ('check', 'Cheque'),
        ('transfer', 'Transferencia'),
        ('cash', 'Efectivo'),
    ], default='check')
    check_number = models.CharField(max_length=50, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']
```

**Vista payroll_record_payment:**
```python
@login_required
def payroll_record_payment(request, record_id):
    """
    Registrar un pago (parcial o completo) para un PayrollRecord.
    """
    profile = getattr(request.user, 'profile', None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        return redirect('dashboard')

    record = get_object_or_404(PayrollRecord, id=record_id)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_date = request.POST.get('payment_date')
        payment_method = request.POST.get('payment_method', 'check')
        check_number = request.POST.get('check_number', '')
        reference = request.POST.get('reference', '')
        notes = request.POST.get('notes', '')

        if amount and payment_date:
            payment = PayrollPayment.objects.create(
                payroll_record=record,
                amount=Decimal(amount),
                payment_date=payment_date,
                payment_method=payment_method,
                check_number=check_number,
                reference=reference,
                notes=notes,
                recorded_by=request.user
            )
            
            messages.success(request,
                           f"Pago de ${amount} registrado para {record.employee}.")
            
            return redirect('payroll_weekly_review')
        else:
            messages.error(request, "Monto y fecha de pago son requeridos.")

    return render(request, 'core/payroll_payment_form.html', {
        'record': record,
    })
```

**Interfaz de Registro de Pago:**
```
┌────────────────────────────────────────────────────────────┐
│ 💳 REGISTRAR PAGO DE NÓMINA                                │
│ Empleado: Juan Pérez                                       │
│ Semana: Aug 18 - Aug 24, 2025                              │
├────────────────────────────────────────────────────────────┤
│ 📊 INFORMACIÓN:                                            │
│ • Total adeudado: $1,000.00                                │
│ • Ya pagado: $0.00                                         │
│ • Balance pendiente: $1,000.00                             │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ NUEVO PAGO:                                                │
│ Monto: [$1000.00_______]                                   │
│        [Pago Completo] [50%] [25%]                         │
│                                                            │
│ Fecha de Pago: [2025-08-25]                                │
│                                                            │
│ Método de Pago:                                            │
│ ● Cheque  ○ Transferencia  ○ Efectivo                     │
│                                                            │
│ Número de Cheque: [#1234______]                            │
│                                                            │
│ Referencia: [Weekly payroll Aug 18-24]                     │
│                                                            │
│ Notas:                                                     │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Pago completo semana regular                           │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [💾 Registrar Pago] [❌ Cancelar]                          │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ HISTORIAL DE PAGOS:                                        │
│ (No hay pagos registrados aún)                             │
└────────────────────────────────────────────────────────────┘

Después de registrar:
┌────────────────────────────────────────────────────────────┐
│ ✅ Pago registrado exitosamente                            │
│ • Monto: $1,000.00                                         │
│ • Cheque #1234                                             │
│ • Balance restante: $0.00                                  │
└────────────────────────────────────────────────────────────┘
```

**Pagos Parciales:**
```
Ejemplo: Pago en 2 partes
┌────────────────────────────────────────────────────────────┐
│ HISTORIAL DE PAGOS - Juan Pérez                            │
│ Total adeudado: $1,000.00                                  │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✅ Pago 1: $600.00                                     │ │
│ │    Aug 25, 2025 | Cheque #1234                        │ │
│ │    Ref: "Partial payment"                              │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✅ Pago 2: $400.00                                     │ │
│ │    Aug 28, 2025 | Transferencia                       │ │
│ │    Ref: "Final payment"                                │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Total pagado: $1,000.00 ✓                                  │
│ Balance: $0.00                                             │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Partial payment support
- ✅ Multiple payment methods
- ✅ Payment tracking per record
- ⚠️ Falta: Automated payment reminders
- ⚠️ Falta: Batch payment processing
- ⚠️ Falta: Bank reconciliation
- ⚠️ Falta: Payment receipt generation
- ⚠️ Falta: Integration with accounting software

---

### 📌 FUNCIÓN 22.3 - Historial de Pagos de Nómina

**Vista payroll_payment_history:**
```python
@login_required
def payroll_payment_history(request, employee_id=None):
    """
    Historial de pagos de nómina. Si se especifica employee_id,
    muestra solo ese empleado.
    """
    profile = getattr(request.user, 'profile', None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        return redirect('dashboard')

    if employee_id:
        employee = get_object_or_404(Employee, id=employee_id)
        records = PayrollRecord.objects.filter(
            employee=employee
        ).order_by('-week_start')
    else:
        employee = None
        records = PayrollRecord.objects.all().order_by(
            '-week_start',
            'employee__last_name'
        )

    # Agregar datos de pagos a cada registro
    records_data = []
    for record in records:
        payments = record.payments.all()
        records_data.append({
            'record': record,
            'payments': payments,
            'amount_paid': record.amount_paid(),
            'balance_due': record.balance_due(),
        })

    context = {
        'employee': employee,
        'records_data': records_data,
    }
    
    return render(request, 'core/payroll_payment_history.html', context)
```

**Interfaz de Historial:**
```
┌────────────────────────────────────────────────────────────┐
│ 📊 HISTORIAL DE PAGOS DE NÓMINA                            │
│ [Ver Todos] [Por Empleado ▼] [Exportar]                   │
├────────────────────────────────────────────────────────────┤
│ Filtros:                                                   │
│ Empleado: [Todos ▼]  Período: [Últimos 3 meses ▼]         │
│ Status: [Todos ▼]                                          │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ SEMANA: Aug 18 - Aug 24, 2025                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 👷 Juan Pérez                                          │ │
│ │ ┌──────────────────────────────────────────────────┐   │ │
│ │ │ Total: $1,000.00 | Pagado: $1,000.00 | ✅ PAID  │   │ │
│ │ │ 40.0 hrs @ $25.00/hr                             │   │ │
│ │ │                                                  │   │ │
│ │ │ PAGOS (2):                                       │   │ │
│ │ │ • Aug 25: $600.00 (Cheque #1234)                │   │ │
│ │ │ • Aug 28: $400.00 (Transferencia)               │   │ │
│ │ │                                                  │   │ │
│ │ │ [Ver Detalles] [Recibo]                         │   │ │
│ │ └──────────────────────────────────────────────────┘   │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 👷 Mike Johnson                                        │ │
│ │ Total: $1,078.00 | Pagado: $500.00 | 🟡 PARTIAL       │ │
│ │ Balance: $578.00                                       │ │
│ │ [Registrar Pago] [Ver Detalles]                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 👷 Carlos Rodriguez                                    │ │
│ │ Total: $770.00 | Pagado: $0.00 | 🔴 PENDING           │ │
│ │ [Registrar Pago] [Ver Detalles]                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ TOTAL SEMANA: $3,812.50 | Pagado: $2,100.00 | Pend: $1,712.50│
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ SEMANA: Aug 11 - Aug 17, 2025                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ TOTAL: $3,240.00 | PAGADO: $3,240.00 | ✅ PAID        │ │
│ │ [Ver Detalles (5 empleados)]                           │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Ver Más Semanas...] [Reporte Mensual] [Exportar Excel]   │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 📊 RESUMEN MENSUAL (Agosto 2025):                          │
│ • Total Nómina: $15,250.00                                 │
│ • Total Pagado: $13,540.00                                 │
│ • Pendiente: $1,710.00                                     │
│ • Empleados activos: 5                                     │
│ • Horas totales: 610 hrs                                   │
└────────────────────────────────────────────────────────────┘
```

**Vista Individual por Empleado:**
```
┌────────────────────────────────────────────────────────────┐
│ 📊 HISTORIAL DE PAGOS - JUAN PÉREZ                         │
│ [⬅️ Volver] [Exportar] [Recibos]                          │
├────────────────────────────────────────────────────────────┤
│ ÚLTIMO TRIMESTRE (Jul - Sep 2025):                         │
│                                                            │
│ Semana         │ Horas │ Pago    │ Pagado  │ Status       │
│ ───────────────┼───────┼─────────┼─────────┼──────────────┤
│ Aug 18-24      │ 40.0  │ $1,000  │ $1,000  │ ✅ Paid      │
│ Aug 11-17      │ 38.5  │ $962    │ $962    │ ✅ Paid      │
│ Aug 4-10       │ 40.0  │ $1,000  │ $1,000  │ ✅ Paid      │
│ Jul 28-Aug 3   │ 35.0  │ $875    │ $875    │ ✅ Paid      │
│ Jul 21-27      │ 40.0  │ $1,000  │ $600    │ 🟡 Partial   │
│ Jul 14-20      │ 40.0  │ $1,000  │ $0      │ 🔴 Pending   │
│ ───────────────┼───────┼─────────┼─────────┼──────────────┤
│ TOTAL          │ 233.5 │ $5,837  │ $5,437  │ -$400 pend.  │
│                                                            │
│ 📈 ESTADÍSTICAS:                                           │
│ • Promedio semanal: 38.9 hrs                               │
│ • Tasa: $25.00/hr                                          │
│ • Proyectos: Villa Moderna (70%), Ocean View (30%)         │
│                                                            │
│ [📥 Descargar Todos los Recibos] [📊 Reporte Anual]       │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Complete payment history
- ✅ Filter by employee/period
- ✅ Payment status tracking
- ⚠️ Falta: Year-end tax reports (W2, 1099)
- ⚠️ Falta: Quarterly summaries
- ⚠️ Falta: Comparison vs budget
- ⚠️ Falta: Employee earnings statements
- ⚠️ Falta: Automated tax calculations
- ⚠️ Falta: Export to QuickBooks/accounting systems

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 22**

### Mejoras CRÍTICAS:
1. 🔴 **Tax & Compliance**
   - Automated tax calculations (federal, state, local)
   - W2/1099 generation
   - Quarterly tax reports
   - Compliance tracking (labor laws)

2. 🔴 **Payment Automation**
   - Direct deposit integration
   - Batch payment processing
   - Bank reconciliation
   - Payment reminders

3. 🔴 **Employee Self-Service**
   - Portal para ver payslips
   - Download pay stubs
   - YTD earnings summary
   - Tax document access

### Mejoras Importantes:
4. ⚠️ Overtime calculation (time and a half)
5. ⚠️ Holiday pay tracking
6. ⚠️ Deductions management (insurance, 401k, etc.)
7. ⚠️ Bonus/commission tracking
8. ⚠️ PTO (Paid Time Off) accrual
9. ⚠️ Benefits administration
10. ⚠️ Multi-currency support
11. ⚠️ Integration con accounting software
12. ⚠️ Audit trail completo
13. ⚠️ Payroll forecasting
14. ⚠️ Mobile app para employees

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)
- ✅ Módulo 12: Planes Diarios (14/14) ⭐ CRÍTICO
- ✅ Módulo 13: SOPs/Plantillas (5/5)
- ✅ Módulo 14: Minutas/Timeline (3/3)
- ✅ Módulo 15: RFIs, Issues & Risks (6/6)
- ✅ Módulo 16: Solicitudes (Material & Cliente) (4/4)
- ✅ Módulo 17: Fotos & Floor Plans (5/5)
- ✅ Módulo 18: Inventory (3/3)
- ✅ Módulo 19: Color Samples & Design Chat (6/6)
- ✅ Módulo 20: Communication (Chat & Comments) (3/3)
- ✅ Módulo 21: Dashboards (6/6) ⭐ CRÍTICO
- ✅ Módulo 22: Payroll (Nómina Semanal) (3/3)

**Total documentado: 179/250+ funciones (72%)** 🎉

**Pendientes:**
- ⏳ Módulos 24-27: 72+ funciones

---

## ✅ **MÓDULO 23: QUALITY CONTROL (DAMAGE REPORTS & TOUCH-UPS)** (4/4 COMPLETO)

### 📌 FUNCIÓN 23.1 - Touch-Up Board (Gestión de Retoques)

**Vista touchup_board:**
```python
@login_required
def touchup_board(request, project_id):
    """Vista dedicada para gestionar touch-ups del proyecto."""
    from django.core.paginator import Paginator
    
    project = get_object_or_404(Project, id=project_id)
    qs = project.tasks.filter(is_touchup=True).select_related(
        'assigned_to',
        'created_by'
    ).order_by('-created_at')
    
    # Filters
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    
    assigned = request.GET.get('assigned')
    if assigned == 'unassigned':
        qs = qs.filter(assigned_to__isnull=True)
    elif assigned:
        qs = qs.filter(assigned_to__id=assigned)
    
    date_from = request.GET.get('date_from')
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['created_at', '-created_at', 'status',
                   '-status', 'assigned_to', '-assigned_to']:
        qs = qs.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get available employees for filter dropdown
    employees = User.objects.filter(
        profile__role__in=['employee', 'superintendent']
    ).order_by('username')
    
    return render(request, 'core/touchup_board.html', {
        'project': project,
        'page_obj': page_obj,
        'filter_status': status,
        'filter_assigned': assigned,
        'filter_date_from': date_from,
        'filter_date_to': date_to,
        'sort_by': sort_by,
        'employees': employees,
    })
```

**Interfaz Touch-Up Board:**
```
┌────────────────────────────────────────────────────────────┐
│ 🔧 TOUCH-UP BOARD - VILLA MODERNA                          │
│ [➕ Nuevo Touch-Up] [📊 Estadísticas] [📥 Exportar]        │
├────────────────────────────────────────────────────────────┤
│ FILTROS:                                                   │
│ Status: [Todos ▼]  Asignado: [Todos ▼]  Desde: [____]     │
│ Ordenar: [Más reciente ▼]  [🔍 Buscar]                    │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 📊 RESUMEN:                                                │
│ Total: 15 │ Pendiente: 8 │ En Progreso: 4 │ Completados: 3│
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ SIN ASIGNAR (5):                                           │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 Paint drip on living room wall                      │ │
│ │    Creado: Hoy 10:30 AM por Cliente                   │ │
│ │    [IMAGEN] [📝 Descripción]                           │ │
│ │    [👤 Asignar a: _______] [▼ Status: Pendiente]      │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟡 Scratch on cabinet door                             │ │
│ │    Creado: Ayer 4:15 PM por PM                        │ │
│ │    [Ver Detalle] [Asignar] [Cambiar Status]           │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ EN PROGRESO (4):                                           │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟢 Corregir esquina bathroom                           │ │
│ │    Asignado a: Juan Pérez | Inicio: Hoy 8:00 AM      │ │
│ │    [Ver Progreso] [Marcar Completado]                 │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ PENDIENTE (8):                                             │
│ • Retocar moldura - Asignado: Mike Johnson                │
│ • Color mismatch puerta - Asignado: Carlos                │
│ • Limpiar exceso caulk - Sin asignar                      │
│ [Ver Todos (8)]                                            │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ COMPLETADOS ESTA SEMANA (3):                               │
│ • ✅ Textura irregular pared - Juan (Aug 24)              │
│ • ✅ Falta sellador - Mike (Aug 23)                       │
│ • ✅ Goteo en techo - Carlos (Aug 22)                     │
│                                                            │
│ [Página 1 de 1] [20 por página ▼]                         │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Dedicated touch-up management
- ✅ Filter by status/assignment
- ✅ Pagination support
- ⚠️ Falta: Bulk assignment
- ⚠️ Falta: Priority levels
- ⚠️ Falta: Due dates
- ⚠️ Falta: Before/after photos
- ⚠️ Falta: Materials needed tracking

---

### 📌 FUNCIÓN 23.2 - Quick Update Touch-Ups (AJAX)

**Vista touchup_quick_update:**
```python
@login_required
def touchup_quick_update(request, task_id):
    """AJAX endpoint for quick status/assignment updates on touch-up board."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    task = get_object_or_404(Task, id=task_id, is_touchup=True)
    
    # Check permission
    if not (request.user.is_staff or 
            task.project.client == request.user.username):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    
    action = request.POST.get('action')
    
    if action == 'status':
        new_status = request.POST.get('status')
        if new_status in dict(Task.STATUS_CHOICES).keys():
            task.status = new_status
            if new_status == 'Completada':
                task.completed_at = timezone.now()
            task.save()
            return JsonResponse({
                'success': True,
                'status': task.get_status_display()
            })
    
    elif action == 'assign':
        employee_id = request.POST.get('employee_id')
        if employee_id:
            employee = get_object_or_404(User, id=employee_id)
            task.assigned_to = employee
            task.save()
            return JsonResponse({
                'success': True,
                'assigned_to': employee.username
            })
        else:
            task.assigned_to = None
            task.save()
            return JsonResponse({
                'success': True,
                'assigned_to': 'Sin asignar'
            })
    
    return JsonResponse({'error': 'Acción inválida'}, status=400)
```

**Interfaz de Quick Update (AJAX):**
```
En Touch-Up Board, click en task:
┌────────────────────────────────────────────────────────────┐
│ 🔧 Paint drip on living room wall                          │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Quick Actions:                                         │ │
│ │ Status: [Pendiente ▼] → [En Progreso] [Completada]   │ │
│ │         ⚡ Actualiza sin recargar página              │ │
│ │                                                        │ │
│ │ Asignar a: [Seleccionar empleado ▼]                  │ │
│ │ • Juan Pérez                                           │ │
│ │ • Mike Johnson                                         │ │
│ │ • Carlos Rodriguez                                     │ │
│ │ • [Sin asignar]                                        │ │
│ │         ⚡ Actualiza sin recargar página              │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘

Después de update:
┌────────────────────────────────────────────────────────────┐
│ ✅ Touch-up actualizado                                    │
│ • Status: En Progreso                                      │
│ • Asignado a: Juan Pérez                                   │
│ [Badge actualiza automáticamente en el board]              │
└────────────────────────────────────────────────────────────┘
```

**JavaScript Example:**
```javascript
function quickUpdateTouchup(taskId, action, value) {
    fetch(`/touchup/${taskId}/quick-update/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `action=${action}&${action}=${value}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI without reload
            if (action === 'status') {
                updateStatusBadge(taskId, data.status);
            } else if (action === 'assign') {
                updateAssignedLabel(taskId, data.assigned_to);
            }
            showNotification('Touch-up actualizado exitosamente');
        }
    });
}
```

**Mejoras Identificadas:**
- ✅ AJAX updates (no page reload)
- ✅ Quick status changes
- ✅ Quick assignment
- ⚠️ Falta: Undo capability
- ⚠️ Falta: Activity log
- ⚠️ Falta: Notifications to assigned employee
- ⚠️ Falta: Batch operations

---

### 📌 FUNCIÓN 23.3 - Damage Report Management

**Modelo DamageReport:**
```python
class DamageReport(models.Model):
    """Reportes de daños encontrados en el proyecto"""
    SEVERITY_CHOICES = [
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
        ('critical', 'Crítico'),
    ]
    STATUS_CHOICES = [
        ('reported', 'Reportado'),
        ('in_repair', 'En Reparación'),
        ('resolved', 'Resuelto'),
    ]
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE,
                               related_name='damage_reports')
    plan = models.ForeignKey(FloorPlan, on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='damage_reports')
    pin = models.OneToOneField(PlanPin, on_delete=models.SET_NULL,
                              null=True, blank=True,
                              related_name='damage_report')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES,
                               default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                             default='reported')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reported_at']
```

**Modelo DamagePhoto:**
```python
class DamagePhoto(models.Model):
    """Fotos de evidencia de daños"""
    report = models.ForeignKey(DamageReport, on_delete=models.CASCADE,
                              related_name='photos')
    image = models.ImageField(upload_to='damage_reports/')
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Vista damage_report_list:**
```python
@login_required
def damage_report_list(request, project_id):
    """Lista de reportes de daños del proyecto."""
    from core.models import DamageReport
    project = get_object_or_404(Project, id=project_id)
    reports = project.damage_reports.select_related(
        'plan',
        'pin',
        'reported_by'
    ).all()
    
    severity = request.GET.get('severity')
    if severity:
        reports = reports.filter(severity=severity)
    
    status = request.GET.get('status')
    if status:
        reports = reports.filter(status=status)
    
    return render(request, 'core/damage_report_list.html', {
        'project': project,
        'reports': reports,
        'filter_severity': severity,
        'filter_status': status,
    })
```

**Interfaz de Damage Reports:**
```
┌────────────────────────────────────────────────────────────┐
│ ⚠️ DAMAGE REPORTS - VILLA MODERNA                          │
│ [➕ Reportar Daño] [📊 Estadísticas] [📥 Exportar]         │
├────────────────────────────────────────────────────────────┤
│ FILTROS:                                                   │
│ Severidad: [Todos ▼]  Status: [Todos ▼]  [🔍 Buscar]      │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ 📊 RESUMEN:                                                │
│ Total: 8 │ Críticos: 1 │ Altos: 2 │ Medios: 3 │ Bajos: 2 │
│ Reportados: 3 │ En Reparación: 4 │ Resueltos: 1           │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ CRÍTICOS (1):                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 CRITICAL: Water damage on ceiling                   │ │
│ │ ┌──────────────────────────────────────────────────┐   │ │
│ │ │ [FOTO 1] [FOTO 2] [FOTO 3]                       │   │ │
│ │ │                                                  │   │ │
│ │ │ Descripción: Mancha de agua detectada en techo  │   │ │
│ │ │ del baño principal. Posible fuga de plomería.   │   │ │
│ │ │                                                  │   │ │
│ │ │ Ubicación: Main Level - Bathroom                │   │ │
│ │ │ [Ver en Floor Plan 📐]                          │   │ │
│ │ │                                                  │   │ │
│ │ │ Reportado por: Cliente                           │   │ │
│ │ │ Fecha: Hoy 9:45 AM                              │   │ │
│ │ │ Status: 🔄 IN_REPAIR                            │   │ │
│ │ │                                                  │   │ │
│ │ │ Touch-up relacionado: TSK-045 (Juan Pérez)     │   │ │
│ │ │                                                  │   │ │
│ │ │ [📝 Actualizar Status] [📸 Agregar Fotos]       │   │ │
│ │ │ [🔧 Crear Touch-up] [Ver Detalle]              │   │ │
│ │ └──────────────────────────────────────────────────┘   │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ALTOS (2):                                                 │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟠 HIGH: Deep scratch on hardwood floor                │ │
│ │    Reportado: Ayer 2:30 PM | Status: REPORTED         │ │
│ │    [Ver Detalle] [Asignar]                             │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ MEDIOS (3): [Ver lista completa]                           │
│ BAJOS (2): [Ver lista completa]                            │
│                                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                            │
│ RESUELTOS ESTA SEMANA (1):                                 │
│ • ✅ Paint chip on wall - Aug 23                          │
└────────────────────────────────────────────────────────────┘
```

**Workflow de Damage Report:**
```
Flujo de Daños:
┌───────────────────────────────────────────────┐
│ 1. REPORTED (Reportado)                       │
│    • Cliente/PM/Superintendent detecta daño   │
│    • Sube fotos y descripción                 │
│    • Marca ubicación en Floor Plan            │
│    • Asigna severidad                         │
│    ↓                                           │
│ 2. IN_REPAIR (En Reparación)                  │
│    • Se crea Touch-up relacionado             │
│    • Asigna a empleado                        │
│    • Actualiza fotos de progreso              │
│    ↓                                           │
│ 3. RESOLVED (Resuelto)                        │
│    • Touch-up completado                      │
│    • Fotos "after" subidas                    │
│    • Cliente aprueba reparación               │
│    • Cierra reporte                           │
└───────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ Multi-photo support
- ✅ Floor plan integration
- ✅ Severity levels
- ✅ Link to touch-ups
- ⚠️ Falta: Automatic touch-up creation
- ⚠️ Falta: Client approval workflow
- ⚠️ Falta: Cost tracking for repairs
- ⚠️ Falta: Before/after comparison
- ⚠️ Falta: Warranty tracking

---

### 📌 FUNCIÓN 23.4 - Update Damage Report Status (AJAX)

**Vista damage_report_update_status:**
```python
@login_required
def damage_report_update_status(request, report_id):
    """Update damage report status and severity."""
    report = get_object_or_404(DamageReport, id=report_id)
    
    # Check permission (staff or superintendent)
    profile = getattr(request.user, 'profile', None)
    if not (request.user.is_staff or 
            (profile and profile.role == 'superintendent')):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        new_severity = request.POST.get('severity')
        
        if new_status and new_status in dict(DamageReport.STATUS_CHOICES).keys():
            report.status = new_status
            report.save()
        
        if new_severity and new_severity in dict(DamageReport.SEVERITY_CHOICES).keys():
            report.severity = new_severity
            report.save()
        
        return JsonResponse({
            'success': True,
            'status': report.get_status_display(),
            'severity': report.get_severity_display()
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
```

**Interfaz de Quick Update:**
```
En Damage Report Detail:
┌────────────────────────────────────────────────────────────┐
│ ⚠️ Water damage on ceiling                                 │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Quick Update:                                          │ │
│ │                                                        │ │
│ │ Status:     [REPORTED ▼]                              │ │
│ │             • REPORTED (Reportado)                     │ │
│ │             • IN_REPAIR (En Reparación) ✓             │ │
│ │             • RESOLVED (Resuelto)                      │ │
│ │                                                        │ │
│ │ Severidad:  [CRITICAL ▼]                              │ │
│ │             • LOW (Bajo)                               │ │
│ │             • MEDIUM (Medio)                           │ │
│ │             • HIGH (Alto)                              │ │
│ │             • CRITICAL (Crítico) ✓                    │ │
│ │                                                        │ │
│ │ [💾 Guardar Cambios]                                   │ │
│ │ ⚡ Sin recargar página                                │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘

Después de update:
┌────────────────────────────────────────────────────────────┐
│ ✅ Damage report actualizado                               │
│ • Status: EN REPARACIÓN 🔄                                │
│ • Severidad: CRÍTICO 🔴                                    │
│ [Badges actualizan automáticamente]                        │
└────────────────────────────────────────────────────────────┘
```

**Notificaciones Automáticas:**
```
Cuando Status cambia a IN_REPAIR:
┌────────────────────────────────────────────────────────────┐
│ 📧 Notificaciones enviadas:                                │
│ • Cliente: "Reparación iniciada para daño #DMG-012"       │
│ • Empleado asignado: "Nuevo touch-up asignado"            │
│ • PM: "Damage report actualizado a IN_REPAIR"             │
└────────────────────────────────────────────────────────────┘

Cuando Status cambia a RESOLVED:
┌────────────────────────────────────────────────────────────┐
│ 📧 Notificaciones enviadas:                                │
│ • Cliente: "Daño reparado. Por favor revisa y confirma"   │
│ • PM: "Damage report #DMG-012 resuelto"                   │
│ • Superintendent: "Touch-up completado exitosamente"      │
└────────────────────────────────────────────────────────────┘
```

**Mejoras Identificadas:**
- ✅ AJAX status updates
- ✅ Severity adjustments
- ✅ Permission controls
- ⚠️ Falta: Automatic notifications
- ⚠️ Falta: Status change log
- ⚠️ Falta: Reason for severity changes
- ⚠️ Falta: Required photos for resolution
- ⚠️ Falta: Client approval step

---

## 🎯 **RESUMEN DE MEJORAS IDENTIFICADAS - MÓDULO 23**

### Mejoras CRÍTICAS:
1. 🔴 **Workflow Automation**
   - Auto-create touch-ups from damage reports
   - Required client approval before resolution
   - Automatic notifications por status changes
   - SLA tracking (response/resolution times)

2. 🔴 **Documentation**
   - Before/after photo comparison
   - Photo annotation tools
   - Required photos para cada status
   - Video evidence support

3. 🔴 **Analytics & Reporting**
   - Damage trends analysis
   - Cost tracking for repairs
   - Quality metrics dashboard
   - Recurring damage patterns

### Mejoras Importantes:
4. ⚠️ Priority levels for touch-ups
5. ⚠️ Due dates and scheduling
6. ⚠️ Materials needed tracking
7. ⚠️ Bulk operations (assign/update múltiples)
8. ⚠️ Activity log/audit trail
9. ⚠️ Warranty tracking
10. ⚠️ Integration with invoicing (charge for damage repairs)
11. ⚠️ Preventive maintenance alerts
12. ⚠️ Mobile app optimized
13. ⚠️ Offline damage reporting
14. ⚠️ Voice notes support

---

## 📊 **PROGRESO DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)
- ✅ Módulo 12: Planes Diarios (14/14) ⭐ CRÍTICO
- ✅ Módulo 13: SOPs/Plantillas (5/5)
- ✅ Módulo 14: Minutas/Timeline (3/3)
- ✅ Módulo 15: RFIs, Issues & Risks (6/6)
- ✅ Módulo 16: Solicitudes (Material & Cliente) (4/4)
- ✅ Módulo 17: Fotos & Floor Plans (5/5)
- ✅ Módulo 18: Inventory (3/3)
- ✅ Módulo 19: Color Samples & Design Chat (6/6)
- ✅ Módulo 20: Communication (Chat & Comments) (3/3)
- ✅ Módulo 21: Dashboards (6/6) ⭐ CRÍTICO
- ✅ Módulo 22: Payroll (Nómina Semanal) (3/3)
- ✅ Módulo 23: Quality Control (Damage Reports & Touch-Ups) (4/4)

**Total documentado: 183/250+ funciones (73%)** 🎉

---

## 📦 **MÓDULOS 24-27: DOCUMENTACIÓN DETALLADA COMPLETA**

**Ver archivo:** `MODULES_24_27_DETAILED.md` para documentación completa

### Resumen Módulos 24-27 (24 funciones adicionales)

**Module 24 - User Management & Settings (4 funciones):**
- 24.1: Cambio de idioma (i18n) - EN/ES para UI completa
- 24.2: Profile & Roles - 6 roles del sistema
- 24.3: ClientProjectAccess - Acceso granular por proyecto
- 24.4: Root redirect - Dashboard routing automático

**Module 25 - Export & Reporting (7 funciones):**
- 25.1: PDF Reporte de Proyecto - Métricas ejecutivas
- 25.2: PDF Factura - Con logo Kibray
- 25.3: Exportación iCal - Calendar sync auto-actualizable
- 25.4: CSV Earned Value - Para análisis con AI
- 25.5: CSV Template Progreso - Bulk upload offline
- 25.6: CSV Progreso Export - Por línea presupuestal
- 25.7: Gantt React View - Drag-and-drop interactive

**Module 26 - Utilities & Advanced Features (5 funciones):**
- 26.1: Earned Value Management - Cálculo real-time PV/EV/AC/SPI/CPI
- 26.2: Schedule Generator - Auto-crear desde estimate
- 26.3: Helper `_is_staffish` - Validación de permisos
- 26.4: Decorator `staff_required` - Restricción de acceso
- 26.5: Utils varios - Inventory, dates, channels

**Module 27 - REST API (8 endpoints):**
- 27.1: Notifications API - CRUD + mark read
- 27.2: Chat API - Channels + messages
- 27.3: Tasks API - Con filtros touchup/assigned
- 27.4: Damage Reports API - Quality control
- 27.5: Floor Plans API - Con pins
- 27.6: Color Samples API - Design workflow
- 27.7: Projects API - Lista proyectos
- 27.8: Schedule API - Con bulk_update para Gantt

**Uso de API:** Frontend React/Vue, Mobile app futura, Integraciones externas

---

## 📝 **MÓDULOS 28-29: CRUD OPERATIONS & PROJECT VIEWS**

**Ver archivo:** `MODULES_28_29_DETAILED.md` para documentación completa

### Resumen Módulos 28-29 (25 funciones adicionales)

**Module 28 - CRUD Operations & Forms (12 funciones):**
- 28.1: schedule_create_view - Crear schedule (legacy)
- 28.2: expense_create_view - Registrar gastos
- 28.3: income_create_view - Registrar ingresos
- 28.4: timeentry_create_view - Registro manual de horas
- 28.5: task_list_view - Lista tareas del proyecto
- 28.6: task_detail - Ver detalle de tarea
- 28.7: task_edit_view - Editar tarea
- 28.8: task_delete_view - Eliminar tarea
- 28.9: task_list_all - Mis tareas (todos los proyectos)
- 28.10: schedule_category_edit - Editar categoría cronograma
- 28.11: schedule_category_delete - Eliminar categoría
- 28.12-13: schedule_item_edit/delete - CRUD items cronograma

**Module 29 - Project Management Views (13 funciones):**
- 29.1: project_list - Lista todos los proyectos
- 29.2: project_overview - Dashboard 360° del proyecto
- 29.3: client_project_view - Vista específica para cliente
- 29.4: pickup_view - Coordinación recogida materiales
- 29.5: budget_line_plan_view - Planificar fechas de líneas
- 29.6: upload_project_progress - Bulk update via CSV
- 29.7: delete_progress - Eliminar punto de progreso
- 29.8: edit_progress - Corregir progreso existente
- 29.9: project_ev_series - JSON para gráficos de tendencia
- 29.10: daily_log_view - Bitácora diaria del proyecto
- 29.11: project_chat_index - Índice de canales de chat
- 29.12: schedule_generator_view - Auto-generar desde estimate
- 29.13: project_schedule_google_calendar - Instrucciones suscripción

**Características destacadas:**
- CRUD completo para entidades principales
- Bulk operations (CSV upload de progreso)
- Vistas especializadas por rol (cliente vs PM)
- Integration con calendarios externos
- EV series para gráficos de tendencia

---

## 🎯 **RESUMEN EJECUTIVO FINAL**

### 📊 Estadísticas del Sistema

**Total Documentado: 232 funciones principales**
- Módulos 1-23: 183 funciones
- Módulos 24-27: 24 funciones  
- Módulos 28-29: 25 funciones

**Cobertura: ~93% del sistema estimado (250+ funciones totales)**

**Distribución por Criticidad:**
- 🔴 Módulos Críticos (6): Facturación, Presupuesto/EV, Planes Diarios, Dashboards - **80 funciones**
- 🟡 Módulos Importantes (14): Time Tracking, Gastos, Proyectos, Change Orders, CRUD, etc. - **110 funciones**
- 🟢 Módulos de Soporte (15): SOPs, Minutas, Color Samples, Communication, API, Utils - **42 funciones**

### 🏗️ Arquitectura del Sistema

**Stack Tecnológico:**
```
Frontend:
├── Vite + TypeScript
├── Templates Django (HTML/Jinja2)
└── AJAX/Fetch API

Backend:
├── Django 4.x
├── PostgreSQL
├── Celery (async tasks)
├── Django REST Framework (API)
└── File Storage (MEDIA_ROOT)

Deployment:
├── Render.com (hosting)
├── Gunicorn (WSGI server)
└── WhiteNoise (static files)
```

**Modelos Principales (30+):**
- Project, Employee, Client, Profile
- TimeEntry, Schedule, DailyPlan, Task
- Expense, Income, Invoice, PayrollRecord
- Estimate, ChangeOrder, BudgetLine
- ColorSample, SitePhoto, FloorPlan
- DamageReport, RFI, Issue, Risk
- ChatChannel, ChatMessage, Notification

**Vistas Principales (180+):**
- 6 Dashboards especializados por rol
- ~40 vistas de gestión de proyectos
- ~30 vistas financieras
- ~25 vistas de tracking (tiempo, materiales, inventory)
- ~20 vistas de calidad (touch-ups, damage reports)
- ~15 vistas de comunicación (chat, comments, design)
- ~50+ vistas complementarias

### 🎨 Características Distintivas

**1. Earned Value Management (EVM)**
- Cálculo automático de PV, EV, AC
- Índices SPI y CPI para alertas tempranas
- Proyecciones EAC, VAC
- Dashboard con alertas por proyecto

**2. Daily Planning System**
- SOPs con templates reutilizables
- Asignación de actividades diarias
- Material checking automático
- Employee morning dashboard
- Completion tracking con fotos

**3. Financial Control**
- Time → Change Order → Invoice flow
- Tracking de tiempo sin CO asignado
- Facturación con estados y pagos parciales
- Nómina semanal con revisión/aprobación
- Budget vs actual por línea presupuestaria

**4. Quality Assurance**
- Damage reports con severidad
- Touch-up board dedicado
- Floor plan integration con pins
- Before/after photo tracking
- Client approval workflow

**5. Multi-Role Dashboards**
- Admin: Command center con alertas globales
- PM: Operational focus (materiales, issues, planning)
- Employee: Daily tasks, clock in/out
- Client: Visual progress, photos, invoices
- Designer: Color samples, floor plans
- Superintendent: Quality control, damage reports

### 🔑 Workflows Clave

**Invoice Generation Flow:**
```
TimeEntry → ChangeOrder → Invoice → Payment
    ↓           ↓            ↓
  Payroll    Budget      Income
```

**Project Lifecycle:**
```
Estimate → Project Creation → Daily Planning → Execution
    ↓           ↓                  ↓              ↓
Approval   Budget Setup      Activities    Time Tracking
                                               ↓
                                          Change Orders
                                               ↓
                                           Invoicing
                                               ↓
                                          Completion
```

**Quality Control Flow:**
```
Site Inspection → Damage Report → Touch-Up Creation
       ↓               ↓                ↓
   SitePhoto      Severity          Assignment
                   Rating               ↓
                     ↓            Completion
                  Status              ↓
                  Updates        Resolution
                                     ↓
                              Client Approval
```

### ⚠️ Mejoras Prioritarias Globales

**CRÍTICAS (Implementar Primero):**
1. 🔴 WebSocket real-time updates (chat, dashboards, notifications)
2. 🔴 Mobile app (React Native o PWA)
3. 🔴 Automated tax calculations y W2/1099 generation
4. 🔴 Direct deposit integration
5. 🔴 Before/after photo comparison tools
6. 🔴 AR visualization para color selection
7. 🔴 Predictive analytics (budget forecasting)
8. 🔴 Offline mode para employees
9. 🔴 Email/Push notification system
10. 🔴 Integration con accounting software (QuickBooks)

**IMPORTANTES (Segunda Fase):**
11. ⚠️ Gantt chart visualization
12. ⚠️ Weather alerts para outdoor work
13. ⚠️ GPS location verification
14. ⚠️ Barcode scanning para inventory
15. ⚠️ Voice messages en chat
16. ⚠️ Bulk operations (assign, approve, export)
17. ⚠️ Employee self-service portal
18. ⚠️ Client approval workflows automated
19. ⚠️ Material cost tracking en inventory
20. ⚠️ Recurring damage pattern detection

### 📈 Métricas de Éxito del Sistema

**Operacionales:**
- Time to invoice: 48 horas promedio
- Payroll processing: 2 horas/semana
- Budget variance alerts: Real-time
- Touch-up resolution: 3-5 días promedio

**Financieras:**
- Revenue tracking: $245K+ documentado
- Expense tracking: $178K+ documentado
- Net profit margin: 27.1%
- Invoice collection rate: 85%+

**Calidad:**
- Damage reports: 8 activos, 94% resolution rate
- Touch-ups: 15 pendientes, response time <24hrs
- Client satisfaction: Visible progress tracking
- Schedule adherence: SPI tracking por proyecto

### 🚀 Próximos Pasos Recomendados

**Fase 1 - Estabilización (1-2 meses):**
1. Completar testing de módulos críticos
2. Implementar notification system básico
3. Mobile-responsive optimization
4. User onboarding guides
5. Data backup automation

**Fase 2 - Enhancement (3-4 meses):**
6. WebSocket implementation
7. Mobile app development
8. Advanced analytics dashboard
9. Integration con servicios externos
10. Workflow automation expansion

**Fase 3 - Scale (6-12 meses):**
11. Multi-company support
12. AI-powered features (predictive analytics)
13. Advanced reporting suite
14. API marketplace
15. White-label capabilities

---

## 📊 **PROGRESO FINAL DE DOCUMENTACIÓN**

**Completados:**
- ✅ Módulo 1: Gestión de Proyectos (10/10)
- ✅ Módulo 2: Gestión de Empleados (8/8)
- ✅ Módulo 3: Time Tracking (10/10)
- ✅ Módulo 4: Gastos (10/10)
- ✅ Módulo 5: Ingresos (10/10)
- ✅ Módulo 6: Facturación (14/14) ⭐ CRÍTICO
- ✅ Módulo 7: Estimados (10/10)
- ✅ Módulo 8: Change Orders (11/11)
- ✅ Módulo 9: Presupuesto/Earned Value (14/14) ⭐ CRÍTICO
- ✅ Módulo 10: Cronograma (12/12)
- ✅ Módulo 11: Tareas (12/12)
- ✅ Módulo 12: Planes Diarios (14/14) ⭐ CRÍTICO
- ✅ Módulo 13: SOPs/Plantillas (5/5)
- ✅ Módulo 14: Minutas/Timeline (3/3)
- ✅ Módulo 15: RFIs, Issues & Risks (6/6)
- ✅ Módulo 16: Solicitudes (Material & Cliente) (4/4)
- ✅ Módulo 17: Fotos & Floor Plans (5/5)
- ✅ Módulo 18: Inventory (3/3)
- ✅ Módulo 19: Color Samples & Design Chat (6/6)
- ✅ Módulo 20: Communication (Chat & Comments) (3/3)
- ✅ Módulo 21: Dashboards (6/6) ⭐ CRÍTICO
- ✅ Módulo 22: Payroll (Nómina Semanal) (3/3)
- ✅ Módulo 23: Quality Control (Damage Reports & Touch-Ups) (4/4)
- ✅ Módulo 24: User Management & Settings (4/4)
- ✅ Módulo 25: Export & Reporting (PDF, iCal, CSV) (7/7)
- ✅ Módulo 26: Utilities & Advanced Features (EVM, Generators) (5/5)
- ✅ Módulo 27: REST API (8 endpoints/8)
- ✅ Módulo 28: CRUD Operations & Forms (12/12)
- ✅ Módulo 29: Project Management Views (13/13)

**Total documentado: 232 funciones (93% del sistema estimado)** 🎉🎉🎉

---

## 🎓 **CONCLUSIÓN**

El sistema Kibray es una **plataforma integral de gestión de proyectos de construcción/pintura** que abarca:

✅ **Gestión Financiera Completa**: Desde estimados hasta facturación y nómina
✅ **Control de Proyectos Avanzado**: EVM, presupuestos, change orders
✅ **Planning Operacional**: Daily plans, SOPs, material tracking
✅ **Quality Assurance**: Damage reports, touch-ups, inspecciones
✅ **Comunicación Multi-Canal**: Chat, comentarios, design collaboration
✅ **Dashboards Especializados**: Por rol (6 tipos diferentes)

**Fortalezas:**
- Workflow completo de negocio
- Multi-role support robusto
- Integration de módulos bien pensada
- Visual tracking para clientes
- Earned Value Management integrado

**Oportunidades de Mejora:**
- Real-time capabilities (WebSocket)
- Mobile-first optimization
- Automation expansion
- AI/ML integration
- External service integrations

El sistema está en un **estado avanzado de desarrollo** con funcionalidad core completa y listo para deployment piloto. Las mejoras identificadas son principalmente enhancement y optimización, no corrección de funcionalidad faltante crítica.

---

*Última actualización: Documentación COMPLETA - 232 funciones documentadas (¡93% del sistema!)*  
*Fecha: Noviembre 13, 2025*  
*Sistema: Kibray - Construction Management Platform*  
*Documentación Detallada:*
- *Módulos 1-23: En este archivo (REQUIREMENTS_DOCUMENTATION.md)*
- *Módulos 24-27: Ver `MODULES_24_27_DETAILED.md`*
- *Módulos 28-29: Ver `MODULES_28_29_DETAILED.md`*

