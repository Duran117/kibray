# Cost Codes Hierarchical Refactor Plan

## Current State

### Model Structure
```python
class CostCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=50, blank=True)  # labor, material, equipment
    active = models.BooleanField(default=True)
```

### Current Usage
CostCode is referenced in:
- `Expense.cost_code` (SET_NULL, optional)
- `TimeEntry.cost_code` (SET_NULL, optional)
- `ScheduleCategory.cost_code` (SET_NULL, optional)
- `ScheduleItem.cost_code` (SET_NULL, optional)
- `BudgetLine.cost_code` (PROTECT, required)
- `EstimateLine.cost_code` (PROTECT, required)
- `MaterialsRequest.cost_code` (SET_NULL, optional)
- `ClientRequest.suggested_cost_code` (SET_NULL, optional)

### Limitations
- Flat structure: no parent-child relationships
- No hierarchical roll-up of costs
- Manual aggregation required for category-level reporting
- Limited flexibility for nested divisions (e.g., "Labor > Painting > Interior")

---

## Proposed Hierarchical Schema

### Model Changes

#### Add to CostCode
```python
class CostCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=50, blank=True)
    active = models.BooleanField(default=True)
    
    # NEW FIELDS
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent cost code for hierarchical grouping"
    )
    level = models.PositiveSmallIntegerField(
        default=0,
        help_text="Hierarchy depth: 0=root, 1=child, 2=grandchild, etc."
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within siblings"
    )
    is_leaf = models.BooleanField(
        default=True,
        help_text="True if code can be assigned to transactions (no children)"
    )
    
    class Meta:
        ordering = ['sort_order', 'code']
        indexes = [
            models.Index(fields=['parent', 'sort_order']),
            models.Index(fields=['level']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-compute level based on parent chain
        if self.parent:
            self.level = self.parent.level + 1
            # Parent cannot be leaf if it has children
            if self.parent.is_leaf:
                self.parent.is_leaf = False
                self.parent.save(update_fields=['is_leaf'])
        else:
            self.level = 0
        super().save(*args, **kwargs)
    
    def get_ancestors(self):
        """Return list of ancestor codes from root to parent."""
        ancestors = []
        node = self.parent
        while node:
            ancestors.insert(0, node)
            node = node.parent
        return ancestors
    
    def get_descendants(self):
        """Return all descendant codes (recursive)."""
        descendants = list(self.children.all())
        for child in self.children.all():
            descendants.extend(child.get_descendants())
        return descendants
    
    def get_full_path(self):
        """Return code path: 'ROOT > CHILD > GRANDCHILD'"""
        ancestors = self.get_ancestors()
        return " > ".join([a.code for a in ancestors] + [self.code])
```

### Example Hierarchy

```
01 - Labor (is_leaf=False)
  ├── 01.10 - Painting (is_leaf=False)
  │   ├── 01.10.01 - Interior Painting (is_leaf=True)
  │   └── 01.10.02 - Exterior Painting (is_leaf=True)
  └── 01.20 - Carpentry (is_leaf=True)

02 - Materials (is_leaf=False)
  ├── 02.10 - Paint & Supplies (is_leaf=True)
  └── 02.20 - Wood & Lumber (is_leaf=True)

03 - Equipment (is_leaf=True)
```

**Business Rule**: Only leaf codes can be assigned to transactions (Expenses, TimeEntries, etc.).

---

## Migration Strategy

### Phase 1: Schema Addition (Non-Breaking)
```python
# Migration 00XX_costcode_hierarchy.py
operations = [
    migrations.AddField('CostCode', 'parent', ...),
    migrations.AddField('CostCode', 'level', ...),
    migrations.AddField('CostCode', 'sort_order', ...),
    migrations.AddField('CostCode', 'is_leaf', ...),
    migrations.AddIndex('CostCode', ['parent', 'sort_order']),
    migrations.AddIndex('CostCode', ['level']),
]
```

### Phase 2: Data Backfill
- All existing cost codes remain at `level=0`, `is_leaf=True`, `parent=None`.
- Admin or data migration script creates parent groups manually:
  - Create `01 - Labor` as parent
  - Update existing labor codes to set `parent=01`, recalculate level
  - Repeat for Material, Equipment categories

