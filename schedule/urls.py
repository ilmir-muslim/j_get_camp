from django.urls import path
from . import views

urlpatterns = [
    path("calendar/", views.schedule_calendar, name="schedule_calendar"),  # Изменено здесь
    path("create/", views.schedule_create, name="schedule_create"),
    path("delete/<int:pk>/", views.schedule_delete, name="schedule_delete"),
    path('quick_edit/<int:pk>/', views.schedule_quick_edit, name='schedule_quick_edit'),
    path('quick_edit/', views.schedule_quick_edit, name='schedule_quick_create'),
]