from django.urls import path
from . import views

urlpatterns = [
    path("", views.regulation_list, name="regulation_list"),
    path("create/", views.regulation_create, name="regulation_create"),
    path("download/<int:pk>/", views.regulation_download, name="regulation_download"),
    path("delete/<int:pk>/", views.regulation_delete, name="regulation_delete"),
]
