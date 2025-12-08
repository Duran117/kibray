# Design System Architecture

## Component Hierarchy

```
┌────────────────────────────────────────────────────────────────────┐
│                         base_modern.html                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                         Header                                │ │
│  │  - Logo                                                       │ │
│  │  - Navigation (Desktop/Mobile)                                │ │
│  │  - Language Switcher                                          │ │
│  │  - User Dropdown                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────┐  ┌──────────────────────────────────────────────┐ │
│  │          │  │          Page Header Block                    │ │
│  │          │  │  (Defined in child template)                  │ │
│  │ Sidebar  │  │                                                │ │
│  │          │  └──────────────────────────────────────────────┘ │
│  │ - Home   │  ┌──────────────────────────────────────────────┐ │
│  │ - Projects│ │          Content Block                        │ │
│  │ - Schedule│ │  (Defined in child template)                  │ │
│  │ - Finance │ │                                                │ │
│  │ - Time   │  │  ┌─────────────────────────────────────────┐ │ │
│  │          │  │  │      Form Section                      │ │ │
│  │          │  │  │  - Icon + Title                        │ │ │
│  │          │  │  │  - Content Block                       │ │ │
│  │          │  │  └─────────────────────────────────────────┘ │ │
│  │          │  │                                                │ │
│  │          │  │  ┌─────────────────────────────────────────┐ │ │
│  │          │  │  │      Card Component                    │ │ │
│  │          │  │  │  - Header (title, icon, action)        │ │ │
│  │          │  │  │  - Content Block                       │ │ │
│  │          │  │  │  - Footer Block                        │ │ │
│  │          │  │  └─────────────────────────────────────────┘ │ │
│  │          │  │                                                │ │
│  │          │  │  ┌─────────────────────────────────────────┐ │ │
│  │          │  │  │      Photo Grid                        │ │ │
│  │          │  │  │  - Thumbnails (aspect-ratio: 1/1)      │ │ │
│  │          │  │  │  - Canvas Overlay (annotations)        │ │ │
│  │          │  │  │  - Edit/Delete Buttons                 │ │ │
│  │          │  │  └─────────────────────────────────────────┘ │ │
│  │          │  │                                                │ │
│  │          │  │  ┌─────────────────────────────────────────┐ │ │
│  │          │  │  │      Button Component                  │ │ │
│  │          │  │  │  - Variants (primary, danger, etc)     │ │ │
│  │          │  │  │  - Icon support                        │ │ │
│  │          │  │  └─────────────────────────────────────────┘ │ │
│  │          │  └──────────────────────────────────────────────┘ │
│  └──────────┘                                                    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Toast Container                           │ │
│  │  (Positioned fixed top-right for notifications)              │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                   Photo Editor Modal (Overlay)                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                         Header                                │ │
│  │  - Title: "Editor de Fotos"                                  │ │
│  │  - Close Button                                               │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                      Drawing Tools                            │ │
│  │  - Mode: Draw, Arrow, Text                                    │ │
│  │  - Actions: Undo, Clear                                       │ │
│  │  - Colors: Red, Blue, Green, Yellow, Black, White             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                                                                │ │
│  │                    Canvas Container                            │ │
│  │                    (Photo + Annotations)                       │ │
│  │                                                                │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                       Action Buttons                          │ │
│  │  - Cancel   - Save                                            │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Page Load
```
1. User requests /changeorder/create/
   ↓
2. Django view: changeorder_create_view()
   ↓
3. Renders: changeorder_form_clean.html
   ↓
4. Extends: base_modern.html
   ↓
5. Includes: header.html, sidebar.html
   ↓
6. JavaScript: kibray-core.js loads
   ↓
7. Kibray.PhotoGallery.init() if photos exist
```

### Photo Upload Flow
```
1. User clicks upload area
   ↓
2. File picker opens
   ↓
3. User selects images
   ↓
4. JavaScript validates files (size, type)
   ↓
5. FileReader creates DataURL previews
   ↓
6. renderPhotoPreview() displays thumbnails
   ↓
