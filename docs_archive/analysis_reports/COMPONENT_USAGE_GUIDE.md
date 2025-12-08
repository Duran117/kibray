# Kibray Design System - Component Usage Guide

## Quick Start

### 1. Extend Base Layout

```django
{% extends "core/base_modern.html" %}
{% load static %}
{% load i18n %}

{% block title %}My Page - Kibray{% endblock %}

{% block page_header %}
    <h1 class="text-2xl font-bold">My Page Title</h1>
{% endblock %}

{% block content %}
    <!-- Your content here -->
{% endblock %}
```

## Components Reference

### Card Component
**File**: `core/templates/core/components/card.html`

**Purpose**: Reusable card container with optional header and footer

**Usage**:
```django
{% include "core/components/card.html" with title="Card Title" icon="box" %}
    <p>Card content goes here</p>
{% include "core/components/card.html" with close_card=True only %}
```

**Advanced Usage** (with header action):
```django
{% include "core/components/card.html" with title="Projects" icon="folder" %}
    {% block header_action %}
        <a href="{% url 'project_create' %}" class="text-sm text-indigo-600 hover:text-indigo-700">
            + Add Project
        </a>
    {% endblock %}
    
    <!-- Card content -->
    <div class="space-y-4">
        {% for project in projects %}
            <div>{{ project.name }}</div>
        {% endfor %}
    </div>
    
    {% block footer %}
        <a href="{% url 'project_list' %}" class="text-sm text-slate-600 hover:text-slate-700">
            View All Projects →
        </a>
    {% endblock %}
{% include "core/components/card.html" with close_card=True only %}
```

---

### Form Section Component
**File**: `core/templates/core/components/form_section.html`

**Purpose**: Styled form section with icon and title

**Usage**:
```django
{% include "core/components/form_section.html" with icon="info-circle" title=_("Basic Information") %}
    <div class="space-y-4">
        <div>
            <label class="block text-sm font-semibold text-slate-700 mb-2">
                {% trans "Name" %}
            </label>
            {{ form.name }}
        </div>
        
        <div>
            <label class="block text-sm font-semibold text-slate-700 mb-2">
                {% trans "Description" %}
            </label>
            {{ form.description }}
        </div>
    </div>
{% include "core/components/form_section.html" with close_section=True only %}
```

**With Description**:
```django
{% include "core/components/form_section.html" with icon="palette" title=_("Color Settings") description=_("Choose colors for this project") %}
    <!-- Form fields -->
{% include "core/components/form_section.html" with close_section=True only %}
```

---

### Button Component
**File**: `core/templates/core/components/button.html`

**Purpose**: Styled button with variants

**Variants**: `primary`, `secondary`, `danger`, `success`

**Usage** (simple):
```django
{% include "core/components/button.html" with text=_("Save") variant="primary" %}
```

**Usage** (with icon):
```django
{% include "core/components/button.html" with text=_("Delete") variant="danger" icon="trash" %}
```

**Usage** (as link):
```django
{% include "core/components/button.html" with text=_("View Details") variant="secondary" icon="arrow-right" href="/projects/1/" %}
```

**Usage** (full customization):
```django
{% include "core/components/button.html" with text=_("Create Project") variant="primary" icon="plus-circle" type="submit" class_extra="mt-4" %}
```

---

### Photo Grid Component
**File**: `core/templates/core/components/photo_grid.html`

**Purpose**: Square thumbnail grid with annotation support

**Usage** (existing photos):
```django
{% if changeorder.photos.all %}
    {% include "core/components/photo_grid.html" with photos=changeorder.photos.all is_existing=True %}
{% endif %}
```

**Usage** (custom photos):
```django
{% include "core/components/photo_grid.html" with photos=project.images.all is_existing=True show_descriptions=True %}
```

**JavaScript Integration**:
```javascript
// Photo grid automatically integrates with Kibray.PhotoGallery
// Buttons have data-photo-id and data-image-url attributes
// Edit button calls: Kibray.PhotoGallery.handleEdit()
// Delete button calls: Kibray.PhotoGallery.handleDelete()

// Or define custom functions:
function openPhotoEditor(imageUrl, photoId, annotations) {
    // Your editor logic
}

function deletePhoto(photoId) {
    // Your delete logic
}
```

---

### Header Component
**File**: `core/templates/core/components/header.html`

**Purpose**: Navigation header with language switcher and user menu

**Usage**: Automatically included in `base_modern.html`

**Customization**: Edit the file directly or override blocks in your template

---

### Sidebar Component
**File**: `core/templates/core/components/sidebar.html`

**Purpose**: Fixed navigation sidebar

**Usage**: Automatically included in `base_modern.html`

**Customization**:
```django
{% block sidebar %}
    {% include "core/components/sidebar.html" %}
{% endblock %}
```

**Or create custom sidebar**:
```django
{% block sidebar %}
    <aside class="fixed left-0 top-16 h-full w-64 bg-white border-r border-slate-200 p-4">
        <!-- Custom sidebar content -->
    </aside>
{% endblock %}
```

