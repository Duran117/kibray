# 🚂 Railway Setup Completo - Kibray

## ✅ Lo que eliminaste
- ✅ Proyecto viejo: `industrious-friendship` (eliminado correctamente)

## 📋 Lo que necesitas ahora

Tu proyecto `lovely-adventure` tiene **3 servicios** que necesitan configuración:

1. **web** - Django backend (el principal)
2. **worker** - Celery worker (procesa tareas en segundo plano)
3. **beat** - Celery beat (scheduler de tareas periódicas)

---

## 🔧 PASO 1: Agregar Servicios Necesarios

En Railway dashboard → proyecto `lovely-adventure`:

### 1.1 Agregar PostgreSQL
1. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway genera automáticamente la variable `DATABASE_URL`
3. ✅ Listo - no necesitas hacer nada más

### 1.2 Agregar Redis
1. Click **"+ New"** → **"Database"** → **"Add Redis"**
2. Railway genera automáticamente la variable `REDIS_URL`
3. ✅ Listo - no necesitas hacer nada más

Después de esto, deberías tener **5 servicios** en total:
- ✅ web (Django)
- ✅ worker (Celery worker)
- ✅ beat (Celery beat)
- ✅ Postgres (base de datos) **← NUEVO**
- ✅ Redis (cache/queue) **← NUEVO**

---

## 🔐 PASO 2: Configurar Variables de Entorno

Ve al servicio **web** → pestaña **"Variables"** → Click **"+ New Variable"**

### Variables OBLIGATORIAS (mínimo para que funcione)

```bash
# 1. Django Secret Key (genera una nueva)
DJANGO_SECRET_KEY=django-insecure-CAMBIA-ESTO-POR-50-CARACTERES-ALEATORIOS

# 2. Environment
DJANGO_ENV=production

# 3. Allowed Hosts (tu dominio de Railway)
ALLOWED_HOSTS=lovely-adventure-production-xxxx.up.railway.app,*.railway.app

# 4. CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS=https://lovely-adventure-production-xxxx.up.railway.app

# 5. CORS Allowed Origins
CORS_ALLOWED_ORIGINS=https://lovely-adventure-production-xxxx.up.railway.app
```

> **Nota:** Railway **automáticamente** crea `DATABASE_URL` y `REDIS_URL` cuando agregaste Postgres y Redis. NO necesitas copiar/pegar nada manualmente.

### Variables OPCIONALES (pero recomendadas)

```bash
# OpenAI (para features de AI)
OPENAI_API_KEY=sk-proj-TU-KEY-AQUI

# Email (para notificaciones)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
DEFAULT_FROM_EMAIL=noreply@kibray.com

# AWS S3 (para archivos/imágenes en producción)
USE_S3=True
AWS_ACCESS_KEY_ID=AKIAXXXXX
AWS_SECRET_ACCESS_KEY=tu-secret-key
AWS_STORAGE_BUCKET_NAME=kibray-media
AWS_S3_REGION_NAME=us-east-1

# Sentry (monitoreo de errores)
SENTRY_DSN=https://xxx@sentry.io/xxx

# SSL (después de que esté estable)
SECURE_SSL_REDIRECT=False  # Déjalo en False por ahora
```

---

## 🔄 PASO 3: Configurar Worker y Beat

Railway necesita saber QUÉ comando ejecutar en cada servicio.

### 3.1 Servicio `worker`

1. Ve al servicio **worker** → **Settings** → **Deploy**
2. Encuentra **"Custom Start Command"**
3. Asegúrate que sea:
   ```bash
   celery -A kibray_backend worker --loglevel=info
   ```

### 3.2 Servicio `beat`

1. Ve al servicio **beat** → **Settings** → **Deploy**
2. Encuentra **"Custom Start Command"**
3. Asegúrate que sea:
   ```bash
   celery -A kibray_backend beat --loglevel=info
   ```

### 3.3 Compartir Variables con Worker/Beat

