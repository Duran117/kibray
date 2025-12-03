# 📋 ANÁLISIS Y MEJORAS - CREACIÓN DE SOPs

## 🔍 **ANÁLISIS DEL SISTEMA ACTUAL**

### **Estado Actual del Formulario de Creación de SOPs**

**Archivo:** `core/templates/core/sop_creator.html`  
**Vista:** `core/views.py:sop_create_edit()`  
**Formulario:** `core/forms.py:ActivityTemplateForm`

#### ✅ **Lo que funciona bien:**
1. ✅ Campos dinámicos para steps, materials, tools
2. ✅ Soporte para archivos múltiples
3. ✅ Validación de campos requeridos
4. ✅ Drag & drop con Sortable.js
5. ✅ Edición de SOPs existentes

#### ❌ **Problemas de UX identificados:**

1. **Formulario muy largo y abrumador**
   - Todos los campos en una sola página
   - No hay organización visual clara
   - Difícil de entender qué es obligatorio vs opcional

2. **Falta de guías visuales**
   - No hay ejemplos o placeholders descriptivos
   - No hay tooltips explicativos
   - Sin indicación de progreso

3. **Campos de texto plano sin formato**
   - `tips`, `description`, `common_errors` son textareas simples
   - No hay editor rico (rich text)
   - Difícil agregar formato o listas

4. **No hay preview en tiempo real**
   - Usuario no ve cómo se verá el SOP final
   - Tiene que guardar y luego ir a ver

5. **Manejo de listas manual**
   - Agregar steps/materials/tools requiere click en "+"
   - No hay drag & drop visual obvio
   - No hay reordenamiento intuitivo

6. **Sin sugerencias inteligentes**
   - No hay autocompletado para materials comunes
   - No hay templates predefinidos por categoría
   - No sugiere tools según categoría

---

## 🚀 **PROPUESTAS DE MEJORA**

### **OPCIÓN 1: Formulario con Wizard (Pasos Múltiples)** ⭐ RECOMENDADO

**Dividir la creación en pasos lógicos:**

```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Crear SOP - Paso 1 de 5                                  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ ●━━━━○━━━━○━━━━○━━━━○                                        │
│ Básico  Pasos  Mat  Ref  Review                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🎯 INFORMACIÓN BÁSICA                                       │
│                                                             │
│ Nombre del SOP:                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Ej: "Instalación de Drywall - Sala Estándar"           │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Categoría:                                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [PREP] ▼                                                │ │
│ │  • PREP - Preparación inicial                           │ │
│ │  • INSTALL - Instalación principal                      │ │
│ │  • FINISH - Acabados finales                            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Descripción breve (opcional):                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Describe en 1-2 líneas qué hace este SOP...            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Tiempo estimado:                                            │
│ ┌───────┐ hrs  ┌───────┐ min                               │
│ │   2   │      │  30   │                                   │
│ └───────┘      └───────┘                                   │
│                                                             │
│                        [❌ Cancelar]  [Siguiente →]         │
└─────────────────────────────────────────────────────────────┘
```

**Paso 2: Steps/Checklist**
```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Crear SOP - Paso 2 de 5: Checklist de Pasos              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ ●━━━━●━━━━○━━━━○━━━━○                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ✅ LISTA DE PASOS A SEGUIR                                  │
│                                                             │
│ 💡 Tip: Agrega pasos en orden secuencial. Los empleados    │
│    los verán como checklist.                                │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🔷 Agregar nuevo paso:                                  │ │
│ │ ┌─────────────────────────────────────────────┐  [+]    │ │
│ │ │ Ej: "Medir y marcar ubicación de sheets"   │         │ │
│ │ └─────────────────────────────────────────────┘         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ 📋 Pasos agregados (arrastra para reordenar):               │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ⋮⋮  1. ☐ Medir área de trabajo                    [×]  │ │
│ │ ⋮⋮  2. ☐ Cortar drywall sheets                    [×]  │ │
│ │ ⋮⋮  3. ☐ Instalar sheets con tornillos           [×]  │ │
│ │ ⋮⋮  4. ☐ Aplicar compound en juntas               [×]  │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ⚠️ Mínimo 1 paso requerido                                  │
│                                                             │
│                  [← Anterior]  [❌ Cancelar]  [Siguiente →] │
└─────────────────────────────────────────────────────────────┘
```

