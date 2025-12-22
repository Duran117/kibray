# Strategic Planner UX Improvements
**Date:** December 10, 2025  
**Status:** ✅ Complete

## Overview
Enhanced the Strategic Planner interface to provide contextual material request and assignment management directly within activity cards, improving workflow efficiency.

---

## 🎯 Implementation Details

### 1. **Material Request Button Inside Activities**

#### Before:
- Material request button was separate at the header level
- Employees had to remember which items needed materials
- No visual indication of which items had material requests

#### After:
```html
<!-- Inside each activity card -->
<button onclick="openMaterialRequestForItem('{{ item.id }}', '{{ item.title }}')" 
    class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
        {% if item.material_requirements.exists %}
            bg-orange-200 text-orange-800
        {% else %}
            bg-amber-100 text-amber-700
        {% endif %}">
    <i class="bi bi-box-seam mr-1"></i>
    {% if item.material_requirements.exists %}
        {{ item.material_requirements.count }}
    {% else %}
        Materials
    {% endif %}
</button>
```

**Features:**
- ✅ Button shows inside each activity card
- ✅ Displays count of materials already requested
- ✅ Changes color when materials exist (orange vs amber)
- ✅ Redirects to material request wizard with activity context
- ✅ Passes `strategic_item` and `item_name` parameters

---

### 2. **Visual Indicator: Orange Cards for Items with Materials**

#### Color System:
```css
/* No materials requested */
bg-white border-gray-200

/* Materials requested */
bg-orange-50 border-orange-300
```

**Card Appearance:**
- **Default (No Materials):** White background with gray text
- **With Materials:** Orange-tinted background with orange-tinted text
- **Badge Colors:** 
  - Amber (no materials): `bg-amber-100 text-amber-700`
  - Orange (has materials): `bg-orange-200 text-orange-800`

**Benefits:**
- Quick visual scan to see which activities have materials pending
- Employee can focus on activities without materials first
- Clear distinction between "needs attention" vs "already handled"

---

### 3. **Clickable Assignment Badges**

#### Before:
- Assignment badges were display-only
- No way to reassign from the board view
- Had to edit via separate form

#### After:
```html
<!-- Assigned employees -->
<button onclick="openReassignModal('{{ item.id }}', '{{ item.title }}')" 
    class="flex -space-x-1 hover:scale-110 transition-transform"
    title="Click to reassign">
    {% for emp in item.assigned_to.all %}
        <div class="h-5 w-5 rounded-full bg-kibray-100">
            {{ emp.first_name|first }}{{ emp.last_name|first }}
        </div>
    {% endfor %}
</button>

<!-- No assignment -->
<button onclick="openReassignModal('{{ item.id }}', '{{ item.title }}')" 
    class="bg-gray-100 hover:bg-kibray-100">
    <i class="bi bi-person-plus"></i> Assign
</button>
```

**Features:**
- ✅ Badge is clickeable button
- ✅ Hover effect (scale-110) indicates interactivity
- ✅ Opens reassignment modal with multi-select
- ✅ Pre-selects current assignments
- ✅ Updates via API (PATCH to `/api/v1/strategic/items/{id}/`)

---

### 4. **Reassignment Modal**

**New Modal Added:**
```html
<div id="reassignModal">
    <h3>Assign/Reassign: [Activity Name]</h3>
    <select id="reassignEmployees" multiple>
        {% for emp in employees %}
            <option value="{{ emp.id }}">{{ emp.name }}</option>
        {% endfor %}
    </select>
</div>
```

**JavaScript Functions:**
```javascript
function openReassignModal(itemId, itemName) {
    // Set item context
    // Pre-select current assignments
    // Show modal
}

function submitReassign() {
    // PATCH to /api/v1/strategic/items/{itemId}/
    // Update assigned_to field
    // Reload page
}
```

**Features:**
- ✅ Multi-select with Ctrl/Cmd support
- ✅ Shows current assignments pre-selected
- ✅ API integration with StrategicItem endpoint
- ✅ Validation and error handling

---

## 📊 User Workflow Improvements

### **Old Workflow:**
1. Employee views board
2. Clicks activity to see details
3. Navigates to separate materials page
4. Creates material request
5. Returns to board
6. ❌ Forgets context of which activity it was for
7. ❌ No visual indicator that materials were requested

### **New Workflow:**
1. Employee views board
2. Sees activity "paint the bunkbed"
3. Clicks **Materials** button inside activity card
4. ✅ Redirected to wizard with activity context pre-filled
5. Completes material request
6. Returns to board
7. ✅ Activity card is now **orange** - materials requested!
8. Moves to next white card (no materials yet)
9. If needs to reassign, clicks **JC badge** → reassign modal opens

---

## 🎨 Visual Design

### Activity Card States:

