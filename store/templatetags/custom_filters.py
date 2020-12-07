from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter(name="dot_to_comma")
@stringfilter
def dot_to_comma(value):
    return value.replace(".", ",")


@register.filter(name="address_type")
def address_type(value):
    if value:
        return "Principal"
    return "Secundário"


@register.filter(name="get_last_dict_value")
def get_last_dict_value(_dict):
    return list(_dict.values())[-1]


@register.filter(name="bank_slip_discount")
def bank_slip_discount(value):
    return float(value) * 0.9


@register.filter(name="remove_brand_name")
@stringfilter
def remove_brand_name(text):
    return text.split("Helga's ")[-1]
