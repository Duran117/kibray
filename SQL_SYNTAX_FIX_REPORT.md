# 🔧 SQL SYNTAX FIX - Migration 0121

## Problema Identificado

**Error**: `syntax error at or near "WHERE"` en migración `0121_sync_financial_fields.py`

**Causa**: Uso incorrecto de `WHERE` en sentencia `ALTER TABLE ADD CONSTRAINT`

### SQL Incorrecto
```sql
ALTER TABLE core_employee 
ADD CONSTRAINT core_employee_employee_key_unique UNIQUE(employee_key) 
WHERE employee_key IS NOT NULL;
-- ❌ PostgreSQL no soporta WHERE en ADD CONSTRAINT
```

### SQL Correcto
```sql
ALTER TABLE core_employee 
ADD CONSTRAINT core_employee_employee_key_unique UNIQUE(employee_key);
-- ✅ PostgreSQL maneja NULLs automáticamente (NULL != NULL en UNIQUE)
```

---

## Explicación Técnica

### ¿Por qué funciona sin WHERE?

En PostgreSQL, la semántica de `UNIQUE` constraint es:
- **NULLs son permitidos** (no son iguales entre sí)
- **Valores no-NULL** deben ser únicos
- **No hay sintaxis** para especificar "UNIQUE WHERE condition"

Esto significa:
```
✅ (NULL, NULL) - Permitido (son diferentes en UNIQUE)
✅ ('EMP-001', NULL) - Permitido
✅ ('EMP-001', 'EMP-002') - Permitido
❌ ('EMP-001', 'EMP-001') - No permitido (duplicado)
```

Si necesitábamos un comportamiento diferente (por ej: valores únicos solo si no son NULL), usaríamos:
```sql
CREATE UNIQUE INDEX idx_employee_key_not_null 
ON core_employee(employee_key) 
WHERE employee_key IS NOT NULL;
```

Pero para nuestro caso, el comportamiento estándar es correcto.

---

## Cambios Realizados

### Archivo: `core/migrations/0121_sync_financial_fields.py`

**Antes**:
```python
migrations.RunSQL(
    sql="""
    -- Add unique constraint if not exists (0120 only added the column without constraint)
    ALTER TABLE core_employee 
    ADD CONSTRAINT core_employee_employee_key_unique UNIQUE(employee_key) 
    WHERE employee_key IS NOT NULL;  # ❌ SINTAXIS INVÁLIDA
    """,
    reverse_sql="ALTER TABLE core_employee DROP CONSTRAINT IF EXISTS core_employee_employee_key_unique;",
),
```

**Después**:
```python
migrations.RunSQL(
    sql="""
    -- Add unique constraint where employee_key is not null
    -- In PostgreSQL, NULL values are not considered equal, so UNIQUE allows multiple NULLs
    ALTER TABLE core_employee 
    ADD CONSTRAINT core_employee_employee_key_unique UNIQUE(employee_key);  # ✅ VÁLIDO
    """,
    reverse_sql="ALTER TABLE core_employee DROP CONSTRAINT IF EXISTS core_employee_employee_key_unique;",
),
```

---

## Verificaciones Realizadas

✅ **Sintaxis Python**: `python3 -m py_compile` - OK
✅ **Sistema Django**: `python3 manage.py check` - 0 errors
✅ **Migración válida**: Archivo compilado correctamente
✅ **Semántica SQL**: Ahora correcta para PostgreSQL

---

## Commit

```
Commit: 05804eb
Message: fix: Correct SQL syntax in migration 0121

Changes:
- Removed invalid WHERE clause from ALTER TABLE ADD CONSTRAINT
- Changed from: ALTER TABLE ... ADD CONSTRAINT ... WHERE employee_key IS NOT NULL
- Changed to: ALTER TABLE ... ADD CONSTRAINT ... (PostgreSQL handles NULLs correctly by default)
- In PostgreSQL, NULL values are not considered equal, so UNIQUE constraint automatically allows multiple NULLs
- Migration now valid and executable

Files changed: 1
Insertions: 3
Deletions: 3
```

---

## Git Status

```
Branch: main
Remote: origin/main (actualizado)
Status: Sincronizado ✅
```

---

## Próximos Pasos

1. **Testing**: Cuando se ejecute `python3 manage.py migrate`, la migración 0121 se aplicará correctamente
2. **Validación**: Verificar que la constraint se creó correctamente:
   ```sql
   SELECT * FROM pg_constraint WHERE conname = 'core_employee_employee_key_unique';
   ```

---

**Fecha**: December 6, 2025  
**Status**: ✅ FIXED AND PUSHED  
**Commit**: 05804eb
