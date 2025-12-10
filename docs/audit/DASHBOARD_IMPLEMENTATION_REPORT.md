# Dashboard Coverage Report vs Backend (Informe)

**Date / Fecha:** 2025-12-10  
**Objective / Objetivo:** Identificar qué tan completo está el reflejo de las funciones de backend en los dashboards (sin escribir código).

## Scope and Method (Alcance y método)
- Revisión de vistas y templates de dashboards: `core/views_financial.py`, `core/views/bi_views.py` y `core/templates/core/dashboard_*.html` (por ejemplo, `dashboard_bi.html`, `financial_dashboard.html`, `dashboard_pm.html`, `dashboard_client.html`).
- Revisión de servicios/funciones de negocio: `core/services/financial_service.py` (cálculos T&M y BI) y modelos asociados.
- Revisión de APIs analíticas y tests: `tests/test_analytics_dashboards.py` (endpoints `analytics-project-health`, `analytics-touchups`, `analytics-color-approvals`, `analytics-pm-performance`).
- Búsqueda de uso de estos endpoints en la UI (`grep analytics core/templates/core`) → sin referencias en dashboards, lo que evidencia que no se consumen desde las vistas HTML actuales.

## Key Findings (Resumen ejecutivo)
1. **Cobertura parcial (~60-70%)**: Los dashboards visibles (Admin, PM, Financiero, BI, Cliente) muestran KPIs básicos, alertas y accesos rápidos, pero no exponen la mayoría de las analíticas detalladas ni varios flujos avanzados disponibles en backend.
2. **APIs analíticas no conectadas a UI**: Los endpoints validados en `tests/test_analytics_dashboards.py` están completos y probados, pero ningún dashboard los consume; no hay llamadas a `analytics-*` en los templates.
3. **Finanzas avanzadas sin UI dedicada**: La lógica de valuación T&M y cálculos financieros (`ChangeOrderService.get_billable_amount`, proyecciones de caja, márgenes) existe; los dashboards muestran KPIs y riesgos de inventario pero no incluyen vistas de valuación FIFO/LIFO, COGS ni flujo de aprobación de pagos/impuestos de nómina.
4. **Inventario y materiales en modo mínimo**: El BI sólo lista ítems críticos y el dashboard PM muestra “materiales pendientes”, pero no hay tableros con aging, valorización o rotación de inventario pese a que los modelos/servicios lo soportan.
5. **Nómina y desempeño**: El backend soporta payroll avanzado y métricas de desempeño (p.ej. `EmployeePerformanceMetric`), con templates dedicadas, pero no hay enlaces ni widgets en los dashboards principales (Admin/PM/Empleado) que expongan bonos, impuestos o cierres de periodo.
6. **Touch-ups / Color approvals / Salud de proyecto**: Las métricas existen vía API (completitud, aging, productividad PM), pero los dashboards siguen mostrando contadores básicos; no hay cards/gráficas que consuman esos endpoints.

## Coverage by Area (Detalle)
| Área backend | Evidencia de implementación | Superficie actual en dashboards | Vacíos detectados |
| --- | --- | --- | --- |
| **Finanzas & BI** | `core/views_financial.py`, `core/views/bi_views.py`, `core/services/financial_service.py` | `financial_dashboard.html` y `dashboard_bi.html` muestran KPIs, proyección de flujo, márgenes y riesgos de inventario. | Sin widgets de valuación FIFO/LIFO/AVG ni COGS; no se muestran cuentas por cobrar detalladas ni workflows de pago/impuestos. |
| **Analíticas (salud de proyecto, touch-ups, approvals, PM performance)** | Endpoints probados en `tests/test_analytics_dashboards.py` | Ningún dashboard HTML llama a `analytics-*`; no hay gráficas/cards usando esos datos. | La funcionalidad analítica está operativa en backend pero no visible en UI. |
| **Inventario / Materiales** | Modelos y servicios completos; riesgos listados en BI | BI muestra “Inventory Critical List”; PM muestra “Materiales Pendientes”. | Falta dashboard de valorización/aging, rotación y umbrales configurables; no se exponen métodos FIFO/LIFO/AVG. |
| **Nómina avanzada** | Modelos y vistas (`PayrollRecord`, cálculos en backend) | No hay widgets ni accesos directos en dashboards principales; sólo templates aisladas (`payroll_summary.html`, etc.). | Sin visibilidad de impuestos, bonos, cierres de periodo ni históricos de pagos en dashboards. |
| **Change Orders T&M** | `ChangeOrderService.get_billable_amount` (desglose T&M) | Dashboards sólo linkean a tableros CO; no muestran breakdown ni alertas de facturación. | Falta card que exponga horas/materiales no facturados y markup aplicado. |
| **Desempeño de empleados** | `EmployeePerformanceMetric` y templates dedicadas | Sin referencias en `dashboard_admin.html` / `dashboard_pm.html` / `dashboard_employee.html`. | No hay vista rápida de KPIs de desempeño, bonos o certificaciones desde dashboards. |
| **Cliente / Portal** | `dashboard_client.html` muestra fotos, facturas, solicitudes y progreso | Cliente sí ve progreso e invoices, pero sin flujos de aprobación/firmas digitales ni pagos en línea. | Añadir acciones para aprobar/firmar y pagar facturas directamente desde el dashboard. |

## Specific Recommendations (Recomendaciones)
- Conectar los endpoints de analítica (`analytics-*`) a los dashboards mediante llamadas fetch/AJAX o vistas que inyecten los datos ya probados.
- Añadir cards en Financial/BI para: valuación de inventario (FIFO/LIFO/AVG), COGS, aging de AR/AP y backlog de change orders con breakdown T&M.
- Incorporar widgets de nómina (periodo activo, impuestos calculados, bonos pendientes) y accesos rápidos a cierres.
- Exponer métricas de desempeño y touch-ups (rates, aging, prioridades) en dashboards Admin/PM con los datos existentes.
- Extender el dashboard cliente con botones de aprobación/firmado y opciones de pago si el flujo de backend ya lo permite.
