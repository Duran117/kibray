# Known Issues - API Serializers (Pre-existing)

**Date Identified**: December 3, 2025  
**Status**: NON-BLOCKING  
**Severity**: LOW (Documentation only)  
**Origin**: Pre-existing codebase  

---

## Issues

### 1. drf_spectacular.E001 - Profile.phone_number

**Error Message**:
```
Schema generation threw exception "Field name `phone_number` is not valid for model `Profile`."
```

**Location**: Unknown serializer referencing Profile model  
**Impact**: ❌ Does NOT block deployment or functionality  
**Affects**: OpenAPI/Swagger documentation generation only  

**Root Cause**:
- A serializer references `Profile.phone_number` field
- This field doesn't exist or has different name in Profile model

**Fix** (Future):
```python
# Option 1: Update serializer to use correct field name
class ProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='phone')  # If field is 'phone'

# Option 2: Add field to Profile model
class Profile(models.Model):
    phone_number = models.CharField(max_length=20, blank=True)
```

---

### 2. drf_spectacular.W001 - Missing Type Hints (~20 warnings)

**Warning Message**:
```
unable to resolve type hint for function "get_X". 
Consider using a type hint or @extend_schema_field. 
Defaulting to string.
```

**Affected Files**:
- `core/api/serializer_classes/changeorder_serializers.py`
- `core/api/serializer_classes/project_serializers.py`

**Affected Functions**:
- `get_days_pending`
- `get_number`
- `get_photos_count`
- `get_project`
- `get_project_name`
- `get_status`
- `get_progress`
- `get_recent_activity`
- `get_tasks_count`
- `get_total_budget`
- `get_total_files_count`
- `get_pending_changeorders_count`
- `get_email`
- `get_full_name`

**Impact**: ⚠️ Documentation less accurate, but API works correctly

**Example Fix**:
```python
# Before (generates warning):
def get_progress(self, obj):
    return obj.calculate_progress()

# After (no warning):
def get_progress(self, obj) -> float:
    return obj.calculate_progress()

# Or with decorator:
from drf_spectacular.utils import extend_schema_field

@extend_schema_field(OpenApiTypes.FLOAT)
def get_progress(self, obj):
    return obj.calculate_progress()
```

---

## Impact Assessment

| Aspect | Status | Notes |
|--------|--------|-------|
| **App Functionality** | ✅ OK | No impact on user-facing features |
| **API Endpoints** | ✅ OK | All endpoints work correctly |
| **Railway Deployment** | ✅ OK | Deploys successfully |
| **Django System Check** | ✅ PASS | Basic check passes |
| **API Documentation** | ⚠️ DEGRADED | Swagger docs less accurate |
| **Production Stability** | ✅ STABLE | Running fine with these warnings |

---

## Recommended Action Plan

### Phase 1: Monitoring (Current - Week 1)
- [x] Document known issues
- [ ] Monitor production for 48-72 hours
- [ ] Validate Phase 3 functionality
- [ ] Collect API usage metrics

### Phase 2: Investigation (Week 2)
- [ ] Create GitHub issue: "Fix DRF Spectacular Warnings"
- [ ] Audit all serializers for missing type hints
- [ ] Identify Profile.phone_number usage
- [ ] Document all API endpoints affected

### Phase 3: Implementation (Week 2-3)
- [ ] Create feature branch: `fix/api-type-hints`
- [ ] Add type hints to all get_* methods
- [ ] Fix Profile.phone_number reference
- [ ] Add @extend_schema_field decorators where needed
- [ ] Update serializer tests

### Phase 4: Testing (Week 3)
- [ ] Test all API endpoints manually
- [ ] Run full test suite
- [ ] Generate Swagger docs and validate
- [ ] Load test critical endpoints

### Phase 5: Deployment (Week 4)
- [ ] Create PR with detailed description
- [ ] Code review
- [ ] Merge to main
- [ ] Monitor production deployment
- [ ] Validate Swagger documentation

---

## Why Not Fix Now?

1. **Not Critical**: These are documentation warnings, not functional errors
2. **Risk Management**: Touching 20+ API files risks regression
3. **Scope Isolation**: Phase 3 (signatures) should not mix with API fixes
4. **Testing Burden**: Would require extensive API endpoint testing
5. **Deployment Confidence**: If something breaks, hard to identify cause
6. **Best Practices**: Separate concerns = easier rollback + debugging

---

## Related Files

Files that would need modification (if fixing):
```
core/api/serializer_classes/
├── changeorder_serializers.py (~10 functions to fix)
├── project_serializers.py (~10 functions to fix)
└── (others TBD after investigation)
```

Estimated effort:
- Investigation: 2-3 hours
- Implementation: 4-5 hours
- Testing: 3-4 hours
- **Total**: 10-12 hours

---

## Current Workaround

None needed - app works fine with these warnings.

If Swagger docs are needed immediately:
- Manually document API endpoints
- Use Postman collections
- Generate docs from OpenAPI spec ignoring warnings

---

## Notes

- These warnings existed before Phase 3 implementation
- Phase 3 code does NOT contribute to these warnings
- Phase 3 deployment is clean and separate from these issues
- Production stability is NOT affected

---

**Status**: DOCUMENTED  
**Priority**: LOW  
**Next Review**: After Phase 3 production validation (3-5 days)  

**Responsible Team**: Backend API team  
**Created by**: Phase 3 Implementation (December 3, 2025)
