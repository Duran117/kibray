# 🚀 Valores para Copiar/Pegar en Railway

## 📋 PASO A PASO

### 1. Ve a Railway Dashboard
→ https://railway.app
→ Selecciona proyecto: **lovely-adventure**
→ Click en servicio: **web**
→ Click en pestaña: **Variables**

---

## 🔐 VARIABLES OBLIGATORIAS

Copia y pega estos valores exactos:

### Variable 1: DJANGO_SECRET_KEY
```
Name:  DJANGO_SECRET_KEY
Value: h9igi_p7yxtv2zh6!pbz@_py467lszlrp(a5)b90f@_-q!j@a#
```

### Variable 2: DJANGO_ENV
```
Name:  DJANGO_ENV
Value: production
```

### Variable 3: ALLOWED_HOSTS
⚠️ **IMPORTANTE:** Necesitas reemplazar `XXXXXX` con tu dominio real de Railway.

Para encontrar tu dominio:
1. Railway → servicio **web** → pestaña **Settings**
2. Busca "Domains" o "Public Networking"
3. Copia el dominio (algo como: `lovely-adventure-production-1a2b.up.railway.app`)

```
Name:  ALLOWED_HOSTS
Value: TU-DOMINIO.up.railway.app,*.railway.app
```

**Ejemplo:**
```
Value: lovely-adventure-production-1a2b.up.railway.app,*.railway.app
```

### Variable 4: CSRF_TRUSTED_ORIGINS
```
Name:  CSRF_TRUSTED_ORIGINS
Value: https://TU-DOMINIO.up.railway.app
```

**Ejemplo:**
```
Value: https://lovely-adventure-production-1a2b.up.railway.app
```

### Variable 5: CORS_ALLOWED_ORIGINS
```
Name:  CORS_ALLOWED_ORIGINS
Value: https://TU-DOMINIO.up.railway.app
```

**Ejemplo:**
```
Value: https://lovely-adventure-production-1a2b.up.railway.app
```

---

## 🤖 VARIABLE OPCIONAL - OpenAI (Features de AI)

### Variable 6: OPENAI_API_KEY
```
Name:  OPENAI_API_KEY
Value: [tu-secret-key-que-ya-tienes-del-business-account]
```

**Ejemplo:**
```
Value: sk-proj-abc123def456xyz789...
```

---

## 📧 VARIABLES OPCIONALES - Email (Notificaciones)

Solo si quieres enviar emails desde la app:

```
Name:  EMAIL_HOST
Value: smtp.gmail.com
```

```
Name:  EMAIL_PORT
Value: 587
```

```
Name:  EMAIL_USE_TLS
Value: True
```

```
Name:  EMAIL_HOST_USER
Value: tu-email@gmail.com
```

```
Name:  EMAIL_HOST_PASSWORD
Value: tu-app-password-de-gmail
```

```
Name:  DEFAULT_FROM_EMAIL
Value: Kibray <noreply@kibray.com>
```

---

## ☁️ VARIABLES OPCIONALES - AWS S3 (Archivos/Imágenes)

Solo si quieres guardar archivos en AWS S3:

```
Name:  USE_S3
Value: True
```

```
Name:  AWS_ACCESS_KEY_ID
Value: AKIAXXXXX
```

```
Name:  AWS_SECRET_ACCESS_KEY
Value: tu-secret-key-de-aws
```

```
Name:  AWS_STORAGE_BUCKET_NAME
Value: kibray-media
```

```
Name:  AWS_S3_REGION_NAME
Value: us-east-1
```

---

## 🔧 VARIABLES QUE RAILWAY CREA AUTOMÁTICAMENTE

**NO necesitas crear estas manualmente:**

✅ `DATABASE_URL` - Railway la crea cuando agregas PostgreSQL
✅ `REDIS_URL` - Railway la crea cuando agregas Redis
✅ `PORT` - Railway la configura automáticamente

---

## 📝 Checklist de Variables Mínimas

Para que funcione el backend necesitas:

- [x] ✅ DJANGO_SECRET_KEY (ya tienes el valor arriba)
- [x] ✅ DJANGO_ENV=production
- [ ] ⚠️ ALLOWED_HOSTS (necesitas tu dominio de Railway)
- [ ] ⚠️ CSRF_TRUSTED_ORIGINS (necesitas tu dominio)
- [ ] ⚠️ CORS_ALLOWED_ORIGINS (necesitas tu dominio)
- [ ] 🤖 OPENAI_API_KEY (opcional - para AI features)

---

## 🚀 Siguiente Paso

1. **Agrega Postgres y Redis:**
   - Railway → proyecto lovely-adventure → **+ New**
   - Click **Database** → **Add PostgreSQL**
   - Click **+ New** otra vez → **Database** → **Add Redis**

2. **Agrega las variables:**
   - Railway → servicio **web** → **Variables**
   - Copia/pega las variables de arriba

3. **Ejecuta migraciones:**
   ```bash
   # Instalar Railway CLI (si no lo tienes)
   brew install railway
   
   # Conectar al proyecto
   cd /Users/jesus/Documents/kibray
   railway link
   
   # Ejecutar migraciones
   railway run python manage.py migrate
   
   # Crear superusuario
   railway run python manage.py createsuperuser
   ```

4. **Verifica que funciona:**
   - Abre tu dominio de Railway en el navegador
   - Deberías ver la aplicación
   - Ve a `/admin/` y haz login

---

## 📞 ¿Necesitas ayuda para encontrar tu dominio?

Dime si ves el dominio en Railway y te ayudo a completar las variables.