**IMPORTANTE:** Worker y Beat necesitan las MISMAS variables que `web`.

1. Ve al servicio **worker** → **Variables**
2. Click **"+ Reference"** (no "New Variable")
3. Selecciona:
   - `DATABASE_URL` → Reference from **Postgres**
   - `REDIS_URL` → Reference from **Redis**
   - `DJANGO_SECRET_KEY` → Reference from **web**
   - `DJANGO_ENV` → Reference from **web**

4. Repite para servicio **beat**

**O** más fácil: en el dashboard principal, Railway puede compartir variables automáticamente si los servicios están en el mismo proyecto.

---

## 🚀 PASO 4: Deploy y Verificación

### 4.1 Ejecutar Migraciones (IMPORTANTE - Primera vez solamente)

Después de que `web` esté en línea:

1. En Railway dashboard → servicio **web** → pestaña **"Deployments"**
2. Click en el último deployment → **"View Logs"**
3. Espera a que muestre: `Listening at: http://0.0.0.0:xxxx`
4. Luego ve a **"Settings"** → **"Deploy"** → Click en el ícono de terminal (si está disponible)
   
   **O** instala Railway CLI en tu Mac:
   ```bash
   # Instalar Railway CLI
   brew install railway
   
   # Conectar al proyecto
   cd /Users/jesus/Documents/kibray
   railway link
   
   # Ejecutar migraciones
   railway run python manage.py migrate
   
   # Crear superusuario
   railway run python manage.py createsuperuser
   
   # Recolectar archivos estáticos (si no se hizo en build)
   railway run python manage.py collectstatic --noinput
   ```

### 4.2 Verificar que todo funciona

#### Opción A: Desde tu Mac (con Railway CLI instalado)

```bash
# 1. Verificar Django
railway run python manage.py check

# 2. Verificar OpenAI
railway run python manage.py shell
```

Dentro del shell:
```python
>>> from core.ai_sop_generator import OPENAI_AVAILABLE
>>> print(OPENAI_AVAILABLE)
True  # ✅ Si configuraste OPENAI_API_KEY

>>> from core.ai_sop_generator import generate_sop_with_ai
>>> sop = generate_sop_with_ai("Test SOP", "PREP")
>>> print(sop['name'])
# Debería generar un nombre
```

#### Opción B: Verificar desde el navegador

1. Abre tu dominio de Railway: `https://lovely-adventure-production-xxxx.up.railway.app`
2. Deberías ver tu aplicación Django
3. Intenta hacer login: `/admin/`
4. Si ves la página de admin → ✅ **TODO FUNCIONA**

---

## 🔍 Troubleshooting

### ❌ Error: "ALLOWED_HOSTS validation failed"

**Solución:** 
1. Ve a **web** → **Variables**
2. Revisa que `ALLOWED_HOSTS` incluya tu dominio de Railway **sin** `https://`
   ```
   Correcto:   lovely-adventure-production-xxxx.up.railway.app
   Incorrecto: https://lovely-adventure-production-xxxx.up.railway.app
   ```

### ❌ Error: "REDIS_URL environment variable must be set"

**Solución:**
1. Verifica que agregaste Redis como servicio
2. Ve a **web** → **Variables**
3. Busca `REDIS_URL` - debería estar ahí automáticamente
4. Si no está, agrégala manualmente (Railway → Redis service → Connect → copia URL)

### ❌ Error: "DATABASE_URL environment variable must be set"

**Solución:**
1. Verifica que agregaste PostgreSQL como servicio
2. Ve a **web** → **Variables**
3. Busca `DATABASE_URL` - debería estar ahí automáticamente
4. Si no está, agrégala manualmente (Railway → Postgres service → Connect → copia URL)

### ❌ Workers no procesan tareas

**Solución:**
1. Verifica logs del servicio `worker`:
   - Railway → servicio **worker** → **Deployments** → logs
