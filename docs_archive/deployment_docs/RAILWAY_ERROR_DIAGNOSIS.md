# 🔧 DIAGNÓSTICO DE ERRORES - RAILWAY DEPLOYMENT

**Fecha**: Diciembre 5, 2025

---

## 🚨 ERRORES COMUNES EN RAILWAY Y SOLUCIONES

### 1. **ERROR: AWS S3 Credentials Missing**

**Síntoma**:
```
ImproperlyConfigured: AWS_ACCESS_KEY_ID not set
```

**Causa**: `USE_S3` está por defecto `True` pero no hay AWS configurado

**Solución**:

En Railway dashboard → Servicio **web** → Variables:

Agrega esta variable:
```
Name:  USE_S3
Value: False
```

**O** si quieres usar S3, agrega:
```
USE_S3 = True
AWS_ACCESS_KEY_ID = tu-access-key
AWS_SECRET_ACCESS_KEY = tu-secret-key
AWS_STORAGE_BUCKET_NAME = kibray-media
AWS_S3_REGION_NAME = us-east-1
```

---

### 2. **ERROR: DATABASE_URL not set**

**Síntoma**:
```
OperationalError: FATAL: password authentication failed
```

**Causa**: PostgreSQL no fue agregado o DATABASE_URL no está disponible

**Solución**:

En Railway → Proyecto → Click **+ New** → **Database** → **PostgreSQL**

Railway automáticamente crea `DATABASE_URL`.

---

### 3. **ERROR: REDIS_URL not set**

**Síntoma**:
```
ConnectionError: Error 111 connecting to localhost:6379
```

**Causa**: Redis no fue agregado

**Solución**:

En Railway → Proyecto → Click **+ New** → **Database** → **Redis**

Railway automáticamente crea `REDIS_URL`.

---

### 4. **ERROR: ALLOWED_HOSTS validation failed**

**Síntoma**:
```
SuspiciousOperation: Invalid HTTP_HOST header: 'kibraypainting.up.railway.app'
```

**Causa**: Variable `ALLOWED_HOSTS` no configurada o valor incorrecto

**Solución**:

En Railway Dashboard → Variables, verifica:
```
ALLOWED_HOSTS = kibraypainting.up.railway.app,*.railway.app
```

**Exactamente así** (sin http://, sin trailing slash)

---

### 5. **ERROR: CSRF Verification Failed (403)**

**Síntoma**:
```
403 Forbidden - CSRF verification failed
Origin check failed
```

**Causa**: `CSRF_TRUSTED_ORIGINS` no configurada o mal escrita

**Solución**:

En Railway Dashboard → Variables:
```
CSRF_TRUSTED_ORIGINS = https://kibraypainting.up.railway.app
```

**Importante**:
- ✅ Incluir `https://`
- ✅ Sin trailing `/`
- ✅ Sin espacios

---

### 6. **ERROR: Collectstatic failed**

**Síntoma**:
```
ERROR: The file is in the middleware, but not in STATIC_ROOT
```

**Causa**: Static files no se compilaron correctamente

**Solución**:

Esto es normal en Railway. La solución está en `railway.json`:

```json
{
  "build": {
    "buildCommand": "pip install -r requirements.txt && python manage.py collectstatic --noinput"
  },
  "deploy": {
    "startCommand": "python manage.py migrate --noinput && gunicorn kibray_backend.wsgi:application --config gunicorn.conf.py"
  }
}
```

✓ Este archivo ya está correcto.

---

### 7. **ERROR: Migrations failed**

**Síntoma**:
```
ERROR: relation "core_task" does not exist
```

**Causa**: Migraciones no corrieron

**Solución**:

Railway automáticamente corre migraciones en `startCommand`.

Si aún falla:
1. Ve a Railway → servicio web → **Connect** (terminal)
2. Ejecuta manualmente:
   ```bash
   python manage.py migrate --noinput
   ```

---

### 8. **ERROR: Port not exposed**

**Síntoma**:
```
Connection refused
```

**Causa**: El servicio web no está exponiendo el puerto correctamente

**Solución**:

En Railway → servicio web → **Settings** → Networking:
- Verifica que haya un puerto expuesto
- Railway debería auto-detectar puertos desde `gunicorn.conf.py`

---

## ✅ CHECKLIST MÍNIMO PARA QUE FUNCIONE

- [ ] PostgreSQL agregado (DATABASE_URL auto-creada)
- [ ] Redis agregado (REDIS_URL auto-creada)
- [ ] DJANGO_SECRET_KEY configurada
- [ ] DJANGO_ENV = `production`
- [ ] ALLOWED_HOSTS = `kibraypainting.up.railway.app,*.railway.app`
- [ ] CSRF_TRUSTED_ORIGINS = `https://kibraypainting.up.railway.app`
- [ ] CORS_ALLOWED_ORIGINS = `https://kibraypainting.up.railway.app`
- [ ] USE_S3 = `False` (si no tienes AWS) o completa credenciales AWS
- [ ] railway.json en root del proyecto ✓
- [ ] Procfile en root del proyecto ✓

---

## 🔍 CÓMO VER LOGS EN RAILWAY

1. https://railway.app → Proyecto **Kibray Painting**
2. Servicio **web**
3. Pestaña **Logs**
4. Scroll down para ver errors

Los logs te dirán exactamente qué está fallando.

---

## 🚨 ERRORES ESPECÍFICOS VISTO FRECUENTEMENTE

### "ModuleNotFoundError: No module named 'channels'"
**Solución**: `pip install -r requirements.txt` está en buildCommand ✓ (ya está)

### "Port already in use"
**Solución**: Railway auto-asigna puertos, ignora este error en local

### "No such file: gunicorn.conf.py"
**Solución**: Verifica que `gunicorn.conf.py` existe en root (ya está ✓)

### "Health check timeout"
**Solución**: La app tarda >300s en iniciar. Aumenta timeout en railway.json

---

## 🎯 PRÓXIMOS PASOS

1. **Comparte el error exacto** que ves en Railway logs
2. **Verifica todas las variables** están configuradas en Railway dashboard
3. **Ejecuta** `railway status` para ver qué servicios están online
4. **Revisa los logs** en Railway dashboard pestaña "Logs"

**Si ves el error específico, puedo darte la solución exacta.**

---

## 📋 VARIABLES CHECKLIST COMPLETO

Copia todas estas en Railway Variables:

```
DJANGO_SECRET_KEY=h9igi_p7yxtv2zh6!pbz@_py467lszlrp(a5)b90f@_-q!j@a#
DJANGO_ENV=production
ALLOWED_HOSTS=kibraypainting.up.railway.app,*.railway.app
CSRF_TRUSTED_ORIGINS=https://kibraypainting.up.railway.app
CORS_ALLOWED_ORIGINS=https://kibraypainting.up.railway.app
USE_S3=False
```

**NO NECESITAS**:
- DATABASE_URL (Railway lo crea)
- REDIS_URL (Railway lo crea)
- PORT (Railway lo asigna)

---

**Comparte el error específico y te ayudaré a solucionarlo.**
