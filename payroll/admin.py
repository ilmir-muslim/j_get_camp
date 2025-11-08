from django.contrib import admin
from .models import Expense, ExpenseCategory, Salary


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "schedule",
        "category",
        "comment",
        "amount",
        "display_category",
    ]
    list_filter = ["category", "schedule"]
    search_fields = ["comment", "category__name"]
    raw_id_fields = ["schedule", "category"]

    def display_category(self, obj):
        return obj.category.name

    display_category.short_description = "Категория"


@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = [
        "employee",
        "schedule",
        "payment_type",
        "daily_rate",
        "percent_rate",
        "total_payment",
        "is_paid",
    ]
    list_filter = ["is_paid", "payment_type", "schedule"]
    search_fields = ["employee__full_name"]
    raw_id_fields = ["employee", "schedule"]
