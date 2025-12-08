# Screen Migration Checklist

Use this checklist when migrating a screen to the Design System.

---

## Pre-Migration

### 1. Analyze Current Screen
- [ ] Identify template file location
- [ ] List all form fields and inputs
- [ ] Document business logic (validations, permissions)
- [ ] Note any JavaScript functionality
- [ ] List API endpoints used
- [ ] Screenshot current design for reference

### 2. Plan Component Usage
- [ ] Map sections to `form_section` components
- [ ] Identify where to use `card` components
- [ ] Plan `button` variants needed
- [ ] Determine if `photo_grid` is needed
- [ ] Check for reusable patterns from other screens

### 3. Backup
- [ ] Create backup: `{template}_legacy.html`
- [ ] Document view logic in comments
- [ ] Note any hardcoded URLs or paths

---

## Migration Steps

### 1. Create New Template

**File**: `core/templates/core/{screen}_clean.html`

```django
{% extends "core/base_modern.html" %}
{% load static %}
{% load i18n %}

{% block title %}{Screen Name} - Kibray{% endblock %}

{% block page_header %}
<div class="flex items-center justify-between">
    <div class="flex items-center gap-4">
        <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-lg">
            <i class="bi bi-{icon} text-2xl"></i>
        </div>
        <div>
            <h1 class="text-2xl font-bold text-slate-900">{Screen Title}</h1>
            <p class="text-sm text-slate-600 mt-1">{Screen Description}</p>
        </div>
    </div>
    
    <!-- Action buttons -->
</div>
{% endblock %}

{% block content %}
    <!-- Your content here -->
{% endblock %}

{% block extra_js %}
<script src="{% static 'core/js/kibray-core.js' %}"></script>
<script>
    // Screen-specific JavaScript
</script>
{% endblock %}
```

- [ ] Template created
- [ ] Extended `base_modern.html`
- [ ] Added `page_header` block
- [ ] Added `content` block
- [ ] Loaded `kibray-core.js` if needed

---

### 2. Migrate HTML Structure

#### Replace Custom Forms
**Before**:
```html
<div class="form-section">
    <h3>Section Title</h3>
    <!-- fields -->
</div>
```

**After**:
```django
{% include "core/components/form_section.html" with icon="info-circle" title=_("Section Title") %}
    <!-- fields -->
{% include "core/components/form_section.html" with close_section=True only %}
```

- [ ] All form sections migrated
- [ ] Icons selected for each section
- [ ] Titles translated with {% trans %}

#### Replace Custom Cards
**Before**:
```html
<div class="card">
    <div class="card-header">Title</div>
    <div class="card-body">Content</div>
</div>
```

**After**:
```django
{% include "core/components/card.html" with title="Title" icon="box" %}
    Content
{% include "core/components/card.html" with close_card=True only %}
```

- [ ] All cards migrated
- [ ] Titles and icons set
- [ ] Optional header actions added

#### Replace Custom Buttons
**Before**:
```html
<button class="btn btn-primary">Save</button>
<a href="#" class="btn btn-danger">Delete</a>
```

**After**:
```django
{% include "core/components/button.html" with text=_("Save") variant="primary" icon="check-circle" %}
{% include "core/components/button.html" with text=_("Delete") variant="danger" icon="trash" href="#" %}
```

- [ ] All buttons migrated
- [ ] Variants selected (primary, secondary, danger, success)
- [ ] Icons added where appropriate

#### Replace Photo Galleries
**Before**:
```html
<div class="photos">
    {% for photo in photos %}
        <div><img src="{{ photo.image.url }}"></div>
    {% endfor %}
</div>
```

**After**:
```django
{% include "core/components/photo_grid.html" with photos=photos is_existing=True %}
```

- [ ] Photo grid component used
- [ ] `is_existing` flag set correctly
- [ ] Photo editor modal included if needed

---

### 3. Migrate Styles

