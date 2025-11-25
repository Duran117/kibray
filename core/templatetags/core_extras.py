from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "")

@register.filter
def mul(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def filter_by_status(queryset, status):
    """Filtra un queryset por status"""
    try:
        return queryset.filter(status=status)
    except AttributeError:
        # Si no es un queryset, filtra una lista
        return [obj for obj in queryset if getattr(obj, 'status', None) == status]

@register.filter
def filter_by_id(queryset, obj_id):
    """Get object by ID from queryset"""
    try:
        return queryset.get(id=int(obj_id))
    except (ValueError, TypeError, AttributeError):
        return None
