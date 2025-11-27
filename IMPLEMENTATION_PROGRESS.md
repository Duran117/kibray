# 📍 Mapa de Progreso – Kibray

Fecha: 2025-11-27

Este archivo resume el estado real del proyecto (código + pruebas) frente a los requisitos documentados. Se actualiza para mantener el rumbo y evitar retrabajo.

## ✅ Resumen Ejecutivo

- Documentación de requisitos: 48/250+ funciones ≈ 19% documentado (según `REQUIREMENTS_DOCUMENTATION.md`).
- Implementación de módulos ya documentados (M1–M6): ≈ 78% cumplido.
- Estado global de pruebas: 513/513 tests PASS.
- Servidor de desarrollo: operativo local; migraciones aplicadas; sin errores de sistema.

Notas clave:
- FASE 2 (Módulo 11: Tasks) completada con API y tests focalizados.
- Facturación (M6) cuenta con estados y pagos parciales implementados; faltan detalles de PDF y paneles.
- Finanzas (Gastos/Ingresos) funcionan, pero faltan algunos campos y flujos de aprobación/soporte general.

## 📊 Cobertura por Módulo (documentados)

Escala: 0–100%. Valores basados en verificación de modelos/vistas/servicios y tests actuales.

- Módulo 1 – Proyectos: 80%
  - Implementado: Proyecto, presupuestos, EV, schedules, dashboards por rol, minutas, CO integrado.
  - Pendiente: numeración automática de proyecto; notificación al asignar PM; firmas digitales para colores.

- Módulo 2 – Empleados: 85%
  - Implementado: CRUD empleado, vinculación User/Profile, activo/inactivo, tarifa/hora, historial básico; lógica de almuerzo aplicada en TimeEntry.
  - Pendiente: Employee Key inmutable (EMP-001…); flujos de aprobación en cambios sensibles (formalizados).

- Módulo 3 – Time Tracking: 95%
  - Implementado: clock in/out, deducción de almuerzo (≥5h y cruza 12:30), multi‑proyecto/CO, costo labor, vistas por empleado/proyecto, histórico.
  - Pendiente: lock post‑payroll; validación GPS futura.

- Módulo 4 – Gastos: 60%
  - Implementado: Expense con recibos, categorías, CO y cost codes; vistas y sumatorias por proyecto/categoría/fecha.
  - Pendiente: expense_type (PROJECT/GENERAL), vendor/método de pago/referencia, estado de pago (pending/partial/paid), múltiples recibos, compresión y alertas.

- Módulo 5 – Ingresos: 70%
  - Implementado: Income con método de pago, vinculación a proyecto/invoice, historial y métricas básicas.
  - Pendiente: ingresos “generales” sin proyecto; comprobantes con vista previa y alertas; dashboard con aging y proyección (Cash Flow Tool).

- Módulo 6 – Facturación: 80%
  - Implementado: numeración automática, estados (draft/sent/viewed/partial/paid/overdue/cancelled), pagos parciales (`InvoicePayment`) y sincronización de `amount_paid`/`balance`; vínculo automático a `Income`.
  - Pendiente: PDF profesional (WeasyPrint/ReportLab), dashboard financiero (KPI: facturado vs cobrado, aging AR/AP), acción de envío por email con tracking.

- Módulo 11 – Tasks (FASE 2): 100%
  - Implementado: prioridades, dependencias (con ciclo‑check), due_date, tracking start/stop, versionado de imágenes, reopen con señales, métricas de tiempo (total_hours), API con acciones; 69 tests focalizados añadidos y pasando.

Promedio (M1–M6): ≈ 78%.

## 🧪 Calidad y compuertas

- Build: PASS
- Lint/Typecheck: pendiente integrar verificación automática (propuesto abajo)
- Tests: PASS (513/513)

## 🚩 Riesgos y brechas relevantes

- Firmas digitales (colores y COs) – legal/compliance.
- Gastos sin estado de pago ni vendor – reduce trazabilidad de CxP.
- Ingresos generales – falta soporte; sesga análisis de cash‑flow.
- PDFs de factura – mejorar presentación para cliente.
- Detección de código duplicado – integrar estático para evitar regresiones.

## 🔧 Acciones siguientes (priorizadas)

1) Finanzas – Gastos (M4)
- Agregar: expense_type (PROJECT/GENERAL), vendor, payment_status, amount_paid, payment_date, payment_method, payment_reference.
- Galería de múltiples recibos y compresión opcional.

2) Finanzas – Ingresos (M5)
- Ingresos generales (sin proyecto) con validaciones y comprobantes.
- Panel de ingresos con filtros + aging básico; alertas de vencidos.

3) Facturación (M6)
- PDF profesional (plantilla HTML+CSS y/o WeasyPrint) y acción “Enviar al cliente” con tracking.
- Dashboard financiero (KPI: facturado vs cobrado, aging AR/AP).

4) Proyectos (M1)
- Numeración automática PRJ‑#### y notificación de asignación de PM.
- Flujo de firmas digitales en gestión de colores.

5) Calidad estática
- Integrar ruff + flake8‑bugbear y un detector de duplicados (ej. jscpd o flake8‑dupe‑code) en CI.

## 📌 Hechos verificados hoy

- Tests globales: 513 PASS.
- Task API y lógica de reopen/time tracking: estable; sin duplicidad de eventos (señales centralizadas).
- Invoice + pagos parciales: presentes en modelos; estados sincronizados.

## 🗺️ Cómo usar este mapa

- Al cerrar una acción de arriba, actualizar el porcentaje del módulo correspondiente y mover la tarea a “Hecho”.
- Si el chat se interrumpe, retomar desde la sección “Acciones siguientes” y validar “Hechos verificados hoy”.

---

Glosario rápido:
- M#: número de módulo según `REQUIREMENTS_DOCUMENTATION.md`.
- PASS: compilación/ejecución de tests sin errores.
- Aging: antigüedad de cuentas por cobrar/pagar.