7. User can edit (opens modal) or delete
   ↓
8. Form submission uploads files to server
```

### Photo Editor Flow
```
1. User clicks "Edit" button
   ↓
2. openPhotoEditor() or openPhotoEditorNew()
   ↓
3. Modal opens with canvas and image
   ↓
4. User draws/annotates
   ↓
5. Annotations stored in currentAnnotations array
   ↓
6. User clicks "Save"
   ↓
7. saveAnnotations() sends to API
   ↓
8. Server saves annotations JSON
   ↓
9. Canvas exports annotated image
   ↓
10. Server saves annotated image file
    ↓
11. Thumbnail canvas updates
    ↓
12. Toast notification confirms success
```

### Existing Photo Delete Flow
```
1. User clicks delete button
   ↓
2. Kibray.PhotoGallery.handleDelete()
   ↓
3. Confirmation dialog
   ↓
4. Fetch API: POST /api/v1/changeorder-photo/{id}/delete/
   ↓
5. Server deletes photo from DB and storage
   ↓
6. Response: {success: true}
   ↓
7. Photo element removed from DOM
   ↓
8. Toast notification confirms deletion
```

---

## JavaScript Module Structure

```
window.Kibray
├── Toast
│   └── show(message, type, duration)
│       - Creates toast notification
│       - Auto-removes after duration
│       - Types: success, error, warning, info
│
├── PhotoGallery
│   ├── init()
│   │   - Attaches event listeners to .photo-edit-btn and .photo-delete-btn
│   │   - Initializes thumbnails
│   │
│   ├── handleEdit(event)
│   │   - Reads data-photo-id and data-image-url from button
│   │   - Calls window.openPhotoEditor()
│   │
│   ├── handleDelete(event)
│   │   - Reads data-photo-id from button
│   │   - Confirms deletion
│   │   - Calls window.deletePhoto()
│   │
│   ├── initThumbnails()
│   │   - Finds all [data-photo-id] elements
│   │   - Reads annotations from <script> tag
│   │   - Calls redrawThumbnail() for each
│   │
│   └── redrawThumbnail(photoId, annotations)
│       - Finds canvas element
│       - Draws annotations on canvas overlay
│       - Handles line, arrow, text types
│
└── Forms
    └── validateRequired(formId)
        - Checks all required fields
        - Adds red border to empty fields
        - Returns boolean
```

---

## Component Communication

### Parent → Child (Props)
```django
{% include "core/components/card.html" with 
    title="My Card"
    icon="box"
    class_extra="mt-4" %}
```

### Child → Parent (Blocks)
```django
{% include "core/components/card.html" with title="Projects" %}
    {% block content %}
        <p>This content comes from parent</p>
    {% endblock %}
{% include "core/components/card.html" with close_card=True only %}
```

### JavaScript Events
```javascript
// Event delegation pattern
document.addEventListener('DOMContentLoaded', function() {
    // Components attach listeners to parent
    document.querySelectorAll('.photo-edit-btn').forEach(btn => {
        btn.addEventListener('click', handler);
    });
});
```

### AJAX Communication
```javascript
// Form → Server
fetch('/api/v1/endpoint/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
})
.then(response => response.json())
.then(data => {
    // Server → UI
    Kibray.Toast.show('Success!', 'success');
});
```

---

## Styling Architecture

### Tailwind Utility Classes
```html
<!-- Instead of custom CSS classes -->
<div class="p-4 bg-white rounded-lg shadow-md">
    <h2 class="text-xl font-bold text-slate-900">Title</h2>
    <p class="text-sm text-slate-600 mt-2">Description</p>
</div>
```

### Component Variants
```html
<!-- Button variants -->
<button class="bg-indigo-600 ...">Primary</button>
<button class="bg-red-600 ...">Danger</button>
<button class="bg-green-600 ...">Success</button>
<button class="bg-slate-200 ...">Secondary</button>
```

### Responsive Design
```html
<!-- Mobile first, then breakpoints -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
    <!-- 1 column mobile, 2 tablet, 3 desktop -->
