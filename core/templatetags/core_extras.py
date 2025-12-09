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
def div(value, arg):
    """Divide el valor por el argumento"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def filter_by_status(queryset, status):
    """Filtra un queryset por status"""
    try:
        return queryset.filter(status=status)
    except AttributeError:
        # Si no es un queryset, filtra una lista
        return [obj for obj in queryset if getattr(obj, "status", None) == status]


@register.filter
def filter_by_id(queryset, obj_id):
    """Get object by ID from queryset"""
    try:
        return queryset.get(id=int(obj_id))
    except (ValueError, TypeError, AttributeError):
        return None


@register.filter
def abs_value(value):
    """Return absolute value"""
    try:
        return abs(int(value))
    except (ValueError, TypeError):
        return value


@register.filter
def sum_attr(queryset, attr_name):
    """Sum an attribute across a queryset or list"""
    try:
        return sum(getattr(obj, attr_name, 0) for obj in queryset)
    except (TypeError, AttributeError):
        return 0


@register.filter
def class_name(value):
    """Return the class name of a Python object.

    Useful in templates to avoid accessing dunder attributes like __class__ directly,
    which Django templates disallow. Example usage:
        {{ field.field.widget|class_name|lower }}
    """
    try:
        return value.__class__.__name__
    except Exception:
        return ""


@register.filter
def getattribute(obj, attr_name):
    """Get attribute from object, handling nested attributes with __"""
    try:
        # Handle nested attributes like 'user__username'
        if "__" in attr_name:
            parts = attr_name.split("__")
            value = obj
            for part in parts:
                value = getattr(value, part, None)
                if value is None:
                    return None
            return value
        else:
            return getattr(obj, attr_name, None)
    except (AttributeError, TypeError):
        return None