```
┌─────────────────────────────┐
│ paint the bunkbed     [✏️]  │ ← White (no materials)
├─────────────────────────────┤
│ 📍 lower level  [JC] [📦 Materials] │
│                              │
│ ✓ Prime surface              │
│ ✓ Apply first coat          │
└─────────────────────────────┘

┌─────────────────────────────┐
│ install cabinets      [✏️]  │ ← Orange (has materials)
├─────────────────────────────┤
│ 📍 kitchen  [MG] [📦 3]     │ ← Shows count
│                              │
│ ✓ Measure and mark          │
│ ✓ Mount upper cabinets      │
└─────────────────────────────┘
```

### Badge Color Coding:
- **Gray + Pin Icon:** Location area
- **Blue Circles:** Assigned employees (clickable)
- **Amber Badge:** No materials yet (clickable)
- **Orange Badge with Count:** Materials requested (clickable)

---

## 🔧 Technical Implementation

### Files Modified:
1. **`core/templates/core/strategic_planning_detail.html`**
   - Added material button inside activity cards (line ~110-125)
   - Added orange background logic based on `material_requirements.exists`
   - Added clickable assignment badges (line ~100-118)
   - Added reassignment modal (line ~350-395)
   - Added JavaScript functions for reassignment (line ~530-580)
   - Added `openMaterialRequestForItem()` redirect function

### Database Queries:
```python
# Check if item has materials
item.material_requirements.exists()

# Count materials
item.material_requirements.count()

# Get assigned employees
item.assigned_to.all()
```

### API Endpoints Used:
- **PATCH** `/api/v1/strategic/items/{id}/` - Update assignment
- **GET** `/projects/{id}/materials/request/new/?strategic_item={id}&item_name={name}` - Material request wizard

---

## ✅ Testing Checklist

- [ ] Activity card shows white background by default
- [ ] After adding materials via StrategicMaterialRequirement, card turns orange
- [ ] Material button shows count when materials exist
- [ ] Clicking material button redirects to wizard with context
- [ ] Assignment badges are clickable
- [ ] Reassignment modal opens with correct item name
- [ ] Current assignments are pre-selected in modal
- [ ] Reassignment saves successfully via API
- [ ] Unassigned items show "Assign" button instead of badges
- [ ] Mobile responsive - all buttons visible and clickable

---

## 🎯 Benefits

### For Employees:
1. **Contextual Actions:** Request materials without leaving activity context
2. **Visual Memory:** Orange cards = "I already handled materials for this"
3. **Quick Reassignment:** Click badge to change assignments on-the-fly
4. **Focus Mode:** Work through white cards (no materials) systematically

### For Project Managers:
1. **Visual Progress:** See at a glance which activities have materials covered
2. **Flexibility:** Easily reassign tasks as team composition changes
3. **Traceability:** Material requests linked to specific activities
4. **Efficiency:** Less context switching, fewer forgotten material requests

---

## 🚀 Future Enhancements

### Potential Additions:
1. **Material Status Badge:**
   ```html
   <span class="bg-green-100">
       Materials Approved
   </span>
   ```

2. **Inline Material List:**
   Show first 2-3 materials in card on hover

3. **Drag-and-Drop Reassignment:**
   Drag employee badge from one card to another

4. **Material Urgency Indicator:**
   Red dot if materials needed ASAP

5. **Completion Tracking:**
   Gray out card when all materials received

---

## 📸 Screenshots

### Before:
```
┌─────────────────────────────┐
│ [← Back] [📦 Request Materials] │ ← Header level, separate
└─────────────────────────────┘

┌─────────────────────────────┐
│ paint the bunkbed           │ ← White card, no indicator
│ 📍 lower level  JC          │ ← Static badge
└─────────────────────────────┘
```

### After:
```
┌─────────────────────────────┐
│ [← Back]                    │ ← Clean header
└─────────────────────────────┘

┌─────────────────────────────┐
│ paint the bunkbed           │ ← White (no materials)
│ 📍 lower level [JC↗] [📦 Materials] │ ← Buttons inside
└─────────────────────────────┘

┌─────────────────────────────┐
│ install cabinets            │ ← Orange (has materials)
│ 📍 kitchen [MG↗] [📦 3]     │ ← Count shown
└─────────────────────────────┘
```

---

## ✨ Summary

**Problem Solved:**
- Employees forgot to request materials because it was a separate action
- No visual indicator of which activities had materials pending
- Assignment changes required navigating away from board view

**Solution Delivered:**
1. ✅ Material button **inside each activity card**
2. ✅ **Orange background** for activities with materials
3. ✅ **Clickable badges** for quick reassignment
4. ✅ Context preservation via URL parameters
5. ✅ Visual workflow guidance (white → handle → orange)

**Result:**
- Faster material requests with better context
- Reduced forgotten materials
- Easier team management
- Better visual workflow tracking
