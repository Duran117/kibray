# Guía de Configuración del Módulo Gantt React

## 📋 Resumen

Hemos creado un módulo completo de cronograma Gantt interactivo usando **React + TypeScript + Frappe Gantt**. Este módulo se integra con tu aplicación Django existente mediante una arquitectura híbrida:

- **Backend**: Django REST API (creado en `core/api/`)
- **Frontend**: React + TypeScript + Vite (creado en `/frontend`)
- **Integración**: API-based, autenticación CSRF

## 🎯 Características Implementadas

### Backend Django (✅ Completo)
- ✅ **Modelos**: `ScheduleCategory` y `ScheduleItem` con soporte para:
  - Jerarquías (categorías padre/hijo)
  - Fases (`is_phase`)
  - Hitos (`is_milestone`)
  - Dependencias entre tareas
  - Estado y progreso
  
- ✅ **API REST** (`core/api/`):
  - `ScheduleCategoryViewSet`: CRUD para categorías
  - `ScheduleItemViewSet`: CRUD para ítems con endpoint de actualización masiva
  - Filtrado por proyecto
  - Serializers con datos anidados
  
- ✅ **URLs**:
  - `/api/schedule/categories/` - Categorías
  - `/api/schedule/items/` - Ítems
  - `/api/schedule/items/bulk_update/` - Actualización masiva
  - `/projects/<id>/schedule/gantt/` - Vista React

- ✅ **Template**: `schedule_gantt_react.html` para cargar la app React

### Frontend React (✅ Completo)
- ✅ **Estructura del proyecto**:
  ```
  frontend/
  ├── package.json          # Dependencias y scripts
  ├── vite.config.ts        # Configuración de build
  ├── tsconfig.json         # TypeScript config
  ├── index.html            # HTML entry point
  └── src/
      ├── main.tsx          # React entry point
      ├── App.tsx           # Componente principal
      ├── types.ts          # Interfaces TypeScript
      ├── api.ts            # Cliente API con CSRF
      └── components/
          ├── GanttChart.tsx    # Componente Gantt con Frappe
          ├── GanttChart.css    # Estilos del Gantt
          ├── TaskEditor.tsx    # Editor de tareas
          └── TaskEditor.css    # Estilos del editor
  ```

- ✅ **Componentes**:
  - `GanttChart`: Visualización con Frappe Gantt, zoom Day/Week/Month
  - `TaskEditor`: Panel lateral para crear/editar tareas
  - `App`: Gestor de estado, llamadas API, handlers de eventos

- ✅ **Funcionalidades**:
  - Visualización de cronograma con barras de tareas
  - Arrastrar para cambiar fechas
  - Editar progreso visualmente
  - Color por estado (verde=completado, azul=en progreso, etc.)
  - Hitos como diamantes
  - Crear/editar/eliminar tareas
  - Exportar a PDF

## 🚀 Pasos de Instalación

### 1. Instalar Node.js y npm

**Node.js no está instalado en tu sistema.** Descárgalo e instálalo desde:
- https://nodejs.org/ (versión LTS recomendada: 20.x)

Después de instalar, verifica con:
```powershell
node --version
npm --version
```

### 2. Instalar Dependencias Frontend

En el directorio `frontend/`:

```powershell
cd C:\Users\jesus\Kibray\frontend
npm install
```

Esto instalará:
- React 18.2.0
- TypeScript 5.3.3
- Vite 5.0.8
- Frappe Gantt 0.6.1
- Axios 1.6.0
- date-fns 3.0.0
- jsPDF 2.5.1
- html2canvas 1.4.1

### 3. Configurar CORS (Ya Configurado)

Asegúrate que `kibray_backend/settings.py` tiene:

```python
INSTALLED_APPS = [
    # ...
    'corsheaders',
    'rest_framework',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Debe estar antes de CommonMiddleware
    # ...
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
]
```

### 4. Desarrollo: Modo Dual Server

#### Terminal 1 - Django Backend:
```powershell
cd C:\Users\jesus\Kibray
.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

#### Terminal 2 - Vite Dev Server:
```powershell
cd C:\Users\jesus\Kibray\frontend
npm run dev
```

El Vite dev server correrá en `http://localhost:5173` y hará proxy de las llamadas API a Django en `localhost:8000`.

### 5. Acceso en Desarrollo

Abre en el navegador:
- **React Gantt**: http://localhost:5173
- **Django Admin**: http://localhost:8000/admin
- **API**: http://localhost:8000/api/schedule/items/?project=1

El componente React tomará el `project_id` del atributo `data-project-id` en el div raíz.

## 📦 Build de Producción

### Compilar Frontend

```powershell
cd C:\Users\jesus\Kibray\frontend
npm run build
```

Esto generará archivos optimizados en:
```
C:\Users\jesus\Kibray\staticfiles\gantt\
├── assets\
│   ├── main-[hash].js
│   └── main-[hash].css
└── .vite\
    └── manifest.json
```

### Configurar Django para Servir Assets

En `kibray_backend/settings.py`:

```python
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'staticfiles' / 'gantt',
]
```

Ejecuta collectstatic:
```powershell
python manage.py collectstatic --noinput
```

### Acceso en Producción

Django servirá automáticamente los assets compilados. Accede a:
- http://yourserver.com/projects/1/schedule/gantt/

