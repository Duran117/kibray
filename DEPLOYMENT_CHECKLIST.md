# 🚀 DEPLOYMENT CHECKLIST - CALENDAR SYSTEM
**Fecha:** Diciembre 7, 2025  
**Commit:** 0d9b793  
**Branch:** main → origin/main

---

## ✅ COMPLETADO

### **1. Código Committed y Pushed**
```bash
✅ Commit: 0d9b793
✅ Push: Exitoso a origin/main
✅ Archivos: 10 nuevos/modificados
✅ Líneas: +2,965 líneas de código
```

### **2. Archivos Desplegados**
```
✅ core/models/__init__.py              - PMBlockedDay modelo
✅ core/views_pm_calendar.py            - Vista PM Calendar (461 líneas)
✅ core/views_client_calendar.py        - Vista Client Calendar (224 líneas)
✅ core/templates/core/pm_calendar.html - Template PM (690 líneas)
✅ core/templates/core/client_project_calendar.html - Template Client (690 líneas)
✅ core/migrations/0127_add_pm_blocked_day_model.py - Migración
✅ core/views.py                        - project_schedule_view mejorada
✅ kibray_backend/urls.py               - 6 rutas nuevas
✅ CALENDAR_SYSTEM_STATUS_DEC_2025.md   - Documentación
✅ CALENDAR_IMPLEMENTATION_COMPLETE.md  - Reporte final
```

---

## ⏳ PRÓXIMOS PASOS EN RAILWAY/RENDER

### **1. Esperar Deployment Automático** (5-10 minutos)
Railway/Render detectará el push automáticamente y comenzará el deployment:

**Proceso:**
```
1. Detectar cambios en main
2. Pull del código nuevo
3. Instalar dependencias (requirements.txt)
4. Collectstatic (archivos estáticos)
5. Correr migraciones (manage.py migrate)
6. Restart workers y servidor
```

**Verificar en:**
- Railway Dashboard: https://railway.app/dashboard
- O Render Dashboard: https://dashboard.render.com/

### **2. Correr Migración (CRÍTICO)**
Una vez que el deployment termine, **debes correr la migración**:

**Opción A - Railway CLI:**
```bash
railway run python manage.py migrate
```

**Opción B - Render Dashboard:**
1. Ir a tu servicio en Render
2. Shell → Manual Deploy
3. Ejecutar: `python manage.py migrate`

**Opción C - Automático (si está configurado):**
Ya debería estar en el `buildCommand` del render.yaml:
```yaml
buildCommand: |
  pip install -r requirements.txt &&
  python manage.py collectstatic --no-input &&
  python manage.py migrate --no-input
```

### **3. Verificar que la Migración Se Aplicó**
```bash
# En Railway/Render shell:
python manage.py showmigrations core | grep 0127

# Debería mostrar:
# [X] 0127_add_pm_blocked_day_model
```

### **4. Verificar URLs Funcionando**
Una vez desplegado, probar estas URLs:

**PM Calendar:**
```
https://tu-dominio.railway.app/pm-calendar/
https://tu-dominio.railway.app/pm-calendar/api/data/
```

**Client Calendar:**
```
https://tu-dominio.railway.app/projects/1/calendar/client/
https://tu-dominio.railway.app/projects/1/calendar/client/api/
```

**Redirect Test:**
```
https://tu-dominio.railway.app/projects/1/schedule/
# Debería redirigir a /projects/1/calendar/client/ si eres cliente
```

### **5. Verificar Logs (Opcional)**
```bash
# Railway CLI:
railway logs

# O en Dashboard: Deployments → View Logs
```

**Buscar:**
- ✅ "Applying migrations..."
- ✅ "Running migrations: 0127_add_pm_blocked_day_model... OK"
- ❌ Errores de migración
- ❌ Import errors

---

## 🔍 TROUBLESHOOTING

### **Problema 1: Migración no se aplica**
**Síntoma:** Error "no such table: pm_blocked_days"

