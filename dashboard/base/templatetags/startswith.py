# base/templatetags/startswith.py
from django import template
register = template.Library()

@register.filter
def startswith(text, prefix):
    try:
        return str(text).startswith(str(prefix))
    except Exception:
        return False
