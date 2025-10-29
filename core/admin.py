from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Ticket


class CustomUserAdmin(UserAdmin):
    # Упрощенные поля при создании пользователя
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2", "role", "branch"),
            },
        ),
    )

    # Упрощенные поля при редактировании пользователя
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (_("Custom fields"), {"fields": ("role", "branch")}),  # Убрали schedules
    )

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "branch",
        "city",
        "is_staff",
    )
    list_filter = ("role", "branch", "city", "is_staff")
    search_fields = ("username", "first_name", "last_name", "email")

    def save_model(self, request, obj, form, change):
        # Автоматически устанавливаем город из филиала
        if obj.branch and obj.branch.city:
            obj.city = obj.branch.city
        super().save_model(request, obj, form, change)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["subject", "user", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["subject", "description", "user__username"]
    readonly_fields = ["created_at", "updated_at"]
    list_editable = ["status"]


admin.site.register(CustomUser, CustomUserAdmin)