**Paso 3: Materiales y Herramientas**
```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Crear SOP - Paso 3 de 5: Materiales y Herramientas       │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ ●━━━━●━━━━●━━━━○━━━━○                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🧰 MATERIALES NECESARIOS                                    │
│                                                             │
│ 💡 Sugerencias comunes para categoría "PREP":               │
│ [+ Drywall sheets] [+ Joint compound] [+ Screws]            │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Agregar material:                                       │ │
│ │ ┌─────────────────────────────────────────┐  [+]        │ │
│ │ │ [Autocompletado habilitado]             │             │ │
│ │ └─────────────────────────────────────────┘             │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Materiales agregados:                                       │
│ • Drywall sheets (4x8)  [×]                                 │
│ • Joint compound  [×]                                       │
│ • Drywall screws (1.25")  [×]                               │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ 🔧 HERRAMIENTAS REQUERIDAS                                  │
│                                                             │
│ 💡 Sugerencias:                                              │
│ [+ Drill] [+ Utility knife] [+ Tape measure]                │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Agregar herramienta:                                    │ │
│ │ ┌─────────────────────────────────────────┐  [+]        │ │
│ │ │                                         │             │ │
│ │ └─────────────────────────────────────────┘             │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Herramientas agregadas:                                     │
│ • Power drill  [×]                                          │
│ • Utility knife  [×]                                        │
│ • Measuring tape  [×]                                       │
│                                                             │
│                  [← Anterior]  [❌ Cancelar]  [Siguiente →] │
└─────────────────────────────────────────────────────────────┘
```

**Paso 4: Referencias y Recursos**
```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Crear SOP - Paso 4 de 5: Referencias                     │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ ●━━━━●━━━━●━━━━●━━━━○                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 📸 FOTOS Y ARCHIVOS DE REFERENCIA (opcional)                │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                                                         │ │
│ │         📁 ARRASTRA ARCHIVOS AQUÍ                       │ │
│ │            o haz click para seleccionar                 │ │
│ │                                                         │ │
│ │         Formatos: JPG, PNG, PDF, DOC                    │ │
│ │                                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Archivos agregados:                                         │
│ 📄 drywall_example.jpg (2.3 MB)  [×]                        │
│ 📄 installation_guide.pdf (1.1 MB)  [×]                     │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ 🎥 VIDEO TUTORIAL (opcional)                                │
│                                                             │
│ URL de YouTube o Vimeo:                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ https://youtube.com/watch?v=...                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ 💡 CONSEJOS Y TIPS (opcional)                               │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ - Siempre usar guantes de protección                   │ │
│ │ - Verificar medidas dos veces antes de cortar          │ │
│ │ - Trabajar en área bien ventilada                      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ⚠️ ERRORES COMUNES (opcional)                               │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ - No medir correctamente antes de cortar               │ │
│ │ - Aplicar demasiado compound en primera capa           │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│                  [← Anterior]  [❌ Cancelar]  [Siguiente →] │
└─────────────────────────────────────────────────────────────┘
```

**Paso 5: Preview y Confirmación**
```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Crear SOP - Paso 5 de 5: Vista Previa                    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ ●━━━━●━━━━●━━━━●━━━━●                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 👀 VISTA PREVIA - Así lo verán los empleados:               │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📋 INSTALACIÓN DE DRYWALL - SALA ESTÁNDAR               │ │
│ │ ─────────────────────────────────────────────────────── │ │
│ │ Categoría: PREP                                         │ │
│ │ Tiempo estimado: 2h 30min                               │ │
│ │                                                         │ │
│ │ 📝 Descripción:                                          │ │
│ │ Proceso completo para instalación de drywall...        │ │
│ │                                                         │ │
│ │ ✅ Pasos a seguir:                                       │ │
│ │  ☐ 1. Medir área de trabajo                            │ │
│ │  ☐ 2. Cortar drywall sheets                            │ │
│ │  ☐ 3. Instalar sheets con tornillos                    │ │
│ │  ☐ 4. Aplicar compound en juntas                       │ │
│ │                                                         │ │
│ │ 🧰 Materiales:                                           │ │
│ │  • Drywall sheets (4x8)                                │ │
│ │  • Joint compound                                       │ │
│ │  • Drywall screws (1.25")                              │ │
│ │                                                         │ │
│ │ 🔧 Herramientas:                                         │ │
│ │  • Power drill                                          │ │
│ │  • Utility knife                                        │ │
│ │  • Measuring tape                                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ✨ Todo se ve bien? Guarda el SOP para hacerlo disponible.  │
│                                                             │
│ ☑️ Activar SOP inmediatamente                               │
│                                                             │
│           [← Anterior]  [💾 GUARDAR SOP]  [❌ Cancelar]     │
└─────────────────────────────────────────────────────────────┘
```

