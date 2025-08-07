from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('create/', views.student_create, name='student_create'),
    path('edit/<int:pk>/', views.student_edit, name='student_edit'),
    path('delete/<int:pk>/', views.student_delete, name='student_delete'),
    path('export/', views.student_export_excel, name='student_export_excel'),
    path('export_pdf/', views.student_export_pdf, name='student_export_pdf'),
    path('create/ajax/', views.student_create_ajax, name='student_create_ajax'),
    path('<int:pk>/quick_edit/', views.student_quick_edit, name='student_quick_edit'),
]


