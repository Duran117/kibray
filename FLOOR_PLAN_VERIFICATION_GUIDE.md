# 🔧 GUÍA DE VERIFICACIÓN POST-DESPLIEGUE
## Floor Plan Image Loading - Fix Complete

---

## ✅ CAMBIOS REALIZADOS

### 1. **Configuración de Producción** (`kibray_backend/settings/production.py`)
- ✅ Cambiado `USE_S3` default de `"True"` a `"False"` 
- ✅ Agregada creación automática del directorio `MEDIA_ROOT`
- ✅ Configuración de Railway Volume en `/data/media`

### 2. **Template de Floor Plan** (`core/templates/core/floor_plan_detail.html`)
- ✅ Agregado manejo de error visual cuando imagen no carga
- ✅ Agregado logging detallado en consola del navegador
- ✅ Agregado verificación de dimensiones de imagen
- ✅ Agregado mensaje cuando no hay imagen asociada

### 3. **Servir Archivos Media** (`kibray_backend/urls.py`)
- ✅ Corregida lógica para servir media files cuando `USE_S3=False`
- ✅ Archivos media ahora accesibles en producción

### 4. **Script de Diagnóstico** (`diagnose_media.py`)
- ✅ Creado script para debugging en producción
- ✅ Verifica configuración de MEDIA_ROOT
- ✅ Lista archivos en directorio de floor plans
- ✅ Muestra tamaños de archivo para detectar problemas

---

## 📋 PASOS DE VERIFICACIÓN

### PASO 1: Esperar Despliegue de Railway
Railway está reconstruyendo la aplicación con los cambios. Esto toma 2-3 minutos.

**Verifica:**
- Ve a Railway Dashboard
- Espera a que el deployment muestre "✅ Success"
- Verifica que no haya errores en los logs

---

### PASO 2: Verificar Logs de Inicio

En Railway Logs, deberías ver:

```
✅ Using Railway Volume for media: /data/media
```

**Si ves:**
```
⚠️  Using local filesystem for media (not persistent!)
```
→ El volumen NO está montado correctamente en `/data`

---

### PASO 3: Ejecutar Script de Diagnóstico (Opcional)

En Railway, abre el terminal y ejecuta:

```bash
python diagnose_media.py
```

Esto te mostrará:
- Configuración de MEDIA_ROOT
- Si el directorio `/data` existe
- Cuántos archivos hay en `floor_plans/`
- Tamaños de los archivos

---

### PASO 4: Subir Nueva Imagen de Plano

**IMPORTANTE:** Las imágenes antiguas se perdieron porque estaban en almacenamiento temporal.

1. Ve a tu proyecto en Kibray
2. Click en "Planos del Edificio" o "Floor Plans"
3. **Opción A:** Crear nuevo plano
   - Click "Subir Nuevo Plano"
   - Llena el formulario
   - **Sube una imagen** (PNG, JPG, etc.)
   - Click "Guardar"

4. **Opción B:** Editar plano existente
   - Click en un plano existente
   - Click "✏️ Edit Plan (image/level)"
   - **Sube una nueva imagen**
   - Click "Guardar"

---

### PASO 5: Verificar que la Imagen Carga

1. **Abre el plano** que acabas de crear/editar

2. **Verifica visualmente:**
   - ¿Se ve la imagen completa del plano?
   - ¿O sigue mostrando el ícono azul pequeño? 🔵

3. **Abre la Consola del Navegador** (F12 → Console)
   
   **Busca estos mensajes:**
   
   ✅ **SI TODO ESTÁ BIEN:**
   ```
   [Floor Plan] Image loaded successfully: 1920 x 1080
   [Floor Plan] Image loaded, initializing...
   ```
   
   ❌ **SI HAY PROBLEMA:**
   ```
   [Floor Plan] Image has invalid dimensions - file may not exist or be corrupted
   [Floor Plan] Error loading image: http://...
   ```

