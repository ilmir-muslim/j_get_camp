from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('create/', views.employee_create, name='employee_create'),
    path('edit/<int:pk>/', views.employee_edit, name='employee_edit'),
    path('delete/<int:pk>/', views.employee_delete, name='employee_delete'),
]

urlpatterns += [
    path('attendances/', views.employee_attendance_list, name='employee_attendance_list'),
    path('attendances/toggle/', views.toggle_employee_attendance, name='toggle_employee_attendance'),
    path('<int:pk>/quick_edit/', views.employee_quick_edit, name='employee_quick_edit'),
    path('create/ajax/', views.employee_create_ajax, name='employee_create_ajax'),
]