---

### **OPCIÓN 2: Formulario con Tabs (Más Compacto)**

```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Crear Nuevo SOP                                          │
├─────────────────────────────────────────────────────────────┤
│ [📝 Básico] [✅ Pasos] [🧰 Mat/Tools] [📸 Referencias]      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🎯 INFORMACIÓN BÁSICA                                       │
│                                                             │
│ [Campos del formulario básico aquí]                         │
│                                                             │
│                                              [💾 Guardar]   │
└─────────────────────────────────────────────────────────────┘
```

---

### **OPCIÓN 3: Templates Predefinidos (Quick Start)** ⭐⭐ MUY RECOMENDADO

```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Crear Nuevo SOP                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🚀 EMPEZAR DESDE UNA PLANTILLA:                             │
│                                                             │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│ │ 🧱 DRYWALL  │ │ 🎨 PINTURA   │ │ 🔨 CARPINT.  │         │
│ │             │ │              │ │              │         │
│ │ • 6 pasos   │ │ • 8 pasos    │ │ • 10 pasos   │         │
│ │ • 5 tools   │ │ • 7 tools    │ │ • 12 tools   │         │
│ │             │ │              │ │              │         │
│ │   [Usar]    │ │   [Usar]     │ │   [Usar]     │         │
│ └──────────────┘ └──────────────┘ └──────────────┘         │
│                                                             │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│ │ 🚿 PLOMERÍA │ │ ⚡ ELECTRIC  │ │ 📋 OTRO      │         │
│ │             │ │              │ │              │         │
│ │ • 7 pasos   │ │ • 9 pasos    │ │ Desde cero   │         │
│ │ • 8 tools   │ │ • 11 tools   │ │              │         │
│ │             │ │              │ │              │         │
│ │   [Usar]    │ │   [Usar]     │ │   [Usar]     │         │
│ └──────────────┘ └──────────────┘ └──────────────┘         │
│                                                             │
│              o [Crear desde cero →]                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ **IMPLEMENTACIÓN TÉCNICA**

### **Cambios Necesarios:**

#### 1. **Nuevo Template: `sop_creator_wizard.html`**
```html
{% extends "core/base.html" %}
{% load i18n static %}

