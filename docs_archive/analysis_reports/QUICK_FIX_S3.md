# SOLUCIÓN RÁPIDA: CAMBIAR USE_S3 A FALSE

El archivo `kibray_backend/settings/production.py` tiene `USE_S3 = True` por defecto.

Esto causa error si no tienes AWS configurado.

## OPCIÓN 1: Agregar Variable a Railway (MÁS FÁCIL)

En Railway dashboard → servicio web → Variables:

Agrega:
```
Name:  USE_S3
Value: False
```

Luego redeploy. El problema se resuelve.

## OPCIÓN 2: Modificar production.py localmente (Alternativa)

Edita el archivo: `kibray_backend/settings/production.py`

Busca línea 36:
```python
USE_S3 = os.getenv("USE_S3", "True") == "True"
```

Cámbialo a:
```python
USE_S3 = os.getenv("USE_S3", "False") == "True"
```

Luego:
```bash
git add kibray_backend/settings/production.py
git commit -m "Change USE_S3 default to False for local file storage"
git push origin main
```

Railway automáticamente redeploy.

## OPCIÓN 3: Usar AWS S3 (Si quieres almacenamiento en cloud)

Agrega estas variables en Railway:

```
USE_S3=True
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=kibray-media
AWS_S3_REGION_NAME=us-east-1
```

---

**Recomendación: Usa OPCIÓN 1 o 2** (sin S3 para empezar)

Después puedes agregar AWS S3 cuando lo necesites.