#### Remove Custom CSS
- [ ] Delete `<style>` blocks in template
- [ ] Remove custom CSS classes
- [ ] Replace with Tailwind utilities

#### Common Replacements
```
Old Class                 → New Tailwind Classes
.container                → max-w-7xl mx-auto px-4
.row                      → grid grid-cols-{n} gap-4
.col-md-6                 → md:col-span-6
.card                     → bg-white rounded-lg shadow-md p-6
.form-control             → w-full px-4 py-2.5 border border-slate-300 rounded-lg
.btn-primary              → bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg
.text-center              → text-center
.mt-4                     → mt-4
.d-flex                   → flex
.justify-content-between  → justify-between
.align-items-center       → items-center
```

- [ ] All custom CSS removed
- [ ] Tailwind utilities applied
- [ ] Responsive classes added (sm:, md:, lg:)

---

### 4. Migrate JavaScript

#### Remove Inline Handlers
**Before**:
```html
<button onclick="deleteItem({{ item.id }})">Delete</button>
```

**After**:
```html
<button class="delete-item-btn" data-item-id="{{ item.id }}">Delete</button>

<script>
document.querySelectorAll('.delete-item-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const itemId = this.dataset.itemId;
        deleteItem(itemId);
    });
});
</script>
```

- [ ] All inline onclick removed
- [ ] Event delegation implemented
- [ ] Data attributes used for IDs

#### Use Kibray Utilities
**Before**:
```javascript
alert('Success!');
```

**After**:
```javascript
Kibray.Toast.show('Success!', 'success');
```

- [ ] Toast notifications for feedback
- [ ] Form validation with Kibray.Forms if needed
- [ ] Photo gallery with Kibray.PhotoGallery if needed

#### Modularize Code
- [ ] Move repeated code to functions
- [ ] Use `const` and `let` instead of `var`
- [ ] Add error handling (try-catch)
- [ ] Add console.log for debugging

---

### 5. Add Internationalization

#### Template Strings
**Before**:
```html
<h1>Create Project</h1>
<button>Save</button>
<p>Please fill all fields</p>
```

**After**:
```django
<h1>{% trans "Create Project" %}</h1>
<button>{% trans "Save" %}</button>
<p>{% trans "Please fill all fields" %}</p>
```

- [ ] All user-facing text wrapped in {% trans %}
- [ ] Placeholder text translated
- [ ] Button labels translated
- [ ] Error messages translated

#### JavaScript Strings
**Before**:
```javascript
alert('Are you sure?');
```

**After**:
```javascript
if (confirm('{% trans "Are you sure?" %}')) {
    // ...
}
```

- [ ] All JavaScript strings translated
- [ ] Toast messages translated
- [ ] Prompt/confirm dialogs translated

---

### 6. Update View

#### Template Selection Logic
**Before**:
```python
return render(request, 'core/screen.html', context)
```

**After**:
```python
# Use clean Design System template by default
# Legacy template available via ?legacy=true
use_legacy = request.GET.get('legacy', 'false').lower() == 'true'
template = 'core/screen_legacy.html' if use_legacy else 'core/screen_clean.html'

return render(request, template, context)
```

- [ ] View updated to use new template
- [ ] Legacy template option added
- [ ] Context variables unchanged

---

### 7. Test Functionality

#### Visual Testing
- [ ] Desktop layout (>1024px)
- [ ] Tablet layout (768-1024px)
- [ ] Mobile layout (<768px)
- [ ] All sections render correctly
- [ ] Components look correct
- [ ] No CSS conflicts or layout breaks

#### Form Testing
- [ ] All fields display correctly
- [ ] Form validation works
- [ ] Required fields marked
- [ ] Error messages display
- [ ] Success messages display
- [ ] Form submission works

#### Interactive Testing
- [ ] All buttons work
- [ ] All links work
- [ ] Modals open/close
- [ ] AJAX requests work
- [ ] File uploads work (if applicable)
- [ ] Photo editor works (if applicable)

