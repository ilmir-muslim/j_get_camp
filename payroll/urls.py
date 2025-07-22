from django.urls import path
from . import views

urlpatterns = [
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/edit/<int:pk>/', views.expense_edit, name='expense_edit'),
    path('expenses/delete/<int:pk>/', views.expense_delete, name='expense_delete'),
]

urlpatterns += [
    path('salaries/', views.salary_list, name='salary_list'),
    path('salaries/create/', views.salary_create, name='salary_create'),
    path('salaries/edit/<int:pk>/', views.salary_edit, name='salary_edit'),
    path('salaries/delete/<int:pk>/', views.salary_delete, name='salary_delete'),
]


