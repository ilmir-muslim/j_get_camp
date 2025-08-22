from django.urls import path
from . import views

urlpatterns = [
    path("", views.student_list, name="student_list"),
    path("create/", views.student_create, name="student_create"),
    path("edit/<int:pk>/", views.student_edit, name="student_edit"),
    path("delete/<int:pk>/", views.student_delete, name="student_delete"),
    path("export/", views.student_export_excel, name="student_export_excel"),
    path("export_pdf/", views.student_export_pdf, name="student_export_pdf"),
    path("create/ajax/", views.student_create_ajax, name="student_create_ajax"),
    path("<int:pk>/quick_edit/", views.student_quick_edit, name="student_quick_edit"),
    path(
        "<int:student_id>/add_balance/", views.add_balance, name="student_add_balance"
    ),
    path(
        "<int:student_id>/balance_history/",
        views.get_balance_history,
        name="student_balance_history",
    ),
    path(
        "<int:student_id>/check_balance/",
        views.check_balance,
        name="student_check_balance",
    ),
    path(
        "<int:student_id>/payments/add_payment/",
        views.add_payment,
        name="student_add_payment",
    ),
    path(
        "<int:student_id>/payments/history/",
        views.payment_history,
        name="student_payment_history",
    ),
    path(
        "<int:student_id>/payment_info/",
        views.student_payment_info,
        name="student_payment_info",
    ),
    path(
        "<int:student_id>/payments/add_payment_form/",
        views.add_payment_form,
        name="student_add_payment_form",
    ),
]
