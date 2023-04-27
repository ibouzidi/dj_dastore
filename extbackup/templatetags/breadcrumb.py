from django import template
from django.urls import reverse
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def breadcrumb(context):
    """
    Generate breadcrumbs based on the current request path.
    """
    breadcrumbs = []
    path_components = context['request'].path.split('/')
    url = ''
    for component in path_components:
        if component:
            url += f'/{component}'
            breadcrumbs.append({
                'label': component.title(),
                'url': url,
            })

    # Add home breadcrumb
    breadcrumbs.insert(0, {
        'label': '<i class="fas fa-home"></i>',
        'url': reverse('HomeView'),
    })

    # Generate breadcrumb HTML
    html = ''
    for index, breadcrumb in enumerate(breadcrumbs):
        active = (index == len(breadcrumbs) - 1)
        html += f'<li class="breadcrumb-item{" active" if active else ""}">'
        if not active:
            html += f'<a href="{breadcrumb["url"]}">{breadcrumb["label"]}</a>'
        else:
            html += breadcrumb["label"]
        html += '</li>'

    return mark_safe(html)