---

### Photo Editor Modal Component
**File**: `core/templates/core/components/photo_editor_modal.html`

**Purpose**: Full-screen photo annotation modal

**Usage**:
```django
{% include "core/components/photo_editor_modal.html" %}
```

**Required JavaScript Functions** (see changeorder_form_clean.html for examples):
- `openPhotoEditor(imageUrl, photoId, annotations)`
- `openPhotoEditorNew(imageUrl, index, isNewPhoto)`
- `closePhotoEditor()`
- `setDrawingMode(mode)` - modes: 'draw', 'arrow', 'text'
- `setDrawingColor(color, element)`
- `undoDrawing()`
- `clearDrawing()`
- `saveAnnotations()`

**Canvas Drawing Variables**:
```javascript
let canvas, ctx, isDrawing, drawingMode, drawingColor;
let startX, startY, currentAnnotations, currentPhotoId;
let drawingHistory, currentImageUrl;
```

---

## JavaScript Utilities

### Kibray.Toast
**Purpose**: Show toast notifications

**Usage**:
```javascript
// Success
Kibray.Toast.show('Changes saved successfully', 'success');

// Error
Kibray.Toast.show('Failed to save changes', 'error');

// Warning
Kibray.Toast.show('Please review your input', 'warning');

// Info
Kibray.Toast.show('Processing your request...', 'info');

// Custom duration (default: 3000ms)
Kibray.Toast.show('Quick message', 'info', 1000);

// Persistent (duration: 0)
Kibray.Toast.show('Stay forever', 'info', 0);
```

---

### Kibray.PhotoGallery
**Purpose**: Handle photo gallery interactions

**Auto-initialization**: Runs on DOMContentLoaded if `.photo-edit-btn` or `.photo-delete-btn` exists

**Manual initialization**:
```javascript
Kibray.PhotoGallery.init();
```

**Methods**:
```javascript
// Initialize event listeners
Kibray.PhotoGallery.init();

// Handle edit button click (called internally via event delegation)
Kibray.PhotoGallery.handleEdit(event);

// Handle delete button click (called internally via event delegation)
Kibray.PhotoGallery.handleDelete(event);

// Initialize thumbnail annotations
Kibray.PhotoGallery.initThumbnails();

// Redraw specific thumbnail
Kibray.PhotoGallery.redrawThumbnail(photoId, annotations);
```

**Expected HTML Structure**:
```html
<div data-photo-id="123">
    <script type="application/json" class="photo-annotations-data">
        [{"type": "line", "x1": 10, "y1": 10, "x2": 50, "y2": 50, "color": "#dc2626"}]
    </script>
    <img src="/media/photo.jpg" alt="Photo">
    <canvas class="photo-annotations-canvas"></canvas>
    <button class="photo-edit-btn" data-photo-id="123" data-image-url="/media/photo.jpg">Edit</button>
    <button class="photo-delete-btn" data-photo-id="123">Delete</button>
</div>
```

---

### Kibray.Forms
**Purpose**: Form validation utilities

**Usage**:
```javascript
// Validate required fields
const isValid = Kibray.Forms.validateRequired('myFormId');

if (!isValid) {
    Kibray.Toast.show('Please fill all required fields', 'error');
}
```

---

## Tailwind Utility Classes

### Common Patterns

**Spacing**:
```html
<div class="p-4">Padding all sides</div>
<div class="px-4 py-2">Padding horizontal and vertical</div>
<div class="mt-4 mb-2">Margin top and bottom</div>
<div class="space-y-4">Vertical spacing between children</div>
<div class="gap-4">Gap in flex/grid</div>
```

**Layout**:
```html
<div class="flex items-center justify-between">Flexbox</div>
<div class="grid grid-cols-3 gap-4">Grid 3 columns</div>
<div class="hidden md:block">Hidden on mobile, visible on desktop</div>
```

**Typography**:
```html
<h1 class="text-2xl font-bold text-slate-900">Heading</h1>
<p class="text-sm text-slate-600">Small gray text</p>
<span class="text-red-600 font-semibold">Red text</span>
```

**Colors**:
- Primary: `bg-indigo-600`, `text-indigo-600`, `border-indigo-600`
- Success: `bg-green-600`, `text-green-600`
- Warning: `bg-yellow-600`, `text-yellow-600`
- Danger: `bg-red-600`, `text-red-600`
- Neutral: `bg-slate-200`, `text-slate-700`

**Borders & Shadows**:
```html
<div class="border border-slate-200 rounded-lg shadow-md">Card</div>
<div class="ring-1 ring-slate-200">Subtle border</div>
```

**Transitions**:
```html
<button class="transition hover:bg-indigo-700">Smooth transition</button>
<div class="transition-all duration-300">Custom duration</div>
```

---

## Responsive Breakpoints

- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

**Usage**:
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
    <!-- 1 column on mobile, 2 on tablet, 3 on desktop -->
</div>

