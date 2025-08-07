from django.urls import path
from branches import views

urlpatterns = [
    path('', views.branch_list, name='branch_list'),
    path('create/', views.branch_create, name='branch_create'),
    path('edit/<int:pk>/', views.branch_edit, name='branch_edit'),
    path('delete/<int:pk>/', views.branch_delete, name='branch_delete'),
    path('<int:pk>/details/', views.branch_detail_modal, name='branch_detail_modal'),
]
