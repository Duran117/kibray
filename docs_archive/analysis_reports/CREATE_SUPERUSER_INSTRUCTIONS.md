# ✅ CREAR SUPERUSER EN RAILWAY - INSTRUCCIONES

## 🎯 Credenciales para el Superuser

```
Username: admin
Email: admin@kibraypainting.com
Password: AdminKibray2025
```

---

## 📋 Método 1: Via Railway Dashboard (Recomendado)

### Paso 1: Abre Railway Console
1. Ve a: https://railway.app
2. Proyecto: **Kibray Painting**
3. Servicio: **web**
4. Click en botón **Connect** (terminal icon en la esquina superior derecha)

### Paso 2: Ejecuta el comando
En la terminal que se abre, copia y pega:

```bash
python manage.py createsuperuser
```

### Paso 3: Completa los datos
```
Username: admin
Email address: admin@kibraypainting.com
Password: AdminKibray2025
Password (again): AdminKibray2025
Superuser created successfully.
```

---

## 📋 Método 2: Via Railway CLI (Si tienes instalado)

```bash
# 1. Asegúrate de estar en el directorio del proyecto
cd /Users/jesus/Documents/kibray

# 2. Linkea el proyecto (si no está linkeado)
railway link

# 3. Selecciona servicio web
railway service web

# 4. Abre interactive shell
railway run python manage.py shell
```

Dentro del shell:
```python
from django.contrib.auth.models import User

User.objects.create_superuser(
    username='admin',
    email='admin@kibraypainting.com',
    password='AdminKibray2025'
)

print("Superuser created!")
exit()
```

---

## 🔐 Credenciales Guardadas

**Para tu referencia personal:**

| Campo | Valor |
|-------|-------|
| Username | `admin` |
| Email | `admin@kibraypainting.com` |
| Password | `AdminKibray2025` |

⚠️ **IMPORTANTE**: 
- Guarda estas credenciales en un lugar seguro
- Después de crear el admin, crea más usuarios con mejores contraseñas
- NO compartas estas credenciales públicamente

---

## ✅ Verificar que funciona

Una vez creado, intenta acceder:

```
URL: https://kibraypainting.up.railway.app/admin/
Username: admin
Password: AdminKibray2025
```

Deberías ver el Django Admin interface.

---

## 📝 Siguiente Paso

Después de crear el superuser:
1. Login al `/admin/`
2. Crea más usuarios (staff/regular users)
3. Configura permisos según roles
4. Considera cambiar la contraseña del admin por una más fuerte

---

## 🆘 Si algo falla

Si no puedes acceder al shell via Railway:
1. Intenta desde Railway Dashboard → servicio web → **Connect** button
2. Si eso tampoco funciona, Railway tiene issues - contacta a Railway support
3. Alternativa: Usa la base de datos PostgreSQL directamente (más avanzado)
