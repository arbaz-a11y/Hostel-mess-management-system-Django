from __future__ import annotations

from django import template

register = template.Library()


@register.filter
def getattr_safe(obj, attr_name: str):
    """
    Template helper: {{ obj|getattr_safe:"field_name" }}
    """

    if obj is None:
        return ""
    return getattr(obj, attr_name, "")

