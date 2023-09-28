# from django import template
# from django.urls import resolve, reverse
# from django.utils.translation import activate, get_language
#
# register = template.Library()
#
# @register.simple_tag(takes_context=True)
# def change_lang(context, lang=None):
#     path = context['request'].path
#     url_parts = resolve(path)
#
#     # remove old language prefix and add the new prefix
#     new_path = path.replace(f"/{url_parts.namespace}/", f"/{lang}/")
#
#     return new_path