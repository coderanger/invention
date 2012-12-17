from decimal import Decimal, InvalidOperation

from django import template
from django.template.defaultfilters import floatformat, special_floats
from django.utils.encoding import force_text

register = template.Library()

@register.filter(is_safe=True)
def percformat(text, arg=-1):
    try:
        input_val = force_text(text)
        d = Decimal(input_val)
    except UnicodeEncodeError:
        return ''
    except InvalidOperation:
        if input_val in special_floats:
            return input_val
        try:
            d = Decimal(force_text(float(text)))
        except (ValueError, InvalidOperation, TypeError, UnicodeEncodeError):
            return ''

    return floatformat(d*100, arg)
