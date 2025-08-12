from django.urls import path
from . import views

urlpatterns = [
    path("calendar/", views.schedule_calendar, name="schedule_calendar"),
    path("create/", views.schedule_create, name="schedule_create"),
    path("delete/<int:pk>/", views.schedule_delete, name="schedule_delete"),
    path("quick_edit/<int:pk>/", views.schedule_quick_edit, name="schedule_quick_edit"),
    path("quick_edit/", views.schedule_quick_edit, name="schedule_quick_create"),
    path("<int:pk>/", views.schedule_detail, name="schedule_detail"),
    path(
        "<int:schedule_id>/remove_employee/<int:employee_id>/",
        views.remove_employee_from_schedule,
        name="remove_employee_from_schedule",
    ),
    path(
        "<int:schedule_id>/remove_student/<int:student_id>/",
        views.remove_student_from_schedule,
        name="remove_student_from_schedule",
    ),
    path(
        "<int:pk>/export_excel/",
        views.export_schedule_students_excel,
        name="export_schedule_students_excel",
    ),
    path(
        "<int:pk>/export_pdf/",
        views.export_schedule_students_pdf,
        name="export_schedule_students_pdf",
    ),
    path("list/", views.schedule_list, name="schedule_list"),
    path("<int:pk>/add-employee/", views.schedule_detail, name="schedule_add_employee"),
    path("<int:pk>/add-student/", views.schedule_detail, name="schedule_add_student"),
    path(
        "<int:schedule_id>/remove-employee/<int:employee_id>/",
        views.remove_employee_from_schedule,
        name="schedule_remove_employee",
    ),
    path(
        "<int:schedule_id>/remove-student/<int:student_id>/",
        views.remove_student_from_schedule,
        name="schedule_remove_student",
    ),
    path("delete/<int:pk>/", views.schedule_delete, name="schedule_delete"),
    path(
        "<int:schedule_id>/toggle_attendance/",
        views.toggle_attendance,
        name="toggle_attendance",
    ),
    #     path(
    #     "<int:schedule_id>/employee_toggle_attendance/",
    #     views.employee_toggle_attendance,
    #     name="employee_toggle_attendance",
    # ),
]
