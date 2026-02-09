from django.contrib import admin

from schedule.templatetags.schedule_extras import romanize
from .models import Student, Squad  # Добавить Squad


@admin.register(Squad)
class SquadAdmin(admin.ModelAdmin):
    list_display = ["name", "get_roman_name", "leader", "schedule", "student_count"]
    list_filter = ["schedule", "schedule__branch"]
    search_fields = ["name", "leader__full_name"]

    def get_roman_name(self, obj):
        """Отображает номер отряда в римских цифрах"""

        return romanize(obj.name)

    get_roman_name.short_description = "Номер (римский)"

    def student_count(self, obj):
        return obj.students.count()

    student_count.short_description = "Количество учеников"


admin.site.register(Student)