### Phase 3: Validation & Enforcement
```python
# In forms/serializers: validate only leaf codes can be assigned
class ExpenseForm(forms.ModelForm):
    def clean_cost_code(self):
        cc = self.cleaned_data.get('cost_code')
        if cc and not cc.is_leaf:
            raise ValidationError("Only leaf cost codes can be assigned to expenses.")
        return cc
```

### Phase 4: Roll-Up Queries
```python
def get_cost_summary(project, root_code=None):
    """
    Aggregate expenses/time by cost code hierarchy.
    If root_code provided, summarize only its descendants.
    """
    if root_code:
        codes = [root_code.id] + [d.id for d in root_code.get_descendants()]
    else:
        codes = CostCode.objects.filter(active=True).values_list('id', flat=True)
    
    expenses = Expense.objects.filter(project=project, cost_code_id__in=codes)
    time_entries = TimeEntry.objects.filter(project=project, cost_code_id__in=codes)
    
    # Group by parent and sum
    return {
        'total_expense': expenses.aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_labor': sum(te.labor_cost for te in time_entries),
    }
```

---

## Admin & UI Adjustments

### Admin Changes
- Use `django-mptt` or custom admin for tree display
- Add inline editing for children under parent code
- Enforce `is_leaf` validation on assignment

### Forms
- Filter dropdowns to show only leaf codes where required
- Display full path in dropdown labels: `"01.10.01 - Interior Painting (01 > 01.10 > 01.10.01)"`

### Reports
- Add hierarchical cost breakdown report showing parent → children totals
- Enable drill-down from summary to detail transactions

---

## Testing Plan

### Unit Tests
```python
def test_costcode_hierarchy_level_auto_compute():
    parent = CostCode.objects.create(code="01", name="Labor")
    child = CostCode.objects.create(code="01.10", name="Painting", parent=parent)
    assert child.level == 1
    assert parent.is_leaf is False

def test_get_descendants():
    parent = CostCode.objects.create(code="01", name="Labor")
    child1 = CostCode.objects.create(code="01.10", name="Painting", parent=parent)
    grandchild = CostCode.objects.create(code="01.10.01", name="Interior", parent=child1)
    assert len(parent.get_descendants()) == 2

def test_expense_only_leaf_codes():
    parent = CostCode.objects.create(code="01", name="Labor", is_leaf=False)
    expense = Expense(cost_code=parent, amount=100, ...)
    with pytest.raises(ValidationError):
        expense.full_clean()
```

### Integration Tests
- Verify budget roll-up across hierarchy
- Confirm filtering by parent includes all children
- Ensure existing flat codes remain functional

---

## Timeline & Effort

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Schema migration | 2 hours | None |
| Data backfill script | 3 hours | Schema complete |
| Form/admin updates | 4 hours | Schema complete |
| Validation logic | 2 hours | Form updates |
| Roll-up queries | 3 hours | Data populated |
| Tests | 4 hours | All phases |
| Documentation | 2 hours | All phases |
| **Total** | **20 hours** | Sequential |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing references | Keep `parent=None` default; existing codes remain functional |
| Performance on deep hierarchies | Add indexes on `parent`, `level`; cache ancestor paths |
| User confusion on leaf vs. parent | Clear UI labels; validation errors guide correct usage |
| Migration rollback complexity | Test migration on staging; document rollback SQL |

---

## Deliverables

1. ✅ Migration files (schema + data backfill)
2. ✅ Updated `CostCode` model with hierarchy methods
3. ✅ Form/serializer validation for leaf-only assignment
4. ✅ Admin interface with tree display
5. ✅ Hierarchical cost summary query functions
6. ✅ Unit + integration test suite
7. ✅ User documentation on hierarchy usage

---

## Next Steps

1. **Review & Approval**: Stakeholder sign-off on schema design
2. **Prototype Migration**: Test on copy of production data
3. **Implement Phase 1**: Schema migration + basic tests
4. **Backfill Data**: Manual or scripted parent assignment
5. **Deploy & Monitor**: Staged rollout with validation checks

---

**Document Version**: 1.0  
**Author**: AI Assistant  
**Date**: November 26, 2025
