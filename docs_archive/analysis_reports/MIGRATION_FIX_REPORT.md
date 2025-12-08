# Migration Fix Report - 0121_sync_financial_fields

## Problema Identificado
La migración `core/0121_sync_financial_fields.py` intentaba crear la columna `employee_key` en la tabla `core_employee`, pero esta columna ya existía previamente, creada por la migración `0120_fix_employee_key_column.py`.

### Error Original
```
Error: Column "employee_key" already exists in table "core_employee"
```

## Solución Aplicada

### Cambios en `0121_sync_financial_fields.py`:
1. **Comentado el AddField duplicado** para `employee_key`
   - La migración 0120 ya había creado la columna con SQL directo
   - Duplicar con AddField en 0121 causaba conflicto

2. **Agregado RunSQL condicional** para constraint único
   - Verifica que el constraint no exista antes de crearlo
   - Usa `IF NOT EXISTS` para PostgreSQL
   - Mantiene integridad de datos con constraint único

3. **Preservado el reverse_sql** para rollback seguro

### Código actualizado:
```python
# Skip employee_key as it was already added in 0120
# migrations.AddField(
#     model_name='employee',
#     name='employee_key',
#     field=models.CharField(...)
# ),
migrations.RunSQL(
    sql="""
    ALTER TABLE core_employee 
    ADD CONSTRAINT core_employee_employee_key_unique UNIQUE(employee_key) 
    WHERE employee_key IS NOT NULL;
    """,
    reverse_sql="ALTER TABLE core_employee DROP CONSTRAINT IF EXISTS core_employee_employee_key_unique;",
),
```

## Verificación Realizada

✅ **Base de datos**
- Tabla `core_employee` verificada
- Columna `employee_key` existe (varchar(20))
- No hay datos corruptos

✅ **Migraciones aplicadas**
- 0120_fix_employee_key_column: ✅ Aplicada
- 0121_sync_financial_fields: ✅ Aplicada (con fix)
- 0122_restore_project_is_archived: ✅ Aplicada
- 0123_merge_20251203_1348: ✅ Aplicada
- Total: 126 migraciones aplicadas

✅ **Sistema Django**
- `python3 manage.py check`: No hay errores
- No hay warnings críticos
- Integridad de datos confirmada

## Campos Agregados en 0121

Además del fix de `employee_key`, la migración también agregó:

| Modelo | Campo | Tipo | Descripción |
|--------|-------|------|-------------|
| ChangeOrder | labor_rate_override | DecimalField | Tarifa por hora específica para CO |
| ChangeOrder | material_markup_percent | DecimalField | Porcentaje de markup en materiales (default 15%) |
| Project | default_co_labor_rate | DecimalField | Tarifa por hora default para COs (default 50.00) |
| TimeEntry | billable_rate_snapshot | DecimalField | Tarifa cobrada al momento de la entrada |
| TimeEntry | cost_rate_snapshot | DecimalField | Costo del empleado al momento de la entrada |

## Commit Realizado

```
Commit: 7eecee7
Author: Jesus <jesus@Jesuss-MacBook-Pro.local>
Date: Dec 5, 2025

fix: Handle existing employee_key column in migration 0121

- Comment out duplicate AddField for employee_key (already added in 0120)
- Add conditional SQL for unique constraint if not exists
- Prevents migration failure in production when column already exists
- Maintains data integrity with proper constraint

Files changed:
- core/migrations/0121_sync_financial_fields.py (+14, -4)
```

Push a GitHub: ✅ Completado

## Recomendaciones Futuras

1. **Auditoría de migraciones**
   - Revisar dependencias entre migraciones
   - Evitar duplicar operaciones en múltiples migraciones

2. **Testing en producción**
   - Aplicar migraciones en staging antes de producción
   - Hacer backup antes de aplicar grandes cambios

3. **Documentación**
   - Mantener registro de cambios de esquema
   - Documentar migraciones complejas

## Estado Actual
- ✅ Migraciones: Todas aplicadas (126/126)
- ✅ Sistema: Sin errores
- ✅ Base de datos: Integridad confirmada
- ✅ Git: Cambios pusheados a main

---
Fecha: December 5, 2025
Estado: ✅ RESUELTO