#### Permission Testing
- [ ] Staff-only features hidden for non-staff
- [ ] User-specific content displays correctly
- [ ] Unauthorized access redirects properly

#### Language Testing
- [ ] Switch to Spanish - all text translates
- [ ] Switch to English - all text translates
- [ ] Form labels translate
- [ ] Button text translates
- [ ] Toast notifications translate

#### Browser Testing
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

---

### 8. Performance Check

#### Load Time
- [ ] Page loads in <2 seconds
- [ ] No unnecessary network requests
- [ ] Images optimized
- [ ] CSS/JS not blocking render

#### Runtime Performance
- [ ] No JavaScript errors in console
- [ ] No layout thrashing
- [ ] Smooth animations
- [ ] Fast interactions

---

### 9. Accessibility Check

#### Keyboard Navigation
- [ ] All interactive elements reachable via Tab
- [ ] Tab order makes sense
- [ ] Enter/Space activates buttons
- [ ] ESC closes modals

#### Screen Reader
- [ ] Headings use proper hierarchy (h1, h2, h3)
- [ ] Images have alt text
- [ ] Buttons have descriptive labels
- [ ] Form fields have labels
- [ ] ARIA labels where needed

#### Color Contrast
- [ ] Text readable on backgrounds
- [ ] Links distinguishable
- [ ] Focus indicators visible

---

### 10. Documentation

#### Code Comments
- [ ] Complex logic explained
- [ ] TODO comments for future work
- [ ] Deprecation notices for old code

#### Update Docs
- [ ] Add screen to migration list
- [ ] Document any new patterns used
- [ ] Update component usage guide if needed

---

## Post-Migration

### 1. Deploy
- [ ] Commit changes to Git
- [ ] Create pull request
- [ ] Code review
- [ ] Deploy to staging
- [ ] QA testing
- [ ] Deploy to production

### 2. Monitor
- [ ] Check error logs for 24 hours
- [ ] Monitor user feedback
- [ ] Watch analytics for usage drops
- [ ] Fix any reported bugs

### 3. Cleanup
- [ ] Remove legacy template after 1-2 weeks
- [ ] Remove `?legacy=true` logic from view
- [ ] Update any documentation references
- [ ] Archive screenshots and notes

---

## Common Issues & Solutions

### Issue: Layout Breaks on Mobile
**Solution**: 
- Use responsive Tailwind classes
- Test with browser dev tools mobile view
- Use `flex-col` on mobile, `flex-row` on desktop

### Issue: JavaScript Not Working
**Solution**:
- Check console for errors
- Verify `kibray-core.js` is loaded
- Ensure event listeners added after DOM ready
- Use `data-` attributes correctly

### Issue: Styles Not Applying
**Solution**:
- Check for typos in Tailwind classes
- Verify no custom CSS overriding
- Use browser inspector to debug
- Check Tailwind CDN is loading

### Issue: Form Submission Fails
**Solution**:
- Check CSRF token present
- Verify form method is POST
- Check field names match Django form
- Verify no JavaScript preventing submit

### Issue: Photos Not Uploading
**Solution**:
- Check file input has `multiple` attribute
- Verify `enctype="multipart/form-data"` on form
- Check file size validation
- Verify server storage configured

---

## Estimated Time

- **Simple screen** (basic form): 2-3 hours
- **Medium screen** (form + photos): 4-6 hours
- **Complex screen** (multiple sections, tables, etc): 8-12 hours

---

## Next Screens to Migrate

### Priority 1 (High Traffic)
1. [ ] Dashboard
2. [ ] Project Detail
3. [ ] Project List

### Priority 2 (Complex)
4. [ ] Financial screens
5. [ ] Time Entry
6. [ ] Schedule view

### Priority 3 (Low Traffic)
7. [ ] User profile
8. [ ] Settings pages
9. [ ] Admin pages

---

**Use this checklist for every screen migration to ensure consistency and quality.**

**Last Updated**: November 2025  
**Version**: 1.0
