from decimal import Decimal, InvalidOperation

from django import template
from django.utils import formats

register = template.Library()


@register.filter
def currency_es(value, places=2):
    """Formato monetario local con símbolo $ y separadores según L10N.
    Uso: {{ amount|currency_es }} -> $1,234.56 (en-US) / $1.234,56 (es-ES si configurado)
    """
    if value is None:
        return "$0.00"
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return value
    q_places = f"{{0:.{places}f}}".format(dec)
    # Usar utilidades de Django para localización si están disponibles
    try:
        localized = formats.number_format(dec, places, use_l10n=True)
    except Exception:
        localized = q_places
    return f"${localized}"


# Alias for compatibility
@register.filter
def currency(value, places=2):
    """Alias for currency_es filter."""
    return currency_es(value, places)


__all__ = ["currency_es", "currency"]