<button class="hidden md:inline-flex">
    <!-- Hidden on mobile, visible on desktop -->
</button>
```

---

## Form Styling

### Input Fields
```html
<input type="text" 
       class="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition">
```

### Textareas
```html
<textarea 
    class="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
    rows="4"></textarea>
```

### Select Dropdowns
```html
<select 
    class="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition">
    <option>Option 1</option>
</select>
```

### Labels
```html
<label class="block text-sm font-semibold text-slate-700 mb-2">
    Field Name <span class="text-red-600">*</span>
</label>
```

### Error Messages
```html
<div class="mt-2 text-sm text-red-600">
    <p>This field is required</p>
</div>
```

---

## Icons

Using **Bootstrap Icons** via CDN in `base_modern.html`

**Usage**:
```html
<i class="bi bi-check-circle text-green-600"></i>
<i class="bi bi-x-circle text-red-600"></i>
<i class="bi bi-info-circle text-blue-600"></i>
<i class="bi bi-pencil text-slate-600"></i>
<i class="bi bi-trash text-red-600"></i>
```

**Common Icons**:
- `check-circle`, `check-circle-fill` - Success
- `x-circle`, `x-circle-fill` - Close/Cancel
- `info-circle`, `info-circle-fill` - Information
- `exclamation-triangle`, `exclamation-triangle-fill` - Warning
- `pencil`, `pencil-square` - Edit
- `trash`, `trash3` - Delete
- `plus-circle`, `plus-circle-fill` - Add
- `arrow-left`, `arrow-right` - Navigation
- `camera`, `camera-fill` - Photos
- `folder`, `folder-fill` - Projects
- `calendar`, `calendar-fill` - Schedule
- `cash`, `cash-stack` - Financial

**Full Icon List**: https://icons.getbootstrap.com/

---

## Best Practices

1. **Always use components** instead of custom HTML when possible
2. **Use Tailwind utilities** instead of custom CSS
3. **Test responsive design** on mobile, tablet, desktop
4. **Add i18n tags** {% trans %} for all user-facing text
5. **Use semantic HTML** (button, nav, main, article, section)
6. **Add ARIA labels** for accessibility
7. **Test with keyboard navigation**
8. **Keep JavaScript modular** and use Kibray namespace
9. **Handle errors gracefully** with toast notifications
10. **Document custom components** if you create new ones

---

## Common Patterns

### Page Header with Action
```django
{% block page_header %}
<div class="flex items-center justify-between">
    <div class="flex items-center gap-4">
        <div class="w-12 h-12 rounded-xl bg-indigo-600 flex items-center justify-center text-white">
            <i class="bi bi-folder text-2xl"></i>
        </div>
        <div>
            <h1 class="text-2xl font-bold text-slate-900">Projects</h1>
            <p class="text-sm text-slate-600">Manage your projects</p>
        </div>
    </div>
    <a href="{% url 'project_create' %}" 
       class="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition">
        <i class="bi bi-plus-circle"></i>
        New Project
    </a>
</div>
{% endblock %}
```

### Empty State
```html
<div class="flex flex-col items-center justify-center py-12 text-center">
    <i class="bi bi-inbox text-6xl text-slate-300 mb-4"></i>
    <h3 class="text-lg font-semibold text-slate-700 mb-2">No items yet</h3>
    <p class="text-sm text-slate-500 mb-6">Get started by creating your first item</p>
    <a href="#" class="inline-flex items-center gap-2 bg-indigo-600 text-white px-6 py-3 rounded-lg">
        <i class="bi bi-plus-circle"></i>
        Create Item
    </a>
</div>
```

### Loading Spinner
```html
<div class="flex items-center justify-center py-12">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
</div>
```

### Alert Boxes
```html
<!-- Success -->
<div class="flex gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
    <i class="bi bi-check-circle-fill text-green-600"></i>
    <div class="text-sm text-green-800">Operation successful!</div>
</div>

<!-- Error -->
<div class="flex gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
    <i class="bi bi-exclamation-triangle-fill text-red-600"></i>
    <div class="text-sm text-red-800">Something went wrong</div>
</div>

<!-- Warning -->
<div class="flex gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
    <i class="bi bi-info-circle-fill text-yellow-600"></i>
    <div class="text-sm text-yellow-800">Please review this</div>
</div>

<!-- Info -->
<div class="flex gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
    <i class="bi bi-info-circle-fill text-blue-600"></i>
    <div class="text-sm text-blue-800">Additional information</div>
</div>
```

---

## Need Help?

- **Component Examples**: See `changeorder_form_clean.html` for comprehensive usage
- **JavaScript Examples**: See `kibray-core.js` for utility functions
- **Tailwind Docs**: https://tailwindcss.com/docs
- **Bootstrap Icons**: https://icons.getbootstrap.com/
- **Django i18n**: https://docs.djangoproject.com/en/stable/topics/i18n/

---

**Last Updated**: November 2025  
**Version**: 1.0  
**Status**: Phase 1 Complete
