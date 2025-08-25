from django import template

register = template.Library()


@register.filter
def sumattr(iterable, attr):
    total = 0
    for item in iterable:
        # Проверяем, является ли элемент словарем
        if isinstance(item, dict):
            value = item.get(attr, 0)
        else:
            value = getattr(item, attr, 0)
        if value:
            total += value
    return total


@register.filter
def count_present(attendance_data, day_index):
    count = 0
    for student in attendance_data:
        # Получаем daily_attendance из словаря или объекта
        if isinstance(student, dict):
            daily_attendance = student.get("daily_attendance", [])
        else:
            daily_attendance = getattr(student, "daily_attendance", [])

        if (
            day_index < len(daily_attendance)
            and daily_attendance[day_index].get("status") == "Присутствовал"
        ):
            count += 1
    return count