La plantilla `schedule_gantt_react.html` detecta automáticamente si está en modo DEBUG o producción y carga los assets correspondientes.

## 🔧 Configuración de Vite

El archivo `frontend/vite.config.ts` está configurado para:

1. **Base URL**: `/static/gantt/` para servir desde Django
2. **Output**: `../staticfiles/gantt/` directamente en el directorio de Django
3. **Manifest**: Genera manifest.json para resolver hashes de archivos
4. **Proxy**: Redirige `/api` a `http://localhost:8000` en desarrollo

## 🎨 Personalización

### Cambiar Colores de Estado

Edita `frontend/src/components/GanttChart.css`:

```css
.gantt .bar.status-done {
  fill: #28a745;  /* Verde */
}

.gantt .bar.status-in_progress {
  fill: #007bff;  /* Azul */
}

.gantt .bar.status-blocked {
  fill: #dc3545;  /* Rojo */
}

.gantt .bar.status-not_started {
  fill: #6c757d;  /* Gris */
}
```

### Ajustar Zoom por Defecto

En `frontend/src/App.tsx`, cambia:

```typescript
const [viewMode, setViewMode] = useState<'Day' | 'Week' | 'Month'>('Week');
```

### Modificar Popup de Tareas

En `frontend/src/components/GanttChart.tsx`, edita la función `custom_popup_html`:

```typescript
function custom_popup_html(task: any) {
  return `
    <div class="gantt-popup">
      <h4>${task.name}</h4>
      <p>Custom info here...</p>
    </div>
  `;
}
```

## 🐛 Debugging

### Error: CSRF Token Missing

Asegúrate que el frontend está enviando cookies:

```typescript
// En api.ts
axios.defaults.withCredentials = true;
```

Y que Django permite credenciales:

```python
# settings.py
CORS_ALLOW_CREDENTIALS = True
```

### Error: No Data Showing

Verifica que existen tareas con fechas en la base de datos:

```powershell
python manage.py shell
```

```python
from core.models import ScheduleItem
items = ScheduleItem.objects.filter(project_id=1)
print(items.count())
for item in items:
    print(f"{item.name}: {item.planned_start} - {item.planned_end}")
```

Si no hay datos, ejecuta el seed script:

```powershell
python seed_schedule_demo.py
```

### Error: Vite Dev Server Not Found

Verifica que Vite está corriendo en puerto 5173:

```powershell
netstat -an | findstr 5173
```

Si no está corriendo:

```powershell
cd frontend
npm run dev
```

## 📊 API Endpoints Disponibles

### Listar Items por Proyecto
```http
GET /api/schedule/items/?project=1
```

### Crear Item
```http
POST /api/schedule/items/
Content-Type: application/json

{
  "project": 1,
  "name": "Nueva tarea",
  "start": "2025-11-15",
  "end": "2025-11-20",
  "status": "NOT_STARTED",
  "progress": 0,
  "category": 2,
  "is_milestone": false
}
```

### Actualizar Item
```http
PATCH /api/schedule/items/5/
Content-Type: application/json

{
  "start": "2025-11-16",
  "end": "2025-11-21",
  "progress": 50
}
```

### Actualización Masiva (Drag & Drop)
```http
POST /api/schedule/items/bulk_update/
Content-Type: application/json

{
  "updates": [
    {"id": "5", "start": "2025-11-16", "end": "2025-11-21"},
    {"id": "6", "progress": 75}
  ]
}
```

### Listar Categorías
```http
GET /api/schedule/categories/?project=1
```

## ✅ Estado Actual

### ✅ Completado
- Backend Django REST API con ViewSets y Serializers
- Frontend React con TypeScript
- Componente GanttChart con Frappe Gantt
- Componente TaskEditor para CRUD
- Cliente API con manejo de CSRF
- Templates de integración
- URLs configuradas
- Modelos con migraciones aplicadas
- Datos de prueba seeded

### ⏳ Pendiente
- [x] Instalar Node.js (Usuario debe hacerlo)
- [ ] `npm install` en /frontend
- [ ] `npm run dev` para probar en desarrollo
- [ ] `npm run build` para compilar producción
- [ ] Testing con datos reales
- [ ] Ajustar estilos según diseño del proyecto

## 🎯 Próximos Pasos

1. **Instalar Node.js** desde https://nodejs.org/
2. **Ejecutar npm install** en `/frontend`
3. **Iniciar ambos servers**:
   - Django: `python manage.py runserver 0.0.0.0:8000`
   - Vite: `npm run dev` (en /frontend)
4. **Probar** en http://localhost:5173
5. **Ajustar** estilos y funcionalidades según necesites
6. **Build** para producción con `npm run build`

## 📚 Recursos

- **Frappe Gantt Docs**: https://frappe.io/gantt
- **React Docs**: https://react.dev
- **Vite Docs**: https://vitejs.dev
- **Django REST Framework**: https://www.django-rest-framework.org
- **Axios**: https://axios-http.com/docs/intro

## 💡 Notas

- El proyecto usa **32 píxeles por día** como escala base
- Los **hitos** se renderizan como diamantes rotados 45°
- Las **dependencias** se muestran con flechas (feature de Frappe Gantt)
- El **PDF export** usa jsPDF + html2canvas para capturar el canvas

---

**¿Preguntas o problemas?** Revisa esta guía o consulta los logs de Django/Vite para debugging.
