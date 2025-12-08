# KIBRAY ERP - UNIFIED ARCHITECTURE# 🏗️ ARQUITECTURA FINAL KIBRAY ERP - DOCUMENTO UNIFICADO

**Implementation Date:** November 28, 2025  

**Last Updated:** December 8, 2025  **Fecha de Implementación:** 28 de Noviembre, 2025  

**Status:** ✅ 100% COMPLETE  **Estado:** ✅ 100% COMPLETADO  

**Tests:** ✅ 738 passing, 3 skipped  **Tests:** ✅ 738 passing, 3 skipped  

**Migration:** 0096_final_architecture.py applied successfully**Migración:** 0096_final_architecture.py aplicada exitosamente



------



## TABLE OF CONTENTS## 📋 TABLA DE CONTENIDOS



1. [Executive Summary](#executive-summary)1. [Resumen Ejecutivo](#resumen-ejecutivo)

2. [Implementation Metrics](#implementation-metrics)2. [Métricas de Implementación](#métricas-de-implementación)

3. [Implemented Modules](#implemented-modules)3. [Módulos Implementados](#módulos-implementados)

4. [Validation Documentation](#validation-documentation)4. [Documentación de Validación](#documentación-de-validación)

5. [Design Decisions](#design-decisions)5. [Decisiones de Diseño](#decisiones-de-diseño)

6. [Technology Stack](#technology-stack)6. [Próximos Pasos](#próximos-pasos)

7. [System Architecture](#system-architecture)

8. [Next Steps](#next-steps)---



---## RESUMEN EJECUTIVO



## EXECUTIVE SUMMARYLa **Arquitectura Final** de Kibray ERP ha sido implementada exitosamente, integrando todas las reglas de negocio críticas en un sistema cohesivo que cubre:



The **Final Architecture** of Kibray ERP has been successfully implemented, integrating all critical business rules into a cohesive system covering:- ✅ **Facturación Flexible** (anticipos, retenciones, draft para revisión)

- ✅ **Reembolsos a Empleados** (tracking completo con 5 estados)

- ✅ **Flexible Invoicing** (deposits, retentions, draft for review)- ✅ **Planner Inteligente** (schedule_weight, checklist, progress_percent)

- ✅ **Employee Reimbursements** (complete tracking with 5 states)- ✅ **Pin Cleanup Automático** (oculta pins al completar tareas)

- ✅ **Intelligent Planner** (schedule_weight, checklist, progress_percent)- ✅ **Inventario Avanzado** (bulk_transfer con exclusión de sobrantes)

- ✅ **Automatic Pin Cleanup** (hides pins when tasks complete)- ✅ **Integración ColorSample → Project** (approved_finishes JSON)

- ✅ **Advanced Inventory** (bulk_transfer with leftover exclusion)- ✅ **Sistema de Roles Granular** (7 roles con permisos específicos)

- ✅ **ColorSample → Project Integration** (approved_finishes JSON)

- ✅ **Granular Role System** (7 roles with specific permissions)---



---## MÉTRICAS DE IMPLEMENTACIÓN



## IMPLEMENTATION METRICS### Cambios en Código



### Code Changes| Componente | Operaciones | Estado |

|------------|------------|--------|

| Component | Operations | Status || **Migración 0096** | 23 operaciones (21 add, 2 alter) | ✅ Aplicada |

|-----------|------------|--------|| **Models modificados** | 7 modelos | ✅ Completo |

| **Migration 0096** | 23 operations (21 add, 2 alter) | ✅ Applied || **Campos nuevos** | 30+ campos | ✅ Completo |

| **Models modified** | 7 models | ✅ Complete || **Métodos nuevos** | 15+ métodos | ✅ Completo |

| **New fields** | 30+ fields | ✅ Complete || **Business logic** | Task.save() pin cleanup, ColorSample approval integration | ✅ Completo |

| **New methods** | 15+ methods | ✅ Complete |

| **Business logic** | Task.save() pin cleanup, ColorSample approval integration | ✅ Complete |### Sistema de Roles



### Role System| Rol | Permisos | Custom Permission | Estado |

|-----|----------|-------------------|--------|

| Role | Permissions | Custom Permission | Status || **General Manager** | 65 | ✅ can_send_external_emails | ✅ Configurado |

|------|-------------|-------------------|--------|| **Project Manager (Full)** | 51 | ✅ can_send_external_emails | ✅ Configurado |

| **General Manager** | 65 | ✅ can_send_external_emails | ✅ Configured || **PM Trainee** | 33 | ❌ NO emails | ✅ Configurado |

| **Project Manager (Full)** | 51 | ✅ can_send_external_emails | ✅ Configured || **Designer** | 14 | - | ✅ Configurado |

| **PM Trainee** | 33 | ❌ NO emails | ✅ Configured || **Superintendent** | 11 | - | ✅ Configurado |

| **Designer** | 14 | - | ✅ Configured || **Employee** | 3 | - | ✅ Configurado |

| **Superintendent** | 11 | - | ✅ Configured || **Client** | 9 | - | ✅ Configurado |

| **Employee** | 3 | - | ✅ Configured |

| **Client** | 9 | - | ✅ Configured |### Testing



### Testing| Categoría | Cantidad | Estado |

|-----------|----------|--------|

| Category | Quantity | Status || **Tests ejecutados** | 741 | ✅ 738 passing |

|----------|----------|--------|| **Tests skipped** | 3 | ℹ️  Normales |

| **Tests executed** | 741 | ✅ 738 passing || **Tests fallidos** | 0 | ✅ Todos pasan |

| **Tests skipped** | 3 | ℹ️  Normal || **Warnings** | 427 | ⚠️  No críticos |

| **Tests failed** | 0 | ✅ All pass |

| **Warnings** | 427 | ⚠️  Non-critical |---



---## MÓDULOS IMPLEMENTADOS



## IMPLEMENTED MODULES### 1. FACTURACIÓN FLEXIBLE (Invoices)



### 1. FLEXIBLE INVOICING (Invoices)**Campos Nuevos:**

- `invoice_type`: `['standard', 'deposit', 'final']` - Tipo de factura

**New Fields:**- `retention_amount`: Decimal - Monto retenido por garantía

- `invoice_type`: `['standard', 'deposit', 'final']` - Invoice type- `is_draft_for_review`: Boolean - Flag para PM Trainee (sin email permission)

- `retention_amount`: Decimal - Amount held for warranty

- `is_draft_for_review`: Boolean - Flag for PM Trainee (no email permission)**Lógica de Negocio:**



**Business Logic:**```python

def calculate_net_payable(self) -> Decimal:

```python    """Calcula monto neto a pagar después de retención"""

def calculate_net_payable(self) -> Decimal:    return self.total_amount - self.retention_amount

    """Calculate net payable amount after retention"""

    return self.total_amount - self.retention_amountdef mark_for_admin_review(self, user):

    """Auto-detecta PM Trainee y marca invoice como draft"""

def mark_for_admin_review(self, user):    if not user.has_perm('core.can_send_external_emails'):

    """Auto-detect PM Trainee and mark invoice as draft"""        self.is_draft_for_review = True

    if not user.has_perm('core.can_send_external_emails'):        self.status = 'DRAFT'

        self.is_draft_for_review = True        # Notifica a admins para revisión

        self.status = 'DRAFT'```

        # Notify admins for review

```**Flujo de Trabajo:**

1. **Anticipo (deposit)**: Cliente paga % inicial antes de comenzar

**Workflow:**2. **Standard**: Facturación por progreso/items completados

1. **Deposit (deposit)**: Client pays % upfront before starting3. **Final**: Cierre de proyecto con balance restante - retención

2. **Standard**: Progress billing by completed items/phases

3. **Final**: Project close with remaining balance minus retention**Casos de Uso:**

- Cliente paga anticipo del 10% → `invoice_type='deposit'`

**Use Cases:**- Facturas periódicas por progreso → `invoice_type='standard'`

- Client pays 10% deposit → `invoice_type='deposit'`- Cierre de proyecto con retención 5% → `invoice_type='final', retention_amount=2500`

- Periodic progress invoices → `invoice_type='standard'`- PM Trainee crea invoice → Auto `is_draft_for_review=True`

- Project close with 5% retention → `invoice_type='final', retention_amount=2500`

- PM Trainee creates invoice → Auto `is_draft_for_review=True`---



---### 2. REEMBOLSOS A EMPLEADOS (Expenses)



### 2. EMPLOYEE REIMBURSEMENTS (Expenses)**Campos Nuevos:**

- `paid_by_employee`: FK a Employee - Quién pagó de su bolsillo

**New Fields:**- `reimbursement_status`: `['not_applicable', 'pending', 'paid_direct', 'next_paycheck', 'petty_cash']`

- `paid_by_employee`: FK to Employee - Who paid out of pocket- `reimbursement_date`: DateField - Cuándo se reembolsó

- `reimbursement_status`: `['not_applicable', 'pending', 'paid_direct', 'next_paycheck', 'petty_cash']`- `reimbursement_reference`: CharField - Referencia de pago/check

- `reimbursement_date`: DateField - When reimbursed

- `reimbursement_reference`: CharField - Payment/check reference**Lógica de Negocio:**



**Business Logic:**```python

def save(self, *args, **kwargs):

```python    """Auto-asigna status pending si empleado pagó"""

def save(self, *args, **kwargs):    if self.paid_by_employee and self.reimbursement_status == 'not_applicable':

    """Auto-assign pending status if employee paid"""        self.reimbursement_status = 'pending'

    if self.paid_by_employee and self.reimbursement_status == 'not_applicable':

        self.reimbursement_status = 'pending'def mark_reimbursed(self, method='paid_direct', reference='', user=None):

    """Marca como reembolsado y registra en AuditLog"""

def mark_reimbursed(self, method='paid_direct', reference='', user=None):    self.reimbursement_status = method

    """Mark as reimbursed and record in AuditLog"""    self.reimbursement_date = timezone.now().date()

    self.reimbursement_status = method    # Crea log de auditoría

    self.reimbursement_date = timezone.now().date()```

    # Create audit log entry

```**Nueva Categoría:**

- `HERRAMIENTAS`: Para gastos en herramientas que empleado compró

**New Category:**

- `TOOLS`: For tool expenses purchased by employee**Casos de Uso:**

- Empleado compra brocha urgente → `paid_by_employee=Jose, reimbursement_status='pending'`

**Use Cases:**- Admin reembolsa → `mark_reimbursed('paid_direct', 'CHK-1001')`

- Employee buys urgent brush → `paid_by_employee=Jose, reimbursement_status='pending'`- Reembolso en siguiente nómina → `mark_reimbursed('next_paycheck')`

- Admin reimburses → `mark_reimbursed('paid_direct', 'CHK-1001')`

- Reimbursement in next paycheck → `mark_reimbursed('next_paycheck')`---



---### 3. PLANNER INTELIGENTE (Tasks)



### 3. INTELLIGENT PLANNER (Tasks)**Campos Nuevos:**

- `schedule_weight`: IntegerField (0-100) - Prioridad en planner visual

**New Fields:**- `is_subtask`: Boolean - Si es subtarea de otra

- `schedule_weight`: IntegerField (0-100) - Priority in visual planner- `parent_task`: FK(self) - Tarea padre (jerarquía)

- `is_subtask`: Boolean - If subtask of another- `is_client_responsibility`: Boolean - Tarea bloqueante por cliente

- `parent_task`: FK(self) - Parent task (hierarchy)- `checklist`: JSONField - Lista verificable `[{item, checked}]`

- `is_client_responsibility`: Boolean - Task blocked by client- `initial_photo`: FK(PlanPin) - Foto inicial del pin asociado

- `checklist`: JSONField - Verifiable list `[{item, checked}]`- `completion_photo`: ImageField - Foto final de completación

- `initial_photo`: FK(PlanPin) - Associated pin's initial photo- `progress_percent`: IntegerField (0-100) - % de avance

- `completion_photo`: ImageField - Final completion photo

- `progress_percent`: IntegerField (0-100) - Progress percentage**Lógica de Negocio - Pin Cleanup:**



**Business Logic - Pin Cleanup:**```python

def save(self, *args, **kwargs):

```python    """Auto-oculta pins de tipo task/touchup al llegar a 100%"""

def save(self, *args, **kwargs):    is_new = self.pk is None

    """Auto-hide task/touchup pins when reaching 100%"""    if not is_new:

    is_new = self.pk is None        old_instance = Task.objects.get(pk=self.pk)

    if not is_new:        old_progress = old_instance.progress_percent

        old_instance = Task.objects.get(pk=self.pk)        

        old_progress = old_instance.progress_percent        # Si pasó de <100 a 100%

                if old_progress != 100 and self.progress_percent == 100:

        # If progressed from <100 to 100%            if self.initial_photo and self.initial_photo.pin_type in ['task', 'touchup']:

        if old_progress != 100 and self.progress_percent == 100:                self.initial_photo.is_visible = False

            if self.initial_photo and self.initial_photo.pin_type in ['task', 'touchup']:                self.initial_photo.save()

                self.initial_photo.is_visible = False    

                self.initial_photo.save()    super().save(*args, **kwargs)

    ```

    super().save(*args, **kwargs)

```**Casos de Uso:**

- **Checklist**: Validar pasos antes de marcar tarea completa

**Use Cases:**- **schedule_weight**: Priorizar tareas críticas en vista kanban

- **Checklist**: Validate steps before marking task complete- **is_client_responsibility**: Marcar tareas bloqueadas por cliente

- **schedule_weight**: Prioritize critical tasks in kanban view- **progress_percent**: Tracking granular (no solo Pendiente/Progreso/Completo)

- **is_client_responsibility**: Mark tasks blocked by client

- **progress_percent**: Granular tracking (not just Pending/In Progress/Complete)---



---### 4. GESTIÓN VISUAL AVANZADA (PlanPins)



### 4. ADVANCED VISUAL MANAGEMENT (PlanPins)**Campos Nuevos:**

- `owner_role`: CharField - Rol del creador (protección para Designer)

**New Fields:**- `is_visible`: Boolean - Visibilidad (para cleanup automático)

- `owner_role`: CharField - Creator role (protection for Designer)

- `is_visible`: Boolean - Visibility (for automatic cleanup)**Tipos de Pin Expandidos:**



**Expanded Pin Types:**```python

PIN_TYPES = [

```python    ('note', 'Nota General'),

PIN_TYPES = [    ('task', 'Tarea Pendiente'),      # ← Nuevo

    ('note', 'General Note'),    ('touchup', 'Touch-up/Retoque'),  # ← Nuevo

    ('task', 'Pending Task'),           # ← New    ('info', 'Información'),          # ← Nuevo

    ('touchup', 'Touch-up/Retouch'),   # ← New    ('hazard', 'Peligro/Hazard'),     # ← Nuevo

    ('info', 'Information'),            # ← New    ('leftover', 'Sobrante de Material'), # ← Nuevo (para inventario)

    ('hazard', 'Danger/Hazard'),        # ← New    # ... otros tipos existentes

    ('leftover', 'Material Leftover'),  # ← New (for inventory)]

    # ... other existing types```

]

```**Lógica de Negocio:**



**Business Logic:**```python

def save(self, *args, **kwargs):

```python    """Auto-asigna owner_role del creador"""

def save(self, *args, **kwargs):    if not self.owner_role and self.created_by:

    """Auto-assign owner_role from creator"""        if hasattr(self.created_by, 'profile'):

    if not self.owner_role and self.created_by:            self.owner_role = self.created_by.profile.role

        if hasattr(self.created_by, 'profile'):    super().save(*args, **kwargs)

            self.owner_role = self.created_by.profile.role```

    super().save(*args, **kwargs)

```**Pin Cleanup Workflow:**

1. PM crea pin tipo `task` en plano

**Pin Cleanup Workflow:**2. Crea Task asociado con `initial_photo = pin`

1. PM creates `task` type pin on floor plan3. Empleado trabaja, actualiza `progress_percent`

2. Creates Task associated with `initial_photo = pin`4. Al llegar a 100%, Task.save() oculta automáticamente el pin

3. Employee works, updates `progress_percent`5. Plano queda limpio, solo visible pins tipo `info`/`hazard`

4. Upon reaching 100%, Task.save() automatically hides pin

5. Floor plan stays clean, only `info`/`hazard` pins visible---



---### 5. INVENTARIO INTELIGENTE (ProjectInventory)



### 5. INTELLIGENT INVENTORY (ProjectInventory)**Campo Nuevo:**

- `reserved_quantity`: Decimal - Cantidad reservada por planner

**New Field:**

- `reserved_quantity`: Decimal - Quantity reserved by planner**Property Calculado:**



**Calculated Property:**```python

@property

```pythondef available_quantity(self):

@property    """Cantidad disponible para transferir/usar"""

def available_quantity(self):    return self.quantity - self.reserved_quantity

    """Available quantity for transfer/use"""```

    return self.quantity - self.reserved_quantity

```**Método Estrella - Transferencia Masiva:**



**Star Method - Bulk Transfer:**```python

@classmethod

```pythondef bulk_transfer(cls, project, category_list, exclude_leftover=True):

@classmethod    """

def bulk_transfer(cls, project, category_list, exclude_leftover=True):    Transfiere items de proyecto → Bodega Central al cerrar.

    """    EXCLUYE automáticamente items marcados como 'leftover' en PlanPins.

    Transfer items from project → Central Warehouse upon close.    

    AUTO-EXCLUDES items marked as 'leftover' in PlanPins.    Args:

            project: Proyecto origen

    Args:        category_list: ['PINTURA', 'HERRAMIENTA', ...]

        project: Source project        exclude_leftover: Si True, excluye sobrantes marcados

        category_list: ['PAINT', 'TOOLS', ...]    

        exclude_leftover: If True, exclude leftover-marked items    Returns:

            {

    Returns:            'success': True,

        {            'transfers': [InventoryMovement, ...],

            'success': True,            'total_transferred': Decimal('450.00')

            'transfers': [InventoryMovement, ...],        }

            'total_transferred': Decimal('450.00')    """

        }    # Implementación excluye items marcados como 'leftover' en PlanPins

    """```

    # Implementation excludes items marked as 'leftover' in PlanPins

```---



---### 6. COLORSAMPLES → PROJECT INTEGRATION



### 6. COLORSAMPLES → PROJECT INTEGRATION**Nuevos Campos en Project:**

- `approved_finishes`: JSONField - Dict de finishes aprobados

**New Fields in Project:**  ```json

- `approved_finishes`: JSONField - Dict of approved finishes  {

  ```json    "kitchen_cabinets": "WHITE_MATTE_001",

  {    "bathroom_tiles": "GREY_GLOSSY_045"

    "kitchen_cabinets": "WHITE_MATTE_001",  }

    "bathroom_tiles": "GREY_GLOSSY_045"  ```

  }

  ```**Workflow:**

1. Client aprueba ColorSample

**Workflow:**2. PM asigna a Project como `approved_finishes`

1. Client approves ColorSample3. Empleados ven finish especificado en app móvil

2. PM assigns to Project as `approved_finishes`4. Al completar, registro con foto confirma aplicación

3. Employees see specified finish in mobile app

4. Upon completion, record with photo confirms application---



---## DOCUMENTACIÓN DE VALIDACIÓN



## SYSTEM ARCHITECTURE### Para Lectores Técnicos



### Technology Stack**Contenido Original:**

- ARQUITECTURA_FINAL_IMPLEMENTADA.md - Especificación completa (773 líneas)

**Backend:**- CHECKLIST_VALIDACION_MANUAL.md - Tests manuales organizados por módulo

- **Framework:** Django 4.2+

- **Language:** Python 3.11+**Ubicación de Código:**

- **Database:** PostgreSQL 15+- `core/models.py` - Modelos con nuevos campos y métodos

- **Cache:** Redis 7+- `core/migrations/0096_final_architecture.py` - Migración base

- **Task Queue:** Celery with Redis broker- `core/tests/` - Suite de tests (738 passing)

- **WebSocket:** Django Channels with Redis channel layer

---

**Frontend:**

- **Framework:** Vue.js 3 / React (hybrid)## DECISIONES DE DISEÑO

- **UI Library:** Tailwind CSS

- **State Management:** Pinia / Redux### 1. Auto-ocultar Pins al Completar Tareas

- **Build Tool:** Vite**Decisión:** Ejecutar en Task.save() en lugar de signal

- **PWA:** Workbox service worker**Razón:** Evitar race conditions, mantener lógica centralizada

**Beneficio:** Planos siempre sincronizados con estado de tareas

**Infrastructure:**

- **Hosting:** Railway (auto-deploy on push to main)### 2. Retención de Facturas Flexible

- **Storage:** AWS S3 for media files**Decisión:** Campo configurable `retention_amount` por invoice

- **CDN:** CloudFront for static assets**Razón:** Permitir diferentes % según tipo de contrato

- **Monitoring:** Sentry for error tracking**Beneficio:** No hardcodear 5%, adaptable a clientes

- **CI/CD:** GitHub Actions

### 3. PM Trainee Draft Workflow

### Application Structure**Decisión:** Auto-marcar como draft si no tiene permiso de email

**Razón:** Evitar emails no autorizados sin necesidad de intervención manual

```**Beneficio:** Compliance automático

/kibray/

├── backend/---

│   ├── apps/

│   │   ├── calendar/          # HIGH PRIORITY - Calendar system## PRÓXIMOS PASOS

│   │   ├── financials/        # HIGH PRIORITY - Financial module

│   │   ├── ai_assistant/      # HIGH PRIORITY - AI Quick Mode### Corto Plazo (Dec 8-14)

│   │   ├── notifications/     # HIGH PRIORITY - Notification system- ✅ Documentación consolidada (este archivo)

│   │   ├── strategic_planner/ # HIGH PRIORITY - Planner- [ ] Deploy a staging environment

│   │   ├── projects/          # Core - Project management- [ ] QA final pass contra CHECKLIST_VALIDACION_MANUAL.md

│   │   ├── tasks/             # Core - Task system

│   │   ├── change_orders/     # Core - Change orders### Mediano Plazo (Dec 15-31)

│   │   ├── estimates/         # Core - Estimates- [ ] Deploy a production

│   │   ├── sop/               # MEDIUM - SOPs- [ ] Monitoreo de performance

│   │   ├── wizards/           # HIGH PRIORITY - Wizards- [ ] Feedback de usuarios

│   │   └── websocket/         # HIGH PRIORITY - Real-time

│   ├── core/### Largo Plazo (2026)

│   │   ├── permissions/       # Role-based access control- [ ] Optimización de bulk_transfer para inventarios masivos

│   │   ├── middleware/        # Custom middleware- [ ] Dashboard para tracking de retenciones

│   │   └── utils/             # Shared utilities- [ ] Mobile app updates para nuevos pin types

│   ├── api/                   # REST API endpoints

│   └── tests/                 # Test suite---

├── frontend/

│   ├── src/## REFERENCIAS

│   │   ├── components/        # Reusable components

│   │   ├── views/             # Page views### Documentos Consolidados

│   │   ├── services/          # API services- Original: ARQUITECTURA_FINAL_IMPLEMENTADA.md (773 líneas)

│   │   └── utils/             # Frontend utilities- Original: ARQUITECTURA_FINAL_README.md (421 líneas)

│   └── public/                # Static assets- Original: ARQUITECTURA_FINAL_RESUMEN_EJECUTIVO.md (561 líneas)

├── docs/                      # 9 master documents

├── docs_archive/              # Archived documentation### Archivado en: `_ARCHIVED_DOCS/`

├── legacy/                    # Legacy code (untouched)- Versiones anteriores se han archivado para historial

└── reports/                   # Generated reports- Consolidación completada: Diciembre 8, 2025

```

---

### Database Schema Highlights

**Última Actualización:** Diciembre 8, 2025  

**Key Models:****Status:** 🟢 LISTO PARA PRODUCCIÓN  

- `Project` - Central project entity**Mantenedor:** Sistema de Auditoría Automática

- `Task` - Granular task management
- `Invoice` - Flexible invoicing with types
- `Expense` - Employee reimbursements
- `ProjectInventory` - Material tracking
- `PlanPin` - Visual floor plan annotations
- `ColorSample` - Color approval workflow
- `Notification` - Multi-channel notifications
- `CalendarEvent` - Calendar entries
- `AuditLog` - Complete audit trail

**Performance Optimizations:**
- Database indexes on frequently queried fields
- Select/prefetch related for N+1 query prevention
- Redis caching for expensive queries
- Celery for async operations
- Connection pooling for Redis

---

## VALIDATION DOCUMENTATION

### For Technical Reviewers

**Original Content:**
- ARQUITECTURA_FINAL_IMPLEMENTADA.md - Complete specification (773 lines)
- CHECKLIST_VALIDACION_MANUAL.md - Manual tests organized by module

**Code Location:**
- `core/models.py` - Models with new fields and methods
- `core/migrations/0096_final_architecture.py` - Base migration
- `core/tests/` - Test suite (738 passing)

---

## DESIGN DECISIONS

### 1. Auto-Hide Pins on Task Completion
**Decision:** Execute in Task.save() instead of signal  
**Reason:** Avoid race conditions, keep logic centralized  
**Benefit:** Floor plans always synchronized with task state

### 2. Flexible Invoice Retention
**Decision:** Configurable `retention_amount` field per invoice  
**Reason:** Allow different percentages based on contract type  
**Benefit:** Don't hardcode 5%, adaptable to clients

### 3. PM Trainee Draft Workflow
**Decision:** Auto-mark as draft if no email permission  
**Reason:** Prevent unauthorized emails without manual intervention  
**Benefit:** Automatic compliance

### 4. Aggressive Code Modernization
**Decision:** Refactor freely while preserving business behavior  
**Reason:** Technical debt reduction, improved maintainability  
**Benefit:** Clean, modern codebase ready for future enhancements

### 5. English-Only Documentation
**Decision:** All documentation in English only  
**Reason:** International standard, better tooling support  
**Benefit:** Consistency, better developer experience

---

## SECURITY ARCHITECTURE

### Authentication & Authorization
- Django built-in authentication
- JWT tokens for API authentication
- Role-based access control (RBAC)
- Permission decorators on all endpoints
- Frontend UI element hiding per role

### Data Protection
- All secrets in Railway environment variables
- No secrets in codebase or version control
- HTTPS enforced in production
- CSRF protection enabled
- SQL injection prevention via ORM

### Audit Logging
- Complete audit trail for all modifications
- Who, what, when, where tracking
- Immutable audit log
- Retention policy compliance

---

## DEPLOYMENT ARCHITECTURE

### Deployment Workflow
1. Developer pushes to `main` branch
2. GitHub Actions runs full test suite
3. On test pass, Railway auto-deploys
4. Migrations run automatically
5. Static files collected to S3
6. Health checks validate deployment
7. Rollback on failure

### Environment Strategy
- **Development:** Local with SQLite/PostgreSQL
- **Staging:** Railway staging environment
- **Production:** Railway production with redundancy

### Monitoring & Alerts
- Sentry for error tracking
- Railway metrics for performance
- Custom health check endpoints
- Alert notifications for critical errors

---

## NEXT STEPS

### Short Term (Dec 8-14, 2025)
- ✅ Consolidated documentation (this file)
- ⏳ Create remaining 7 master documents
- ⏳ Complete Phase 1 consolidation
- [ ] Deploy to staging environment
- [ ] Final QA pass against validation checklist

### Medium Term (Dec 15-31, 2025)
- [ ] Code cleanup (588 orphans, 73 admin classes)
- [ ] Function documentation (70 functions)
- [ ] Legacy code migration to `/legacy/`
- [ ] Deploy to production
- [ ] Performance monitoring
- [ ] User feedback collection

### Long Term (2026)
- [ ] Optimize bulk_transfer for massive inventories
- [ ] Dashboard for retention tracking
- [ ] Mobile app updates for new pin types
- [ ] AI model improvements
- [ ] Advanced analytics and reporting

---

## REFERENCES

### Consolidated Documents
- Original: ARQUITECTURA_FINAL_IMPLEMENTADA.md (773 lines)
- Original: ARQUITECTURA_FINAL_README.md (421 lines)
- Original: ARQUITECTURA_FINAL_RESUMEN_EJECUTIVO.md (561 lines)

### Archived in: `docs_archive/architecture_docs/`
- Previous versions archived for history
- Consolidation completed: December 8, 2025

### Cross-References
- See **REQUIREMENTS_OVERVIEW.md** for system requirements
- See **MODULES_SPECIFICATIONS.md** for detailed module specs
- See **ROLE_PERMISSIONS_REFERENCE.md** for permission matrix
- See **API_ENDPOINTS_REFERENCE.md** for API documentation
- See **DEPLOYMENT_MASTER.md** for deployment procedures

---

**Last Updated:** December 8, 2025  
**Status:** 🟢 PRODUCTION READY  
**Maintainer:** Automated Audit System  
**Document Control:** Official Master Document #1 of 9