{% block extra_css %}
<style>
  .wizard-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .wizard-progress {
    display: flex;
    justify-content: space-between;
    margin-bottom: 2rem;
  }
  
  .wizard-step {
    flex: 1;
    text-align: center;
    position: relative;
  }
  
  .wizard-step.active .step-circle {
    background: #0d6efd;
    color: white;
  }
  
  .wizard-step.completed .step-circle {
    background: #198754;
    color: white;
  }
  
  .step-circle {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #e9ecef;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 0.5rem;
    font-weight: bold;
  }
  
  .step-content {
    display: none;
  }
  
  .step-content.active {
    display: block;
    animation: fadeIn 0.3s;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  .suggestion-pills {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin: 1rem 0;
  }
  
  .suggestion-pill {
    padding: 0.25rem 0.75rem;
    background: #e7f1ff;
    border: 1px solid #0d6efd;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .suggestion-pill:hover {
    background: #0d6efd;
    color: white;
  }
  
  .drag-drop-zone {
    border: 2px dashed #dee2e6;
    border-radius: 0.5rem;
    padding: 3rem;
    text-align: center;
    background: #f8f9fa;
    cursor: pointer;
    transition: all 0.3s;
  }
  
  .drag-drop-zone:hover {
    border-color: #0d6efd;
    background: #e7f1ff;
  }
  
  .drag-drop-zone.dragover {
    border-color: #198754;
    background: #d1e7dd;
  }
  
  .preview-card {
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 0.5rem;
    padding: 1.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
</style>
{% endblock %}

{% block content %}
<div class="wizard-container">
  <!-- Wizard Progress -->
  <div class="wizard-progress">
    <div class="wizard-step active" data-step="1">
      <div class="step-circle">1</div>
      <small>{% trans "Básico" %}</small>
    </div>
    <div class="wizard-step" data-step="2">
      <div class="step-circle">2</div>
      <small>{% trans "Pasos" %}</small>
    </div>
    <div class="wizard-step" data-step="3">
      <div class="step-circle">3</div>
      <small>{% trans "Materiales" %}</small>
    </div>
    <div class="wizard-step" data-step="4">
      <div class="step-circle">4</div>
      <small>{% trans "Referencias" %}</small>
    </div>
    <div class="wizard-step" data-step="5">
      <div class="step-circle">5</div>
      <small>{% trans "Preview" %}</small>
    </div>
  </div>
  
  <form method="post" enctype="multipart/form-data" id="sop-wizard-form">
    {% csrf_token %}
    
    <!-- Step 1: Basic Info -->
    <div class="step-content active" data-step="1">
      <h3>🎯 {% trans "Información Básica" %}</h3>
      <p class="text-muted">{% trans "Define el nombre y categoría del SOP" %}</p>
      
      <div class="mb-3">
        <label class="form-label">{% trans "Nombre del SOP" %}*</label>
        <input type="text" name="name" class="form-control form-control-lg" 
               placeholder='{% trans "Ej: Instalación de Drywall - Sala Estándar" %}' required>
        <small class="form-text text-muted">{% trans "Nombre descriptivo y específico" %}</small>
      </div>
      
      <div class="mb-3">
        <label class="form-label">{% trans "Categoría" %}*</label>
        {{ form.category }}
      </div>
      
      <div class="mb-3">
        <label class="form-label">{% trans "Descripción breve" %}</label>
        <textarea name="description" class="form-control" rows="3" 
                  placeholder='{% trans "Describe en 1-2 líneas qué hace este SOP..." %}'></textarea>
      </div>
      
      <div class="row">
        <div class="col-md-6">
          <label class="form-label">{% trans "Tiempo estimado (horas)" %}</label>
          <input type="number" name="time_hours" class="form-control" min="0" step="0.5" value="0">
        </div>
        <div class="col-md-6">
          <label class="form-label">{% trans "Minutos" %}</label>
          <input type="number" name="time_minutes" class="form-control" min="0" max="59" value="0">
        </div>
      </div>
    </div>
    
    <!-- Step 2: Checklist Steps -->
    <div class="step-content" data-step="2">
      <h3>✅ {% trans "Lista de Pasos a Seguir" %}</h3>
      <div class="alert alert-info">
        <i class="bi bi-lightbulb"></i> 
        {% trans "Agrega pasos en orden secuencial. Los empleados los verán como checklist." %}
      </div>
      
      <div class="mb-3">
        <div class="input-group input-group-lg">
          <input type="text" id="step-input" class="form-control" 
                 placeholder='{% trans "Ej: Medir y marcar ubicación de sheets" %}'>
          <button type="button" class="btn btn-primary" id="add-step">
            <i class="bi bi-plus-lg"></i> {% trans "Agregar" %}
          </button>
        </div>
      </div>
      
      <h5>📋 {% trans "Pasos agregados" %} (<span id="step-count">0</span>)</h5>
      <p class="text-muted small">{% trans "Arrastra para reordenar" %}</p>
      <ul id="steps-list" class="list-group mb-3"></ul>
      <input type="hidden" name="steps" id="id_steps">
      
      <div class="alert alert-warning" id="steps-warning" style="display: none;">
        ⚠️ {% trans "Debes agregar al menos 1 paso" %}
      </div>
    </div>
    
    <!-- Step 3: Materials & Tools -->
    <div class="step-content" data-step="3">
      <h3>🧰 {% trans "Materiales y Herramientas" %}</h3>
      
      <h5>{% trans "Materiales Necesarios" %}</h5>
      <div class="alert alert-info">
        <i class="bi bi-lightbulb"></i> 
        {% trans "Sugerencias comunes:" %}
      </div>
      <div class="suggestion-pills" id="material-suggestions"></div>
      
      <div class="input-group mb-3">
        <input type="text" id="material-input" class="form-control" 
               placeholder='{% trans "Ej: Drywall sheets (4x8)" %}'>
        <button type="button" class="btn btn-primary" id="add-material">
          <i class="bi bi-plus-lg"></i>
        </button>
      </div>
      
      <ul id="materials-list" class="list-group mb-4"></ul>
      <input type="hidden" name="materials_list" id="id_materials_list">
      
      <hr>
      
      <h5>{% trans "Herramientas Requeridas" %}</h5>
      <div class="suggestion-pills" id="tool-suggestions"></div>
      
      <div class="input-group mb-3">
        <input type="text" id="tool-input" class="form-control" 
               placeholder='{% trans "Ej: Power drill" %}'>
        <button type="button" class="btn btn-primary" id="add-tool">
          <i class="bi bi-plus-lg"></i>
        </button>
      </div>
      
      <ul id="tools-list" class="list-group"></ul>
      <input type="hidden" name="tools_list" id="id_tools_list">
    </div>
    
    <!-- Step 4: References -->
    <div class="step-content" data-step="4">
      <h3>📸 {% trans "Referencias y Recursos" %}</h3>
      
      <h5>{% trans "Fotos y Archivos de Referencia" %}</h5>
      <div class="drag-drop-zone" id="drop-zone">
        <i class="bi bi-cloud-upload" style="font-size: 3rem; color: #6c757d;"></i>
        <p class="mt-3">{% trans "Arrastra archivos aquí" %}</p>
        <p class="text-muted small">{% trans "o haz click para seleccionar" %}</p>
        <p class="text-muted small">{% trans "Formatos: JPG, PNG, PDF, DOC" %}</p>
        <input type="file" name="reference_files" id="file-input" multiple 
               accept="image/*,.pdf,.doc,.docx" style="display: none;">
      </div>
      <div id="file-list" class="mt-3"></div>
      
      <hr>
      
      <h5>🎥 {% trans "Video Tutorial" %}</h5>
      <input type="url" name="video_url" class="form-control" 
             placeholder="https://youtube.com/watch?v=...">
      
      <hr>
      
      <h5>💡 {% trans "Consejos y Tips" %}</h5>
      <textarea name="tips" class="form-control" rows="4" 
                placeholder='{% trans "Ej:\n- Siempre usar guantes de protección\n- Verificar medidas dos veces antes de cortar" %}'></textarea>
      
      <hr>
      
      <h5>⚠️ {% trans "Errores Comunes" %}</h5>
      <textarea name="common_errors" class="form-control" rows="4" 
                placeholder='{% trans "Ej:\n- No medir correctamente antes de cortar\n- Aplicar demasiado compound en primera capa" %}'></textarea>
    </div>
    
    <!-- Step 5: Preview -->
    <div class="step-content" data-step="5">
      <h3>👀 {% trans "Vista Previa" %}</h3>
      <p class="text-muted">{% trans "Así lo verán los empleados:" %}</p>
      
      <div class="preview-card" id="sop-preview">
        <!-- Dynamic preview will be generated here -->
      </div>
      
      <div class="form-check mt-4">
        <input class="form-check-input" type="checkbox" name="is_active" id="is_active" checked>
        <label class="form-check-label" for="is_active">
          {% trans "Activar SOP inmediatamente" %}
        </label>
      </div>
    </div>
    
    <!-- Navigation Buttons -->
    <div class="d-flex justify-content-between mt-4">
      <button type="button" class="btn btn-secondary" id="prev-btn" style="display: none;">
        <i class="bi bi-arrow-left"></i> {% trans "Anterior" %}
      </button>
      <div class="flex-grow-1"></div>
      <a href="{% url 'sop_library' %}" class="btn btn-outline-secondary me-2">
        ❌ {% trans "Cancelar" %}
      </a>
      <button type="button" class="btn btn-primary" id="next-btn">
        {% trans "Siguiente" %} <i class="bi bi-arrow-right"></i>
      </button>
      <button type="submit" class="btn btn-success" id="submit-btn" style="display: none;">
        <i class="bi bi-save"></i> {% trans "Guardar SOP" %}
      </button>
    </div>
  </form>
</div>

<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
<script src="{% static 'core/sop_wizard.js' %}"></script>
{% endblock %}
```

#### 2. **Nuevo JavaScript: `core/static/core/sop_wizard.js`**
```javascript
// Wizard navigation
let currentStep = 1;
const totalSteps = 5;

// Data storage
const sopData = {
  steps: [],
  materials: [],
  tools: []
};

// Suggestions by category
const suggestions = {
  'PREP': {
    materials: ['Drywall sheets', 'Joint compound', 'Screws', 'Tape'],
    tools: ['Power drill', 'Utility knife', 'Tape measure', 'Level']
  },
  'PAINT': {
    materials: ['Paint', 'Primer', 'Brushes', 'Rollers', 'Tape'],
    tools: ['Paint tray', 'Drop cloth', 'Ladder', 'Putty knife']
  },
  'INSTALL': {
    materials: ['Lumber', 'Nails', 'Screws', 'Brackets'],
    tools: ['Hammer', 'Saw', 'Drill', 'Level', 'Square']
  }
};

// Initialize wizard
document.addEventListener('DOMContentLoaded', function() {
  setupWizardNavigation();
  setupDynamicLists();
  setupFileUpload();
  setupSuggestions();
  updateStepIndicator();
});

function setupWizardNavigation() {
  const nextBtn = document.getElementById('next-btn');
  const prevBtn = document.getElementById('prev-btn');
  const submitBtn = document.getElementById('submit-btn');
  
  nextBtn.addEventListener('click', () => {
    if (validateCurrentStep()) {
      currentStep++;
      showStep(currentStep);
    }
  });
  
  prevBtn.addEventListener('click', () => {
    currentStep--;
    showStep(currentStep);
  });
  
  // Handle form submission with validation
  document.getElementById('sop-wizard-form').addEventListener('submit', function(e) {
    if (!validateAllSteps()) {
      e.preventDefault();
      alert('Por favor completa todos los campos requeridos');
    }
  });
}

function showStep(step) {
  // Hide all steps
  document.querySelectorAll('.step-content').forEach(el => {
    el.classList.remove('active');
  });
  
  // Show current step
  document.querySelector(`.step-content[data-step="${step}"]`).classList.add('active');
  
  // Update step indicators
  updateStepIndicator();
  
  // Update buttons
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');
  const submitBtn = document.getElementById('submit-btn');
  
  prevBtn.style.display = step === 1 ? 'none' : 'inline-block';
  nextBtn.style.display = step === totalSteps ? 'none' : 'inline-block';
  submitBtn.style.display = step === totalSteps ? 'inline-block' : 'none';
  
  // Generate preview on last step
  if (step === totalSteps) {
    generatePreview();
  }
}

function updateStepIndicator() {
  document.querySelectorAll('.wizard-step').forEach((el, idx) => {
    const stepNum = idx + 1;
    el.classList.remove('active', 'completed');
    
    if (stepNum === currentStep) {
      el.classList.add('active');
    } else if (stepNum < currentStep) {
      el.classList.add('completed');
    }
  });
}

function validateCurrentStep() {
  switch(currentStep) {
    case 1:
      const name = document.querySelector('input[name="name"]').value.trim();
      const category = document.querySelector('select[name="category"]').value;
      if (!name || !category) {
        alert('Por favor completa el nombre y categoría');
        return false;
      }
      return true;
      
    case 2:
      if (sopData.steps.length === 0) {
        document.getElementById('steps-warning').style.display = 'block';
        return false;
      }
      document.getElementById('steps-warning').style.display = 'none';
      return true;
      
    case 3:
      // Materials and tools are optional
      return true;
      
    case 4:
      // References are optional
      return true;
      
    default:
      return true;
  }
}

function validateAllSteps() {
  // Final validation before submission
  const name = document.querySelector('input[name="name"]').value.trim();
  const category = document.querySelector('select[name="category"]').value;
  
  return name && category && sopData.steps.length > 0;
}

function setupDynamicLists() {
  // Steps list
  setupList('step', 'steps', sopData.steps);
  
  // Materials list
  setupList('material', 'materials', sopData.materials);
  
  // Tools list
  setupList('tool', 'tools', sopData.tools);
}

function setupList(type, fieldName, dataArray) {
  const input = document.getElementById(`${type}-input`);
  const addBtn = document.getElementById(`add-${type}`);
  const list = document.getElementById(`${fieldName}-list`);
  const hiddenField = document.getElementById(`id_${fieldName}_list`) || 
                      document.getElementById(`id_${fieldName}`);
  
  function renderList() {
    list.innerHTML = '';
    dataArray.forEach((item, idx) => {
      const li = document.createElement('li');
      li.className = 'list-group-item d-flex align-items-center';
      li.innerHTML = `
        <span class="drag-handle me-2" style="cursor: move;">⋮⋮</span>
        ${type === 'step' ? `<i class="bi bi-check-square me-2"></i> ${idx + 1}.` : '•'}
        <span class="flex-grow-1 ms-2">${item}</span>
        <button type="button" class="btn btn-sm btn-danger" onclick="removeItem('${type}', ${idx})">
          <i class="bi bi-x"></i>
        </button>
      `;
      list.appendChild(li);
    });
    
    // Update hidden field
    if (hiddenField) {
      hiddenField.value = JSON.stringify(dataArray);
    }
    
    // Update counter for steps
    if (type === 'step') {
      const counter = document.getElementById('step-count');
      if (counter) counter.textContent = dataArray.length;
    }
    
    // Make list sortable
    new Sortable(list, {
      handle: '.drag-handle',
      animation: 150,
      onEnd: function() {
        // Update array order
        const items = Array.from(list.querySelectorAll('.flex-grow-1')).map(el => el.textContent.trim());
        dataArray.length = 0;
        dataArray.push(...items);
        renderList();
      }
    });
  }
  
  addBtn.addEventListener('click', () => {
    const value = input.value.trim();
    if (value) {
      dataArray.push(value);
      input.value = '';
      renderList();
    }
  });
  
  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addBtn.click();
    }
  });
  
  renderList();
  
  // Make removeItem global
  window.removeItem = function(type, idx) {
    if (type === 'step') sopData.steps.splice(idx, 1);
    else if (type === 'material') sopData.materials.splice(idx, 1);
    else if (type === 'tool') sopData.tools.splice(idx, 1);
    renderList();
  };
}

