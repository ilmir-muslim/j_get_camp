from .models import Ticket


def unread_tickets_count(request):
    """Контекстный процессор для отображения количества тикетов с непросмотренными ответами"""
    if request.user.is_authenticated:
        unread_count = Ticket.objects.filter(
            user=request.user, has_unread_admin_response=True
        ).count()
        return {"unread_tickets_count": unread_count}
    return {"unread_tickets_count": 0}
