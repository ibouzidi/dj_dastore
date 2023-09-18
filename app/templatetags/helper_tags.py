from django import template
from django.urls import resolve, reverse
from django.utils.translation import activate, get_language

register = template.Library()

@register.simple_tag(takes_context=True)
def change_lang(context, lang=None):
    path = context['request'].path
    url_parts = resolve(path)

    cur_language = get_language()
    try:
        activate(lang)
        url = reverse(url_parts.view_name, kwargs=url_parts.kwargs)
    finally:
        activate(cur_language)

    return url