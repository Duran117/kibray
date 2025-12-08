# Change Order - Photo & Color Management Guide

## 🎨 Overview

This guide documents the new color selection and photo management features added to the Change Order system.

## ✅ Features Implemented

### 1. **Color Selection**
- **HTML5 Color Picker**: Visual color selector in forms
- **Color Preview**: Live preview of selected color
- **Hex Input**: Manual entry of color codes (e.g., #FF5733)
- **Reference Code**: Field for paint brand/color codes (e.g., "SW 7006", "Benjamin Moore 2024-10")
- **Color Display**: Color swatch shown in detail view

### 2. **Photo Upload**
- **Multiple Photos**: Upload multiple images per Change Order
- **Drag & Drop Area**: User-friendly upload interface
- **Photo Descriptions**: Add captions to each photo
- **Photo Gallery**: Grid display in detail view
- **Photo Ordering**: Manual sort order for photos

### 3. **Photo Annotations (Drawing Tool)**
- **Canvas Editor**: HTML5 Canvas-based drawing interface
- **Drawing Tools**:
  - ✏️ Freehand drawing (pen)
  - 📏 Straight lines
  - ➡️ Arrows
  - ⭕ Circles
  - ⬜ Rectangles
  - 🔤 Text (planned)
- **Tool Options**:
  - Color picker for drawings
  - Line width adjustment (1-10px)
  - Undo functionality
  - Clear canvas
- **Annotation Storage**: Saved as JSON in database
- **Annotation Display**: Rendered on photos in detail view

### 4. **Fullscreen Photo Viewer**
- Click any photo to view full size
- Annotations rendered on fullscreen view
- ESC key to close
- Mobile responsive

## 📁 Files Modified/Created

### Models (`core/models.py`)
```python
# ChangeOrder model additions:
- color (CharField): Hex color code (#RRGGBB)
- reference_code (CharField): Paint/material reference code

# New ChangeOrderPhoto model:
- change_order (ForeignKey)
- image (ImageField): Photo file
- description (CharField): Photo caption
- annotations (TextField): JSON drawing data
- uploaded_at (DateTimeField)
- order (IntegerField): Display order
```

### Forms (`core/forms.py`)
```python
# Updated ChangeOrderForm:
- Added color field with HTML5 color input widget
- Added reference_code field

# New ChangeOrderPhotoForm:
- For photo upload and management
```

### Views (`core/views.py`)
```python
# Updated changeorder_create_view:
- Handles FILE upload (request.FILES)
- Creates ChangeOrderPhoto instances
- Saves photo descriptions

# Updated changeorder_edit_view:
- Handles new and existing photos
- Maintains photo order

# New save_photo_annotations:
- AJAX endpoint for saving drawing annotations
- Updates ChangeOrderPhoto.annotations field

# New delete_changeorder_photo:
- AJAX endpoint for photo deletion
```

### Templates

#### `changeorder_form_standalone.html` (NEW)
- Standalone HTML5 document
- Same professional design as detail view
- Sections:
  1. Basic Information (project, description, amount, status, notes)
  2. Color Selection (color picker + reference code)
  3. Photo Upload (drag-drop area + preview grid)
- Photo Editor Modal:
  - Canvas drawing interface
  - Tool palette
  - Save/cancel buttons
- JavaScript:
  - File preview rendering
  - Canvas drawing logic
  - Annotation save/load
  - Photo deletion

#### `changeorder_detail_standalone.html` (UPDATED)
- Added Color Information section:
  - Color swatch display
  - Reference code
- Added Photo Gallery section:
  - Responsive grid layout
  - Photo captions
  - Annotation badges
- Added Fullscreen Photo Modal:
  - Canvas rendering
  - Annotation overlay
  - Close on ESC or click outside

### URLs (`kibray_backend/urls.py`)
```python
# Added:
path("changeorder/photo/<int:photo_id>/annotations/", 
     views.save_photo_annotations, name="save_photo_annotations")
path("changeorder/photo/<int:photo_id>/delete/", 
     views.delete_changeorder_photo, name="delete_changeorder_photo")
```

### Migration
```
core/migrations/0063_changeorder_color_changeorder_reference_code_and_more.py
- Add field color to changeorder
- Add field reference_code to changeorder
- Create model ChangeOrderPhoto
```

## 🎯 User Workflows

### Creating a Change Order with Color & Photos

1. Navigate to Change Order Board
2. Click "Create Change Order"
3. Fill basic information (project, description, amount, etc.)
4. **Select Color**:
   - Click color picker to choose visually
   - OR type hex code manually (e.g., #FF5733)
   - Enter reference code (e.g., "Sherwin Williams 7006")
5. **Upload Photos**:
   - Click upload area or drag files
   - Add descriptions to each photo
   - Click "Edit" on any photo to add drawings
6. **Draw Annotations** (optional):
   - Select drawing tool (pen, line, arrow, circle, etc.)
   - Choose color for drawings
   - Adjust line width
   - Draw on photo
   - Click "Save Annotations"
7. Submit form

### Editing Photos on Existing Change Order

1. Open Change Order detail view
2. Click "Edit" button
3. Existing photos shown at top
4. Click "Edit" on any photo to modify annotations
5. Click "Delete" to remove photos
6. Add new photos using upload area
7. Save changes

### Viewing Photos

1. Open Change Order detail view
2. Scroll to "Photos" section
3. Click any photo thumbnail
4. Photo opens in fullscreen with annotations
5. ESC to close or click outside

## 🎨 Design System

### Colors
- **Primary Purple**: `#667eea` (buttons, icons, highlights)
- **Success Green**: `#059669` (amounts, success states)
- **Background**: `#f8fafc` (page background)
- **Card White**: `#ffffff` (main container)
- **Text Dark**: `#1e293b` (primary text)
- **Text Muted**: `#64748b` (secondary text)
- **Border**: `#e2e8f0` (dividers, inputs)

### Typography
- **System Font Stack**: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Headings**: 600-700 font-weight
- **Body**: 1rem (16px) with 1.6 line-height

### Layout
- **Max Width**: 900px (centered)
- **Border Radius**: 8-12px
- **Grid Gap**: 1-1.5rem
- **Padding**: 0.75-2.5rem (contextual)

## 🔧 Technical Details

### Photo Storage
- **Path**: `MEDIA_ROOT/changeorders/photos/`
- **Format**: Any image format (JPG, PNG, HEIC, etc.)
- **Field**: `ImageField` with Pillow library

### Annotation Format (JSON)
```json
[
  {
    "type": "line",
    "color": "#FF0000",
    "width": 3,
    "x1": 100,
    "y1": 200,
    "x2": 300,
    "y2": 400
  },
  {
    "type": "arrow",
    "color": "#00FF00",
    "width": 5,
    "x1": 150,
    "y1": 150,
    "x2": 500,
    "y2": 500
  },
  {
    "type": "circle",
    "color": "#0000FF",
    "width": 3,
    "x1": 400,
    "y1": 300,
    "x2": 500,
    "y2": 400
  }
]
```

### Canvas Drawing
- **Library**: Vanilla HTML5 Canvas API
- **Coordinate System**: Image pixels (stored at original resolution)
- **Rendering**: Server-side storage, client-side rendering
- **History**: Undo stack maintained during editing session

### AJAX Endpoints

#### Save Annotations
```javascript
POST /changeorder/photo/<photo_id>/annotations/
Content-Type: application/json

{
  "annotations": "[{...annotation objects...}]"
}

Response: { "success": true }
```

#### Delete Photo
```javascript
POST /changeorder/photo/<photo_id>/delete/
X-CSRFToken: <token>

Response: { "success": true }
```

## 📱 Mobile Responsive

- Photo gallery: Single column on mobile
- Drawing tools: Wrap on small screens
- Canvas: Scales to fit viewport
- Touch support: Works with touch events for drawing

## 🔒 Security

- `@login_required` on all views
- CSRF protection on POST requests
- File upload validation (image types only)
- Foreign key constraints prevent orphaned records

## 🚀 Future Enhancements

### Potential Features
1. **Text Tool**: Add text annotations to photos
2. **Color Palette**: Dropdown of pre-approved company colors
3. **Photo Rotation**: Rotate images before saving
4. **Photo Crop**: Crop/resize images
5. **Batch Photo Upload**: Drag-drop multiple at once
6. **Photo Comparison**: Before/after slider
7. **PDF Export**: Include photos in PDF output
8. **Mobile App**: Native camera integration

### Performance Optimizations
1. **Image Thumbnails**: Generate thumbnails for gallery view
2. **Lazy Loading**: Load photos on scroll
3. **CDN Storage**: Move images to cloud storage (S3, etc.)
4. **Image Compression**: Optimize file sizes on upload

## 📊 Database Schema

```sql
-- Change Order table additions
ALTER TABLE core_changeorder 
ADD COLUMN color VARCHAR(7),
ADD COLUMN reference_code VARCHAR(50);

-- New ChangeOrderPhoto table
CREATE TABLE core_changeorderphoto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_order_id INTEGER REFERENCES core_changeorder(id),
    image VARCHAR(100),
    description VARCHAR(255),
    annotations TEXT,
    uploaded_at DATETIME,
    order INTEGER DEFAULT 0
);

CREATE INDEX idx_co_photos ON core_changeorderphoto(change_order_id);
```

## 🧪 Testing

### Manual Testing Checklist

**Color Selection**:
- [ ] Color picker opens and selects colors
- [ ] Manual hex input accepts valid codes
- [ ] Color preview updates in real-time
- [ ] Reference code saves correctly
- [ ] Color displays in detail view

**Photo Upload**:
- [ ] Single photo upload works
- [ ] Multiple photo upload works
- [ ] Photo descriptions save
- [ ] Photos display in grid
- [ ] Photo order maintained

**Drawing Tool**:
- [ ] All tools work (pen, line, arrow, circle, rect)
- [ ] Color picker changes drawing color
- [ ] Line width adjustment works
- [ ] Undo removes last annotation
- [ ] Clear removes all annotations
- [ ] Annotations save to database
- [ ] Annotations render in detail view

**Fullscreen Viewer**:
- [ ] Photo opens on click
- [ ] Annotations render correctly
- [ ] ESC closes modal
- [ ] Click outside closes modal
- [ ] Mobile pinch-zoom works

**Edge Cases**:
- [ ] Form validates without photos
- [ ] Form validates without color
- [ ] Edit view loads existing photos
- [ ] Photo deletion works
- [ ] Large image handling
- [ ] Invalid file type rejection

## 📝 Notes

- Template inheritance avoided by using standalone HTML
- All JavaScript vanilla (no jQuery dependency)
- CSS Grid for responsive layouts
- Canvas API for maximum compatibility
- JSON storage allows flexible annotation types

## 🆘 Troubleshooting

### Issue: Styles not applying
- **Cause**: Using base template inheritance
- **Solution**: Templates are standalone, don't extend base.html

### Issue: Photos not uploading
- **Cause**: Missing `request.FILES` or `enctype="multipart/form-data"`
- **Solution**: Verify form has `enctype` and view uses `request.FILES`

### Issue: Annotations not saving
- **Cause**: CSRF token missing or JSON parse error
- **Solution**: Check CSRF token in AJAX headers, validate JSON format

### Issue: Canvas not drawing
- **Cause**: Image not loaded before canvas setup
- **Solution**: Wait for `img.onload` before drawing

## 📚 Resources

- [HTML5 Canvas API](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API)
- [Django ImageField](https://docs.djangoproject.com/en/4.2/ref/models/fields/#imagefield)
- [HTML Color Input](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/color)
- [CSS Grid Layout](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Grid_Layout)

---

**Created**: November 14, 2025  
**Version**: 1.0  
**Author**: Kibray Development Team
