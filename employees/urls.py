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
    path('attendances/create/', views.employee_attendance_create, name='employee_attendance_create'),
    path('attendances/edit/<int:pk>/', views.employee_attendance_edit, name='employee_attendance_edit'),
    path('attendances/delete/<int:pk>/', views.employee_attendance_delete, name='employee_attendance_delete'),
]