**Solución:**
```bash
railway run python manage.py migrate core 0127
# O
railway run python manage.py migrate --run-syncdb
```

### **Problema 2: URLs no resuelven (404)**
**Síntoma:** 404 en `/pm-calendar/`

**Solución:**
1. Verificar que `kibray_backend/urls.py` se desplegó
2. Restart del servidor:
   ```bash
   railway restart
   ```

### **Problema 3: Import Error**
**Síntoma:** "Cannot import name 'pm_calendar_views'"

**Solución:**
1. Verificar que `core/views_pm_calendar.py` existe en servidor
2. Verificar imports en `urls.py`:
   ```python
   from core import views_pm_calendar as pm_calendar_views
   from core import views_client_calendar as client_calendar_views
   ```

### **Problema 4: Template Not Found**
**Síntoma:** "TemplateDoesNotExist: core/pm_calendar.html"

**Solución:**
1. Verificar que templates se desplegaron
2. Correr collectstatic:
   ```bash
   railway run python manage.py collectstatic --no-input
   ```

---

## 📊 VERIFICACIÓN POST-DEPLOYMENT

### **Checklist:**
- [ ] Deployment completado sin errores
- [ ] Migración 0127 aplicada
- [ ] URL `/pm-calendar/` accesible (PM users)
- [ ] URL `/projects/{id}/calendar/client/` accesible
- [ ] Redirect funciona para clientes en `/projects/{id}/schedule/`
- [ ] API endpoints retornan JSON válido
- [ ] FullCalendar se carga correctamente
- [ ] No hay errores en browser console
- [ ] Botón "Bloquear Día" funciona (PM)
- [ ] Modal de milestone funciona (Cliente)

### **Test Rápido:**
1. Login como PM → Navegar a `/pm-calendar/`
2. Verificar que carga el calendario
3. Click "Bloquear Día" → Verificar que funciona
4. Login como Cliente → Navegar a proyecto
5. Click "Ver Cronograma" → Verificar redirect y vista hermosa

---

## 🎉 LISTO PARA USAR

Una vez completados todos los pasos:

### **Rutas Disponibles:**
```
✅ /pm-calendar/                              - PM Calendar principal
✅ /pm-calendar/api/data/                     - API eventos PM
✅ /pm-calendar/block/                        - POST bloquear día
✅ /pm-calendar/unblock/<id>/                 - POST desbloquear día
✅ /projects/<id>/calendar/client/            - Client Calendar
✅ /projects/<id>/calendar/client/api/        - API eventos cliente
✅ /schedule/item/<id>/detail/                - Detalle milestone AJAX
✅ /projects/<id>/schedule/                   - Con redirect automático
```

### **Usuarios:**
- **Project Managers:** Acceso completo a PM Calendar + todos los proyectos asignados
- **Clientes:** Acceso solo a Client Calendar de sus proyectos
- **Admin:** Acceso a todo

---

## 📝 NOTAS IMPORTANTES

1. **Base de Datos:** La migración 0127 crea la tabla `pm_blocked_days` con todos los campos necesarios
2. **Permisos:** Ya están implementados los checks de rol en todas las vistas
3. **Tests:** Se han creado scripts de prueba en `test_calendar_urls.py` y `test_calendar_functional.py`
4. **Documentación:** Todo está documentado en los archivos MD incluidos

---

## 🔗 ENLACES ÚTILES

- **GitHub Repo:** https://github.com/Duran117/kibray
- **Último Commit:** 0d9b793
- **Railway Dashboard:** https://railway.app/dashboard
- **Documentación Completa:** Ver `CALENDAR_IMPLEMENTATION_COMPLETE.md`

---

**Estado:** ✅ **CÓDIGO DESPLEGADO - ESPERANDO APLICACIÓN DE MIGRACIÓN**

**Próxima acción:** Correr `python manage.py migrate` en Railway/Render