</div>
```

---

## State Management

### Form State
- **Django Form Object**: Server-side validation and rendering
- **JavaScript selectedFiles Array**: Client-side file management
- **Canvas currentAnnotations Array**: Drawing state

### Photo Editor State
```javascript
let currentPhotoId = null;      // Existing photo ID
let currentPhotoIndex = null;   // New photo index
let currentAnnotations = [];    // Current drawing
let drawingHistory = [];        // Undo stack
let isDrawing = false;          // Drawing in progress
let drawingMode = 'draw';       // draw|arrow|text
let drawingColor = '#dc2626';   // Current color
```

### UI State
- **Modal Visibility**: `hidden` class on modal
- **Active Tool**: `active` class on tool button
- **Selected Color**: `active` class on color swatch
- **Toast Visibility**: Auto-removed after timeout

---

## API Endpoints Used

### Photo Annotations
```
POST /api/v1/changeorder-photo/{id}/annotations/
Body: {"annotations": "[{...}]"}
Response: {"success": true}
```

### Annotated Image
```
POST /api/v1/changeorder-photo/{id}/annotated-image/
Body: {"image_data": "data:image/png;base64,..."}
Response: {"success": true}
```

### Photo Delete
```
POST /api/v1/changeorder-photo/{id}/delete/
Response: {"success": true}
```

### Approved Colors
```
GET /api/projects/{id}/approved-colors/
Response: {"colors": [{code, brand, name}, ...]}
```

---

## File Dependencies

### Template Dependencies
```
changeorder_form_clean.html
├── extends base_modern.html
│   ├── includes header.html
│   ├── includes sidebar.html (optional)
│   └── loads kibray-core.js
├── includes form_section.html (3x)
├── includes photo_grid.html (1x)
└── includes photo_editor_modal.html (1x)
```

### JavaScript Dependencies
```
kibray-core.js
├── Requires: No external dependencies
├── Expects: DOM elements with specific classes
│   - .photo-edit-btn with data-photo-id
│   - .photo-delete-btn with data-photo-id
│   - [data-photo-id] with .photo-annotations-data
│   - #toast-container for notifications
└── Provides: Global Kibray namespace
```

### CSS Dependencies
```
base_modern.html
├── Tailwind CSS (CDN)
├── Bootstrap Icons (CDN)
└── Custom styles (minimal, scoped to modal)
```

---

## Performance Considerations

### Event Delegation
✅ **Efficient**: One listener for all buttons
```javascript
document.querySelectorAll('.photo-edit-btn').forEach(...)
```

❌ **Inefficient**: Inline onclick on each button
```html
<button onclick="handler(id)">...</button>
```

### Canvas Rendering
✅ **Optimized**: Only redraw when needed
```javascript
function redrawAnnotations() {
    img.onload = () => {
        ctx.clearRect(...);
        ctx.drawImage(img, 0, 0);
        annotations.forEach(draw);
    };
}
```

### File Upload
✅ **Validated**: Size and type checks before upload
```javascript
if (file.size > 10 * 1024 * 1024) { skip; }
if (!file.type.startsWith('image/')) { skip; }
```

### AJAX Requests
✅ **Error Handling**: Try-catch and toast notifications
```javascript
fetch(...).catch(err => {
    console.error(err);
    Kibray.Toast.show('Error', 'error');
});
```

---

## Security Considerations

### CSRF Protection
```javascript
fetch('/api/...', {
    headers: {
        'X-CSRFToken': '{{ csrf_token }}'
    }
});
```

### File Validation
- Server-side file type validation
- Server-side file size validation
- Client-side pre-validation for UX

### Permission Checks
```django
{% if user.is_staff %}
    <!-- Staff-only content -->
{% endif %}
```

### XSS Prevention
- Django auto-escapes template variables
- Use `|safe` only for trusted content
- Sanitize user input before rendering

---

**Architecture Version**: 1.0  
**Last Updated**: November 2025  
**Status**: Production Ready
