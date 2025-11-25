# Arquitectura de Dashboards - Sistema Kibray

## 📊 Estructura de Dashboards

El sistema Kibray tiene dos dashboards complementarios para administradores:

### 1. Dashboard Operativo (`/dashboard/admin/`)
**Propósito:** Operaciones diarias, monitoreo y aprobaciones rápidas

**Características:**
- ✅ Métricas financieras en tiempo real (ingresos, gastos, profit)
- ✅ Alertas críticas del sistema:
  - Time entries sin asignar a Change Orders
  - Solicitudes de clientes pendientes
  - Change Orders pendientes de aprobación
  - Facturas pendientes de pago
- ✅ Proyectos con alertas de Earned Value (SPI/CPI)
- ✅ Resumen de nómina y tiempo trabajado
- ✅ Gráficos visuales (Income vs Expenses, distribución de alertas)
- ✅ Acciones rápidas a secciones operativas

**Cuándo usar:**
- Monitoreo diario de operaciones
- Revisión de métricas y KPIs
- Aprobaciones y seguimiento de workflows
- Detección de problemas y alertas

### 2. Panel Administrativo Avanzado (`/admin-panel/`)
**Propósito:** Configuración del sistema y gestión de datos

**Características:**
- ✅ CRUD completo de usuarios, grupos y permisos
- ✅ CRUD de todos los modelos del sistema:
  - Proyectos
  - Gastos
  - Ingresos
  - Time Entries
  - Change Orders
  - Floor Plans
  - Schedules
  - Tasks
- ✅ Logs de auditoría y actividad
- ✅ Filtros avanzados, búsqueda y paginación
- ✅ Acciones en lote (próximamente)
- ✅ Exportación/importación CSV (próximamente)

**Cuándo usar:**
- Configuración inicial del sistema
- Gestión de usuarios y permisos
- Edición masiva de datos
- Auditoría de cambios
- Corrección de datos incorrectos
- Administración de parámetros del sistema

## 🔄 Flujo de Trabajo Recomendado

```
Inicio de día → Dashboard Operativo
  ├─ Revisar alertas críticas
  ├─ Aprobar COs y solicitudes
  ├─ Monitorear métricas
  └─ Detectar problemas
  
Necesitas crear/editar/eliminar → Panel Administrativo
  ├─ Crear usuario nuevo
  ├─ Editar datos de proyecto
  ├─ Eliminar registros incorrectos
  └─ Ver logs de auditoría
  
Fin de día → Dashboard Operativo
  └─ Revisar totales y KPIs del día
```

## 📱 Navegación

**Desde Dashboard Operativo:**
- Botón "Panel Administrativo" en la parte superior → Abre `/admin-panel/`

**Desde Panel Administrativo:**
- Botón "Dashboard Operativo" en la parte superior → Abre `/dashboard/admin/`

## 🎯 Separación de Responsabilidades

| Función | Dashboard Operativo | Panel Administrativo |
|---------|---------------------|---------------------|
| Ver métricas/KPIs | ✅ | ❌ |
| Alertas y notificaciones | ✅ | ❌ |
| Aprobaciones rápidas | ✅ | ❌ |
| Crear usuarios | ❌ | ✅ |
| Editar datos CRUD | ❌ | ✅ |
| Ver logs de auditoría | ❌ | ✅ |
| Gestionar permisos | ❌ | ✅ |
| Gráficos visuales | ✅ | ❌ |
| Filtros avanzados | ❌ | ✅ |

## ✅ Decisión Final

**Mantener ambos dashboards** porque:
1. Dashboard Operativo → Uso diario, monitoreo, decisiones rápidas
2. Panel Administrativo → Configuración, gestión de datos, auditoría
3. No se solapan en funcionalidad
4. Cada uno optimizado para su caso de uso específico

## 🚀 Próximas Mejoras

**Dashboard Operativo:**
- [ ] Widget de tareas pendientes
- [ ] Notificaciones en tiempo real
- [ ] Exportar reportes PDF
- [ ] Más gráficos interactivos

**Panel Administrativo:**
- [x] CRUD de Proyectos
- [x] CRUD de Gastos
- [x] CRUD de Ingresos
- [ ] CRUD de Time Entries
- [ ] CRUD de Tasks
- [ ] CRUD de Change Orders
- [ ] Filtros avanzados
- [ ] Acciones en lote
- [ ] Exportación CSV
- [ ] Importación CSV
- [ ] Ordenamiento por columnas

---

**Última actualización:** Nov 19, 2025
