from django.contrib import admin
from .models import Student, Squad  # Добавить Squad


@admin.register(Squad)
class SquadAdmin(admin.ModelAdmin):
    list_display = ["name", "leader", "schedule", "student_count"]
    list_filter = ["schedule", "schedule__branch"]
    search_fields = ["name", "leader__full_name"]

    def student_count(self, obj):
        return obj.students.count()

    student_count.short_description = "Количество учеников"


admin.site.register(Student)
