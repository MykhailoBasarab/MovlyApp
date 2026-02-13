from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Отримати елемент зі словника за ключем"""
    if dictionary is None:
        return None
    return dictionary.get(key)

