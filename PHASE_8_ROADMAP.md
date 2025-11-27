# 🚀 FASE 8 – ADVANCED FEATURES (Roadmap)

Fecha: 26 Nov 2025
Owner: Tech Lead

## Objetivos
- Desbloquear planificación avanzada (dependencias de tareas y Gantt).
- Formalizar firmas digitales (legal/compliance) en módulos clave.
- Normalizar Cost Codes para reportes financieros.
- Unificar exportes (PDF/JSON) con un motor de reportes común.
- Preparar base para EVM dinámico.

## Alcance por Módulo

### 1) Task Dependencies (Gantt)
- Nuevo modelo: TaskDependency
  - task (FK Task)
  - predecessor (FK Task)
  - type: FS|SS|FF|SF (default FS)
  - lag_minutes (int, default 0)
- Cambios en Task:
  - derived fields: earliest_start, earliest_finish (servicio)
  - API: endpoints para CRUD de dependencias
- Endpoints:
  - POST /api/v1/tasks/{id}/dependencies/
  - DELETE /api/v1/tasks/{id}/dependencies/{dep_id}/
  - GET /api/v1/tasks/gantt?project={id}
- Tests mínimos:
  - Crear dependencia FS y validar orden
  - Ciclo simple A->B->C (sin ciclos)
  - Prevención de ciclos (400)

### 2) Digital Signatures
- Entidades: ColorSample, ChangeOrder
- Campos:
  - signed_by (FK User)
  - signed_at (DateTime)
  - signature_blob (bytes/base64)
  - signature_ip (char)
- Endpoints:
  - POST /api/v1/color-samples/{id}/sign/
  - POST /api/v1/change-orders/{id}/sign/
- Validaciones:
  - Solo roles autorizados (client/admin)
  - Idempotencia (re-firma opcional bloqueada)

### 3) Cost Codes Refactor
- Modelo CostCode
  - normalizar jerarquía (Division-Section-Code)
  - campo `is_leaf` y `parent`
- Migración de BudgetLine/Expense/Income para usar FK consistente
- Endpoints:
  - GET /api/v1/cost-codes/tree/
  - POST /api/v1/cost-codes/import/ (CSV)
- Tests:
  - Import básico
  - Asignación a Budget/Expense

### 4) Report Engine Unificado
- Servicio `report_engine.py`
  - generate_pdf(entity, id)
  - generate_json(entity, id)
- Integraciones iniciales:
  - DamageReport, FloorPlan (resumen de pins), ChangeOrder, Task
- Endpoints:
  - GET /api/v1/reports/{entity}/{id}.pdf
  - GET /api/v1/reports/{entity}/{id}.json
- Tests:
  - JSON válido (estructura contract)
  - PDF generado (cabecera + checksum simple)

### 5) EVM Dynamic Recalculation
- Servicio `earned_value.py` extendido
  - snapshots vs rolling
  - inputs desde ScheduleItems & Tasks
- Endpoint:
  - GET /api/v1/evm/summary?project={id}
- Tests:
  - Proyecto simple: PV, EV, AC coherentes

## Contratos (v1)
- TaskDependency:
  - input: { predecessor_id, type, lag_minutes }
  - output: { id, task, predecessor, type, lag_minutes }
  - errores: 400 ciclo detectado, 404 tarea inexistente
- Signatures:
  - input: { signature_blob, signature_ip }
  - output: { signed_by_name, signed_at }

## Riesgos / Edge cases
- Ciclos en dependencias
- Cambios masivos de fechas por cascada (performance)
- Firmas desde móvil (tamaños de payload)
- Cost Codes legacy: mapeo correcto

## Entregables
- Código + tests verdes
- Doc de API actualizada
- Mini guía de uso (README)

## Plan de Sprint (estimado)
- Semana 1: Task Dependencies (+ tests)
- Semana 2: Digital Signatures + Report Engine base
- Semana 3: Cost Codes refactor + EVM

