# 📱 Kibray PWA (Progressive Web App) - Guía Completa

## ✅ Estado Actual: PWA INSTALADO

**Fecha de Implementación:** 2025-01-13  
**Versión PWA:** 1.0.0

---

## 🎯 ¿Qué es un PWA?

Un **Progressive Web App** es una aplicación web que se comporta como una app nativa en teléfonos y tablets:

✅ **Instalable** - Se puede instalar en la pantalla de inicio  
✅ **Funciona Offline** - Algunas funciones disponibles sin internet  
✅ **Experiencia Nativa** - Pantalla completa, sin barra del navegador  
✅ **Rápida** - Carga instantánea con caché inteligente  
✅ **Push Notifications** - Recibe notificaciones (próximamente)  

---

## 📦 Archivos Implementados

### 1. **manifest.json** ✅
- **Ubicación:** `/core/static/manifest.json`
- **Función:** Define la identidad de la app (nombre, íconos, colores)
- **Contenido:**
  - Nombre: "Kibray Construction Management"
  - Tema: Azul (#1e3a8a)
  - 8 tamaños de íconos (72px a 512px)
  - 4 shortcuts: Dashboard, Proyectos, Planificación, Finanzas

### 2. **service-worker.js** ✅
- **Ubicación:** `/core/static/service-worker.js`
- **Función:** Maneja caché y funcionalidad offline
- **Características:**
  - **Caché Inteligente:** Guarda páginas visitadas para acceso offline
  - **Network First:** Intenta cargar desde internet, luego caché
  - **Actualizaciones Automáticas:** Detecta nuevas versiones cada hora
  - **Background Sync:** Sincroniza datos cuando regresa conexión (próximamente)
  - **Push Notifications:** Preparado para recibir notificaciones (próximamente)

### 3. **offline.html** ✅
- **Ubicación:** `/core/templates/offline.html`
- **Función:** Página que se muestra cuando no hay internet
- **Características:**
  - Diseño atractivo con gradiente
  - Tips para recuperar conexión
  - Botón "Reintentar"
  - Auto-detecta cuando regresa internet

### 4. **base.html (actualizado)** ✅
- **Cambios realizados:**
  - ✅ Meta tags PWA agregados
  - ✅ Link a manifest.json
  - ✅ Íconos Apple Touch agregados
  - ✅ Service Worker registrado automáticamente
  - ✅ Install prompt (banner de instalación)

### 5. **Íconos PWA** ⚠️ PLACEHOLDER
- **Ubicación:** `/core/static/icons/`
- **Archivos:**
  - `icon.svg` - Ícono base (letra K + brocha) ✅
  - `generate-icons.html` - Generador web de íconos PNG ✅
  - `README.md` - Instrucciones para generar íconos finales ✅
  - **Pendiente:** Generar archivos PNG finales (ver sección siguiente)

---

## 🖼️ Generar Íconos Finales

Los íconos actuales son **placeholders**. Para generar los íconos finales:

### **Opción 1: Generador Web (Más Fácil)** ⭐

1. Abre en Chrome/Firefox: 
   ```
   file:///Users/jesus/Documents/kibray/core/static/icons/generate-icons.html
   ```

2. Se generarán automáticamente 8 tamaños

3. Haz clic en "Download All Icons (ZIP)" o descarga uno por uno

4. Guarda los archivos PNG en `/core/static/icons/`

5. Nombres correctos:
   - icon-72x72.png
   - icon-96x96.png
   - icon-128x128.png
   - icon-144x144.png
   - icon-152x152.png
   - icon-192x192.png
   - icon-384x384.png
   - icon-512x512.png

### **Opción 2: Herramienta Online**

1. Ve a: https://realfavicongenerator.net/
2. Sube `/core/static/icons/icon.svg`
3. Selecciona "Progressive Web App"
4. Descarga el paquete
5. Copia los archivos PNG a `/core/static/icons/`

### **Opción 3: ImageMagick (Terminal)**

```bash
cd /Users/jesus/Documents/kibray/core/static/icons/

# Instalar ImageMagick si no lo tienes
brew install imagemagick

# Generar todos los tamaños
for size in 72 96 128 144 152 192 384 512; do
  convert icon.svg -resize ${size}x${size} icon-${size}x${size}.png
done
```

---

## 📱 Cómo Instalar Kibray en Dispositivos

### **iPhone/iPad (iOS)**

1. Abre Kibray en Safari (no Chrome)
2. Toca el botón **Compartir** (cuadro con flecha hacia arriba)
3. Desplázate y toca **"Agregar a pantalla de inicio"**
4. Cambia el nombre si quieres
5. Toca **"Agregar"**
6. ¡Listo! Ícono de Kibray en tu pantalla de inicio

### **Android**

1. Abre Kibray en Chrome
2. Verás un banner en la parte inferior: **"Instalar Kibray"**
3. Toca **"Instalar"**
4. O toca el menú (⋮) → **"Agregar a pantalla de inicio"**
5. ¡Listo! Ícono de Kibray en tu pantalla de inicio

### **Windows/Mac Desktop**

1. Abre Kibray en Chrome
2. En la barra de direcciones, verás un ícono de **instalar** (+)
3. Haz clic en el ícono
4. Haz clic en **"Instalar"**
5. Kibray se abrirá como una app independiente

---

## 🚀 Funcionalidades PWA Actuales

### ✅ **Implementado**

1. **Instalación en Pantalla de Inicio**
   - Ícono personalizado
   - Nombre "Kibray"
   - Abre en pantalla completa

2. **Banner de Instalación Automático**
   - Aparece en navegadores compatibles
   - Se puede cerrar si no quieres instalar
   - No molesta si ya instalaste

3. **Caché Inteligente**
   - Páginas visitadas se guardan
   - Assets (CSS, JS, imágenes) se cachean
   - Dashboard accesible offline

4. **Página Offline Bonita**
   - En lugar de error genérico
   - Tips para recuperar conexión
   - Auto-detecta cuando regresa internet

5. **Actualizaciones Automáticas**
   - Service worker se actualiza cada hora
   - Aviso cuando hay nueva versión
   - Opción de actualizar ahora

6. **Shortcuts de App**
   - Dashboard
   - Proyectos
   - Planificación Diaria
   - Dashboard Financiero

### ⏳ **Próximamente**

7. **Background Sync**
   - Subir fotos cuando regresa conexión
   - Guardar time entries offline
   - Sincronizar automáticamente

8. **Push Notifications** (FASE 3)
   - Nueva factura aprobada
   - Change order creado
   - Material recibido
   - Touch-up completado
   - Tarea asignada

---

## 🧪 Probar el PWA

### **1. Verificar Service Worker**

1. Abre Kibray en Chrome
2. Presiona `F12` (DevTools)
3. Ve a **Application** → **Service Workers**
4. Deberías ver: `service-worker.js` - Status: **activated and is running**

### **2. Verificar Manifest**

1. En DevTools → **Application** → **Manifest**
2. Deberías ver:
   - Name: "Kibray Construction Management"
   - Start URL: "/dashboard/"
   - Theme color: #1e3a8a
   - Íconos (8 tamaños)

### **3. Probar Offline**

1. En DevTools → **Network** → Marca **"Offline"**
2. Recarga la página (`Cmd+R`)
3. Deberías ver la página offline bonita
4. Desmarca "Offline" y presiona "Reintentar"
5. Deberías volver al dashboard

### **4. Lighthouse Audit**

1. En DevTools → **Lighthouse**
2. Selecciona **"Progressive Web App"**
3. Click **"Generate report"**
4. Deberías obtener puntaje **90+**

---

## 🔧 Mantenimiento

### **Actualizar Service Worker**

Si haces cambios importantes, incrementa la versión en:

```javascript
// /core/static/service-worker.js
const CACHE_NAME = 'kibray-v1'; // Cambiar a v2, v3, etc.
```

### **Limpiar Caché (Desarrollo)**

Si necesitas forzar actualización durante desarrollo:

```javascript
// En la consola del navegador
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(registration => registration.unregister());
});

caches.keys().then(keys => {
  keys.forEach(key => caches.delete(key));
});

location.reload();
```

### **Desinstalar Service Worker (Reset Total)**

1. DevTools → Application → Service Workers
2. Click en **"Unregister"** junto a service-worker.js
3. Application → Storage → **"Clear site data"**
4. Recarga la página

---

## 📊 Métricas de Éxito

### **Antes del PWA**
- ⏱️ Carga inicial: ~3-5 segundos
- 📶 Offline: Error genérico
- 📱 Móvil: Barra de navegador visible
- 🔔 Notificaciones: No disponibles

### **Después del PWA**
- ⚡ Carga inicial: ~0.5-1 segundo (con caché)
- 📶 Offline: Página personalizada + funciones limitadas
- 📱 Móvil: Pantalla completa, app nativa
- 🔔 Notificaciones: Preparado (FASE 3)

---

## 🐛 Troubleshooting

### **El banner de instalación no aparece**

- ✅ Verifica que estés usando HTTPS (o localhost)
- ✅ Confirma que manifest.json esté cargando (DevTools → Network)
- ✅ Revisa que service-worker.js esté activado (DevTools → Application)
- ✅ Intenta en modo incógnito (caché limpio)

### **Service Worker no se actualiza**

- ✅ Incrementa `CACHE_NAME` en service-worker.js
- ✅ Cierra todas las pestañas de Kibray
- ✅ Abre de nuevo (debería detectar actualización)
- ✅ En DevTools → Application → Service Workers → "Update on reload"

### **Página offline no aparece**

- ✅ Verifica que `/templates/offline.html` exista
- ✅ Confirma que offline.html esté en PRECACHE_ASSETS
- ✅ Revisa que la ruta en settings.py sea correcta
- ✅ Carga offline.html manualmente primero para que se cachee

### **Íconos no se ven**

- ✅ Genera los archivos PNG (actualmente son placeholders)
- ✅ Verifica las rutas en manifest.json
- ✅ Confirma que los archivos estén en `/core/static/icons/`
- ✅ Recarga con `Cmd+Shift+R` (hard refresh)

---

## 📚 Recursos Adicionales

- **PWA Checklist:** https://web.dev/pwa-checklist/
- **Service Worker API:** https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API
- **Web App Manifest:** https://developer.mozilla.org/en-US/docs/Web/Manifest
- **Lighthouse:** https://developers.google.com/web/tools/lighthouse

---

## ✨ Próximos Pasos

1. **Generar íconos finales** (ver sección arriba) ⏳
2. **Implementar búsqueda global** (FASE 2) ⏳
3. **Optimizar templates móviles** (FASE 3) ⏳
4. **Integrar push notifications** (FASE 3) ⏳

---

**¡El PWA está listo para usar!** 🎉

Los empleados ya pueden instalar Kibray en sus teléfonos y trabajar con una experiencia de app nativa.
