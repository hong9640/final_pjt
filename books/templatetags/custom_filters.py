from django import template

register = template.Library()

@register.filter
def slugify_filter(value):
    return value.replace("/", "-")
