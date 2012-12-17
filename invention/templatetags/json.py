from django import template
from django.utils.safestring import mark_safe

from invention.utils import json

register = template.Library()

@register.filter(is_safe=True)
def jsonify(obj):
    return mark_safe(json.dumps(obj))
