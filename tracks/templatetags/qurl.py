# tracks/templatetags/qurl.py
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def qurl(context, **kwargs):
    """
    Будує query-string, зберігаючи поточні параметри,
    та замінюючи/видаляючи передані kwargs.
    Приклад: {% qurl page=3 %} -> "?genre=pop&page=3"
    """
    request = context["request"]
    params = request.GET.copy()
    for k, v in kwargs.items():
        if v is None:
            params.pop(k, None)
        else:
            params[k] = v
    s = params.urlencode()
    return f"?{s}" if s else ""