function setupFileUpload() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const fileList = document.getElementById('file-list');
  
  dropZone.addEventListener('click', () => fileInput.click());
  
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });
  
  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
  });
  
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    fileInput.files = e.dataTransfer.files;
    displayFiles();
  });
  
  fileInput.addEventListener('change', displayFiles);
  
  function displayFiles() {
    fileList.innerHTML = '';
    const files = Array.from(fileInput.files);
    
    if (files.length > 0) {
      const ul = document.createElement('ul');
      ul.className = 'list-group';
      
      files.forEach(file => {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        li.innerHTML = `
          <span>
            <i class="bi bi-file-earmark"></i> ${file.name}
          </span>
          <span class="badge bg-secondary">${(file.size / 1024).toFixed(1)} KB</span>
        `;
        ul.appendChild(li);
      });
      
      fileList.appendChild(ul);
    }
  }
}

function setupSuggestions() {
  const categorySelect = document.querySelector('select[name="category"]');
  
  if (categorySelect) {
    categorySelect.addEventListener('change', function() {
      const category = this.value;
      updateSuggestions(category);
    });
  }
}

function updateSuggestions(category) {
  const materialSuggestions = document.getElementById('material-suggestions');
  const toolSuggestions = document.getElementById('tool-suggestions');
  
  if (suggestions[category]) {
    // Material suggestions
    materialSuggestions.innerHTML = suggestions[category].materials.map(item => 
      `<span class="suggestion-pill" onclick="addFromSuggestion('material', '${item}')">
        + ${item}
      </span>`
    ).join('');
    
    // Tool suggestions
    toolSuggestions.innerHTML = suggestions[category].tools.map(item => 
      `<span class="suggestion-pill" onclick="addFromSuggestion('tool', '${item}')">
        + ${item}
      </span>`
    ).join('');
  }
}