4. **Si aparece error visual en la página:**
   - Verás un recuadro rojo con el mensaje de error
   - Mostrará la URL de la imagen que falló
   - Esto significa que el archivo no existe en el servidor

---

### PASO 6: Verificar URL de la Imagen

En la consola del navegador, copia la URL de la imagen que aparece en los logs.

**Ejemplo:**
```
http://kibray.up.railway.app/media/floor_plans/plan_abc123.png
```

Pega esta URL en una nueva pestaña del navegador:

- ✅ **Si carga la imagen:** El archivo existe, problema es en el template
- ❌ **Si muestra 404:** El archivo no se guardó correctamente

---

## 🐛 TROUBLESHOOTING

### Problema 1: Imagen muestra 404
**Causa:** El archivo no se guardó en `/data/media`

**Solución:**
1. Verifica que el volumen de Railway esté montado en `/data`
2. Ejecuta `diagnose_media.py` para ver si `/data` existe
3. Re-sube la imagen

### Problema 2: Imagen es muy pequeña (< 1000 bytes)
**Causa:** El archivo está corrupto o es un placeholder

**Solución:**
1. Elimina el plano
2. Crea uno nuevo con una imagen válida
3. Usa formato PNG o JPG

### Problema 3: Imagen se ve en desarrollo pero no en producción
**Causa:** `USE_S3` está configurado incorrectamente

**Solución:**
1. Ve a Railway → Variables
2. Verifica que `USE_S3 = False`
3. Redesplegar si es necesario

### Problema 4: Imagen se pierde después de redesplegar
**Causa:** No estás usando el volumen de Railway

**Solución:**
1. Ve a Railway → Servicio "web" → Settings → Volumes
2. Verifica que existe un volumen montado en `/data`
3. Si no existe, créalo:
   - Mount Path: `/data`
   - Click "Add"

---

## 🎯 CHECKLIST DE VERIFICACIÓN FINAL

Marca cada item cuando lo hayas verificado:

- [ ] Railway deployment muestra "✅ Success"
- [ ] Logs muestran "✅ Using Railway Volume for media: /data/media"
- [ ] Volumen de Railway está creado y montado en `/data`
- [ ] Variable `USE_S3 = False` está configurada
- [ ] Subiste una NUEVA imagen de plano (las viejas se perdieron)
- [ ] La imagen se ve completa (no el ícono azul 🔵)
- [ ] Consola del navegador muestra "Image loaded successfully"
- [ ] URL de la imagen es accesible (no 404)
- [ ] Puedes agregar pines al plano
- [ ] Los pines se guardan correctamente

---

## 📞 SI SIGUE SIN FUNCIONAR

Si después de seguir TODOS los pasos anteriores la imagen sigue sin cargar:

1. **Toma screenshot de:**
   - La página del plano (mostrando el error)
   - La consola del navegador (F12 → Console)
   - Los logs de Railway

2. **Ejecuta en Railway:**
   ```bash
   python diagnose_media.py
   ```
   Copia TODO el output

3. **Envía la siguiente información:**
   - Screenshots
   - Output de diagnose_media.py
   - URL completa de la imagen que falla

---

## ✨ NOTAS IMPORTANTES

1. **Las imágenes ANTIGUAS se perdieron** porque Railway sin volumen borra los archivos en cada deploy. Esto es normal.

2. **Las imágenes NUEVAS** se guardarán en `/data/media` que es persistente gracias al volumen de Railway.

3. **No necesitas AWS S3** si usas Railway Volumes. Es más simple y gratuito.

4. **Cada vez que subas una nueva imagen**, se guardará permanentemente y NO se perderá en futuros deploys.

---

## 🎉 ÉXITO

Si la imagen carga correctamente y puedes agregar pines:

**¡FELICITACIONES! El problema está resuelto.**

Ahora puedes:
- Subir todos los planos que necesites
- Agregar pines sin problemas
- Las imágenes se guardarán permanentemente

---

*Generado: Diciembre 10, 2025*
*Commits: c511df2, 141a987, 6616752, 4551ae5, 2824588, 87a564e*
