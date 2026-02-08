from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def romanize(value):
    """Конвертирует число в римские цифры"""
    try:
        num = int(value)
    except (ValueError, TypeError):
        return value

    roman_numerals = {
        1000: "M",
        900: "CM",
        500: "D",
        400: "CD",
        100: "C",
        90: "XC",
        50: "L",
        40: "XL",
        10: "X",
        9: "IX",
        5: "V",
        4: "IV",
        1: "I",
    }

    roman = ""
    for r, letter in roman_numerals.items():
        while num >= r:
            roman += letter
            num -= r
    return roman
