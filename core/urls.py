from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("analytics/", views.analytics_dashboard, name="analytics_dashboard"),
    path("tickets/create/", views.create_ticket, name="create_ticket"),
    path("tickets/my-tickets/", views.my_tickets, name="my_tickets"),
    path("tickets/list/", views.ticket_list, name="ticket_list"),
    path("tickets/update/<int:ticket_id>/", views.update_ticket, name="update_ticket"),
]
