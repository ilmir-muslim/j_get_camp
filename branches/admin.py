from django.contrib import admin
from .models import City, Branch


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "address"]
    list_filter = ["city"]
    search_fields = ["name", "city__name"]
    fields = ["name", "city", "address"]
