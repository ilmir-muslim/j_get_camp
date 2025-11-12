from django.contrib import admin
from .models import Employee, EmployeeAttendance, Position


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ["name", "responsibilities"]
    search_fields = ["name", "responsibilities"]
    list_filter = ["name"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["full_name", "position", "branch", "schedule", "rate_per_day"]
    list_filter = ["position", "branch", "schedule"]
    search_fields = ["full_name"]


admin.site.register(EmployeeAttendance)
