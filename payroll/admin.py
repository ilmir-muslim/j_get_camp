from django.contrib import admin
from .models import Expense, ExpenseCategory, Salary


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


admin.site.register(Expense)
admin.site.register(Salary)
