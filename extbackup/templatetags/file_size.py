from django.template.defaulttags import register


@register.filter
def sizify(value):
    """
    Simple kb/mb/gb size snippet for templates:
    """
    # value = ing(value)
    if value < 512000:
        value = value / 1024.0
        ext = 'KB'
    elif value < 4194304000:
        value = value / 1048576.0
        ext = 'MB'
    else:
        value = value / 1073741824.0
        ext = 'GB'
    return '%s %s' % (str(round(value, 2)), ext)