2. Debe decir: `celery@xxx ready`
3. Si dice error de conexión a Redis:
   - Ve a **worker** → **Variables**
   - Asegúrate que `REDIS_URL` esté compartida desde Redis service

### ❌ Beat no ejecuta tareas programadas

**Solución:**
1. Verifica que SOLO tienes **1 instancia** de beat corriendo
2. Beat debe estar en el mismo proyecto con acceso a `REDIS_URL`
3. Verifica logs: Railway → **beat** → logs
4. Debe decir: `celery beat v5.x.x is starting`

---

## 📊 Monitoreo y Logs

### Ver logs en tiempo real

#### Opción A: Railway Dashboard
1. Railway → servicio **web** → **Deployments**
2. Click en el último deployment
3. Click **"View Logs"**

#### Opción B: Railway CLI
```bash
# Logs del servicio web
railway logs --service web

# Logs del worker
railway logs --service worker

# Logs del beat
railway logs --service beat

# Logs en tiempo real (live tail)
railway logs --service web --follow
```

---

## 🎯 Siguiente Paso: Prueba de Features AI

Una vez que `OPENAI_API_KEY` esté configurado, puedes probar:

### 1. Generar SOP con AI

```python
# Desde Railway CLI
railway run python manage.py shell

# Dentro del shell:
from core.ai_sop_generator import generate_sop_with_ai

sop = generate_sop_with_ai(
    task_description="Preparar superficie para pintura exterior",
    category="PREP",
    language="es"
)

print(f"✅ SOP Generado: {sop['name']}")
print(f"📝 Pasos: {len(sop['steps'])}")
print(f"⏱️  Tiempo estimado: {sop['time_estimate']}")
```

### 2. Calcular Task Impact con AI

```python
from core.ai_focus_helper import calculate_task_impact_ai

result = calculate_task_impact_ai(
    task_title="Follow up on $120K proposal - ABC Construction",
    user_role="owner",
    session_context={
        'energy_level': 8,
        'total_tasks': 12
    }
)

print(f"⭐ Impact Score: {result['score']}/10")
print(f"💡 Reasoning: {result['reasoning']}")
print(f"👥 Delegable: {result['is_delegable']}")
```

### 3. Recomendar ONE THING

```python
from core.ai_focus_helper import recommend_one_thing_ai

tasks = [
    {'title': 'Follow up $120K proposal', 'role': 'owner'},
    {'title': 'Review paint samples', 'role': 'pm'},
    {'title': 'Order materials', 'role': 'pm'},
]

recommendation = recommend_one_thing_ai(
    tasks_list=tasks,
    user_context={'role': 'owner', 'energy': 8}
)

print(f"🐸 ONE THING: Task #{recommendation['recommended_task_id']}")
print(f"💭 Reason: {recommendation['recommendation_reason']}")
```

---

## ✅ Checklist Final

Marca cuando completes cada paso:

- [ ] Agregué PostgreSQL a Railway
- [ ] Agregué Redis a Railway
- [ ] Configuré variables obligatorias en servicio `web`
- [ ] Configuré OPENAI_API_KEY (opcional)
- [ ] Compartí variables con `worker` y `beat`
- [ ] Ejecuté `railway run python manage.py migrate`
- [ ] Creé superusuario con `railway run python manage.py createsuperuser`
- [ ] Verifiqué que `/admin/` funciona
- [ ] Verifiqué logs de `web`, `worker`, `beat`
- [ ] Probé features AI (si configuré OpenAI)

---

## 🆘 ¿Necesitas Ayuda?

Si algo no funciona:
1. Revisa logs: `railway logs --service web`
2. Verifica variables: Railway dashboard → web → Variables
3. Compara con este checklist
4. Pregúntame y comparte el error específico de los logs

---

**Última actualización:** Diciembre 5, 2025
**Proyecto Railway:** `lovely-adventure`
**Estado:** Configuración inicial pendiente
