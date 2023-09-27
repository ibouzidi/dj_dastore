from django import template
from django.urls import resolve, reverse
from django.utils.translation import activate, get_language

register = template.Library()

@register.simple_tag(takes_context=True)
def change_lang(context, lang=None):
    path = context['request'].path
    url_parts = resolve(path)

    cur_language = get_language()

    # Get view name and kwargs to generate URL later
    view_name = url_parts.view_name
    kwargs = url_parts.kwargs

    # Switch to the desired language
    try:
        activate(lang)
        url = reverse(view_name, kwargs=kwargs)
    finally:
        activate(cur_language)  # revert back to the original language

    # Include the server scheme and host
    scheme = context['request'].scheme
    host = context['request'].META['HTTP_HOST']

    # Create full URL
    full_url = f"{scheme}://{host}{url}"

    return full_url