window.addFromSuggestion = function(type, value) {
  if (type === 'material') {
    sopData.materials.push(value);
    document.getElementById('materials-list').dispatchEvent(new Event('update'));
  } else if (type === 'tool') {
    sopData.tools.push(value);
    document.getElementById('tools-list').dispatchEvent(new Event('update'));
  }
  
  // Re-render the appropriate list
  const addBtn = document.getElementById(`add-${type}`);
  if (addBtn) {
    // Trigger re-render by simulating add
    setupDynamicLists();
  }
};

function generatePreview() {
  const preview = document.getElementById('sop-preview');
  const name = document.querySelector('input[name="name"]').value;
  const category = document.querySelector('select[name="category"]').selectedOptions[0].text;
  const description = document.querySelector('textarea[name="description"]').value;
  const hours = document.querySelector('input[name="time_hours"]').value || 0;
  const minutes = document.querySelector('input[name="time_minutes"]').value || 0;
  
  let html = `
    <h4>📋 ${name}</h4>
    <hr>
    <p><strong>Categoría:</strong> ${category}</p>
    ${hours > 0 || minutes > 0 ? `<p><strong>Tiempo estimado:</strong> ${hours}h ${minutes}min</p>` : ''}
    ${description ? `<p><strong>Descripción:</strong><br>${description}</p>` : ''}
    
    <h5 class="mt-4">✅ Pasos a seguir:</h5>
    <ul class="list-group mb-3">
      ${sopData.steps.map((step, idx) => `
        <li class="list-group-item">
          <input type="checkbox" class="form-check-input me-2" disabled>
          ${idx + 1}. ${step}
        </li>
      `).join('')}
    </ul>
  `;
  
  if (sopData.materials.length > 0) {
    html += `
      <h5>🧰 Materiales:</h5>
      <ul>
        ${sopData.materials.map(m => `<li>${m}</li>`).join('')}
      </ul>
    `;
  }
  
  if (sopData.tools.length > 0) {
    html += `
      <h5>🔧 Herramientas:</h5>
      <ul>
        ${sopData.tools.map(t => `<li>${t}</li>`).join('')}
      </ul>
    `;
  }
  
  preview.innerHTML = html;
}
```

#### 3. **Actualizar URLs en `core/urls.py`:**
```python
# Add new wizard route
path('planning/sop/create/wizard/', sop_create_wizard, name='sop_create_wizard'),
```

#### 4. **Nueva Vista en `core/views.py`:**
```python
@login_required
def sop_create_wizard(request):
    """
    Wizard-style SOP creator with step-by-step guidance
    """
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    if request.method == "POST":
        # Process form data
        name = request.POST.get('name')
        category = request.POST.get('category')
        description = request.POST.get('description', '')
        tips = request.POST.get('tips', '')
        common_errors = request.POST.get('common_errors', '')
        video_url = request.POST.get('video_url', '')
        is_active = request.POST.get('is_active') == 'on'
        
        # Parse JSON fields
        import json
        steps = json.loads(request.POST.get('steps', '[]'))
        materials_list = json.loads(request.POST.get('materials_list', '[]'))
        tools_list = json.loads(request.POST.get('tools_list', '[]'))
        
        # Create SOP
        sop = ActivityTemplate.objects.create(
            name=name,
            category=category,
            description=description,
            tips=tips,
            common_errors=common_errors,
            video_url=video_url,
            is_active=is_active,
            steps=steps,
            materials_list=materials_list,
            tools_list=tools_list,
            created_by=request.user
        )
        
        # Handle file uploads
        uploaded_files = request.FILES.getlist("reference_files")
        if uploaded_files:
            for f in uploaded_files:
                SOPReferenceFile.objects.create(sop=sop, file=f)
        
        messages.success(request, "✨ SOP creado exitosamente!")
        return redirect("sop_library")
    
    # GET request - show wizard
    form = ActivityTemplateForm()
    context = {
        "form": form,
    }
    return render(request, "core/sop_creator_wizard.html", context)
