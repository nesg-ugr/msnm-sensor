from django import template
from pyparsing import basestring

register = template.Library()


@register.filter('startswith')
def startswith(text, starts):
    if isinstance(text, basestring):
        return text.startswith(starts)
    return False