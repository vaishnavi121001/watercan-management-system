from django import template

register = template.Library()

@register.filter(name='add_attr')
def add_attr(field, attr):
    attrs = {}
    definition = attr.split(':', 1)
    if len(definition) == 2:
        attrs[definition[0]] = definition[1]
    return field.as_widget(attrs=attrs)