```

---

## 📊 **COMPARACIÓN DE OPCIONES**

| Característica | Actual | Wizard (Opción 1) | Tabs (Opción 2) | Templates (Opción 3) |
|---|---|---|---|---|
| **Facilidad de uso** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Guía paso a paso** | ❌ | ✅ | ⚠️ | ✅ |
| **Preview en tiempo real** | ❌ | ✅ | ⚠️ | ✅ |
| **Sugerencias inteligentes** | ❌ | ✅ | ✅ | ✅✅ |
| **Templates predefinidos** | ❌ | ❌ | ❌ | ✅✅ |
| **Complejidad técnica** | Baja | Media | Baja | Media-Alta |
| **Tiempo de implementación** | - | 2-3 días | 1 día | 3-4 días |

---

## 🎯 **RECOMENDACIÓN FINAL**

**Implementar OPCIÓN 1 (Wizard) + OPCIÓN 3 (Templates)**

### **Por qué esta combinación:**
1. ✅ **Wizard** = UX súper intuitivo, paso a paso
2. ✅ **Templates** = Acelera creación para casos comunes
3. ✅ **Preview** = Usuario ve resultado antes de guardar
4. ✅ **Sugerencias** = Reduce errores y omisiones

### **Flujo propuesto:**
```
Usuario va a crear SOP
  ↓
¿Usar template predefinido?
  ↓ SÍ                          ↓ NO
  ↓                             ↓
Selecciona template    →    Wizard paso a paso
  ↓                             ↓
Pre-llena campos              Guía completa
  ↓                             ↓
Edita lo necesario            Agrega detalles
  ↓                             ↓
  └──────────→ Preview y Guardar ←──────────┘
```

---

## 📝 **PRÓXIMOS PASOS**

1. ✅ **Aprobar diseño** del wizard con el usuario
2. ⚙️ **Implementar** nuevo template y JavaScript
3. 🧪 **Testing** con usuarios reales
4. 📊 **Medir** tiempo de creación antes/después
5. 🔄 **Iterar** basado en feedback

---

## 💡 **MEJORAS ADICIONALES OPCIONALES**

1. **Autoguardado** - Guardar progreso automáticamente
2. **Duplicar SOP** - Crear variaciones de SOPs existentes
3. **Importar desde Excel/CSV** - Bulk creation
4. **AI Suggestions** - Sugerir steps basado en categoría
5. **Video recording** - Grabar video tutorial directo desde la app
6. **Mobile-friendly** - Optimizar para tablets/móviles

---

**Estimación de tiempo de implementación completa: 5-7 días de desarrollo**
