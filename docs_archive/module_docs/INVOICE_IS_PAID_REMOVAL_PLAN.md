# Invoice.is_paid Removal Migration Plan (R3)

## Status: PREPARADO
**Fecha análisis**: 25 Nov 2025  
**Última ejecución check script**: 25 Nov 2025

---

## Análisis Actual

### Referencias en Código
- **1 referencia detectada** en `core/models.py:1575` (método `update_status`)
  - Uso: `update_fields=['status','paid_date','is_paid']`
  - Acción: Remover `is_paid` de `update_fields` y solo actualizar campos derivados necesarios

### Estado Base de Datos
- Total facturas: 2
- Discrepancias `is_paid` vs `fully_paid`: **0** ✅
- Sistema sincronizado correctamente tras refactor previo

### Dependencias Externas
- **Revisar manualmente**:
  - Serializers que expongan `is_paid` en respuesta API
  - Reportes o scripts que filtren por `is_paid`
  - Integraciones externas consumiendo este campo

---

## Plan de Ejecución (5 pasos)

### Paso 1: Actualizar Código (pre-migración)
**Archivos a modificar**:

1. `core/models.py` (Invoice.update_status):
   ```python
   # Antes:
   super(Invoice, self).save(update_fields=['status','paid_date','is_paid'])
   
   # Después:
   super(Invoice, self).save(update_fields=['status','paid_date'])
   ```

2. `core/api/serializers.py` (InvoiceSerializer):
   - Añadir campo computado `fully_paid` si no existe
   - Remover `is_paid` de `fields` list
   - Opcional: añadir deprecation warning en `to_representation()` durante periodo transitorio

3. Tests:
   - Buscar assertions sobre `invoice.is_paid`
   - Reemplazar por `invoice.fully_paid`

**Comando búsqueda global**:
```bash
grep -rn "\.is_paid" core/ tests/ --include="*.py" | grep -v migration
```

### Paso 2: Migración de Sincronización (si necesario)
Como actualmente **no hay discrepancias**, este paso se puede omitir.

Si en futuro se detectan:
```python
# core/migrations/XXXX_sync_invoice_is_paid.py
from django.db import migrations

def sync_is_paid(apps, schema_editor):
    Invoice = apps.get_model('core', 'Invoice')
    for invoice in Invoice.objects.all():
        expected = invoice.amount_paid >= invoice.total_amount if invoice.total_amount > 0 else False
        if invoice.is_paid != expected:
            invoice.is_paid = expected
            invoice.save(update_fields=['is_paid'])

class Migration(migrations.Migration):
    dependencies = [('core', 'XXXX_previous')]
    operations = [migrations.RunPython(sync_is_paid, migrations.RunPython.noop)]
```

### Paso 3: Migración de Remoción
```python
# core/migrations/XXXX_remove_invoice_is_paid.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [('core', 'XXXX_sync_or_previous')]
    
    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='is_paid',
        ),
        # Opcional: añadir constraint de sobrepago
        migrations.RunSQL(
            sql="ALTER TABLE core_invoice ADD CONSTRAINT check_payment_reasonable CHECK (amount_paid <= total_amount * 1.25);",
            reverse_sql="ALTER TABLE core_invoice DROP CONSTRAINT IF EXISTS check_payment_reasonable;"
        ),
    ]
```

### Paso 4: Actualizar Documentación
**Archivos**:
- `API_README.md`:
  - Sección "Breaking Changes": documentar remoción de `is_paid`
  - Indicar uso de `fully_paid` property (computed)
- `CHANGELOG.md`:
  - Entrada versión X.X.X: "BREAKING: Invoice.is_paid removed, use fully_paid computed property"
- `REQUIREMENTS_DOCUMENTATION.md`:
  - Actualizar ejemplos de Invoice que usen `is_paid`

### Paso 5: Validación Post-Migración
**Checklist**:
- [ ] Ejecutar suite de tests completa (sin errores relacionados con is_paid)
- [ ] Verificar dashboards financieros (Invoice Dashboard, Financial KPIs)
- [ ] Probar endpoints API: GET/POST/PATCH invoices (sin referencias a is_paid)
- [ ] Revisar logs durante 48h por warnings/errores
- [ ] Confirmar con usuarios piloto que reportes funcionan

**Rollback plan**:
- Si falla: revertir migración y restaurar campo `is_paid` temporalmente
- Re-sincronizar valores con script del Paso 2
- Investigar dependencias faltantes antes de reintentar

---

## Timeline Sugerido

| Fase | Acción | Duración | Responsable |
|------|--------|----------|-------------|
| Pre-migración | Paso 1 (actualizar código) | 1-2 hrs | Dev |
| Testing | Ejecutar tests + review manual | 30 min | Dev |
| Migración | Crear y aplicar migración (Paso 3) | 15 min | Dev |
| Validación | Post-deploy checks (Paso 5) | 48 hrs | Equipo |
| Documentación | Actualizar docs (Paso 4) | 1 hr | Dev |

**Total estimado**: 3-4 horas trabajo + 48h monitoreo

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Código externo usa is_paid | Media | Alto | Periodo de deprecación con warning logs antes de remover |
| Reportes SQL directos filtran por is_paid | Baja | Medio | Buscar en scripts/ y documentar alternativa (usar amount_paid >= total_amount) |
| Rollback complejo si hay datos nuevos | Baja | Medio | Backup BD antes de migración |

---

## Comandos Útiles

### Búsqueda de referencias
```bash
# Código Python
grep -rn "is_paid" core/ tests/ --include="*.py" | grep -v migration | grep -v "__pycache__"

# Templates (si aplica)
grep -rn "is_paid" core/templates/

# SQL raw (si hay queries hardcoded)
grep -rn "is_paid" . --include="*.sql"
```

### Verificación post-migración
```bash
# Confirmar campo removido
python manage.py dbshell -c "\d core_invoice" | grep is_paid

# Confirmar constraint (PostgreSQL)
python manage.py dbshell -c "SELECT conname FROM pg_constraint WHERE conrelid = 'core_invoice'::regclass;"
```

---

## Estado Actual: LISTO PARA PASO 1

✅ BD sincronizada  
⚠️  1 referencia en código (fácil de corregir)  
📋 Plan documentado

**Próxima acción recomendada**: Ejecutar Paso 1 (actualizar código) y luego crear migración.

---

_Generado automáticamente por `scripts/check_invoice_is_paid_usage.py`_
