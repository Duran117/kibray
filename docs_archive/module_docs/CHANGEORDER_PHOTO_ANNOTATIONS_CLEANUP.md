# ChangeOrder Photo Annotations Cleanup

Fecha: 2025-11-15

## Objetivo
Normalizar y corregir anotaciones de fotos de Change Orders que fueron guardadas con doble codificación JSON (por ejemplo: una cadena que contiene otra cadena JSON) antes de la corrección del flujo de edición.

## Problema Original
- El frontend enviaba `JSON.stringify(currentAnnotations)` dentro de otro `JSON.stringify`.
- El backend guardaba el resultado tal cual en un `TextField`, creando valores como:
  ```
  "[\"{\\\"x\\\":10,...}\"]"
  ```
- Al abrir el editor, el parseo fallaba o las anotaciones aparecían vacías.

## Solución Implementada
1. Se modificó el frontend para enviar directamente el arreglo de anotaciones sin doble stringify.
2. El backend ahora detecta si la entrada es cadena doble codificada y la normaliza.
3. Se creó un comando de gestión para limpiar los registros antiguos.

## Comando de Limpieza
Archivo: `core/management/commands/cleanup_annotations.py`

### Uso
```bash
# Ver qué cambiaría sin aplicar modificaciones
python3 manage.py cleanup_annotations --dry-run --verbose

# Aplicar cambios realmente
python3 manage.py cleanup_annotations --verbose

# Limitar a los primeros 50 registros
python3 manage.py cleanup_annotations --limit 50 --verbose
```

### Salida Esperada
```
Photo #12: changed=True reason=double_encoded_struct
Photo #13: changed=False reason=already_ok_struct
...
Annotation cleanup complete
Total existing with annotations: 87
Processed: 87
Fixed: 42
Unchanged: 45
```

## Lógica de Normalización
1. Parseo inicial (`json.loads`):
   - Si produce lista/dict → Se re-serializa con `json.dumps` (formato limpio).
   - Si produce string → Se verifica si esa string parece JSON y se intenta segundo parseo.
2. Si el segundo parseo produce lista/dict → Se guarda una única versión limpia.
3. Si no es JSON válido → Se deja intacto.

## Idempotencia
El comando puede ejecutarse múltiples veces sin dañar datos; sólo modifica cuando detecta doble codificación o deserialización necesaria.

## Post-Limpieza
Después de ejecutar el comando:
- Abrir una foto con anotaciones previas.
- Verificar que cargan correctamente en el editor.
- Editar y guardar para confirmar nuevo formato estable.

## Preguntas Frecuentes (FAQ)
**¿Afecta a nuevas fotos?** No, sólo corrige las antiguas pre-parche.

**¿Puede afectar otras anotaciones (TouchUp, PlanPin)?** No, se limita a `ChangeOrderPhoto`.

**¿Qué pasa si interrumpo el comando?** Puedes re-ejecutarlo; es seguro.

**¿Necesito backup?** Recomendado siempre, pero el riesgo es bajo (solo normaliza JSON ya existente).

## Próximos Pasos Opcionales
- Migrar `annotations` a `JSONField` para acceso directo (requiere migration).
- Añadir validación del esquema (ej: cada anotación debe tener `type`, `points`, `color`).
- Implementar versionado de anotaciones para histórico.

---
Mantenido por: GitHub Copilot
