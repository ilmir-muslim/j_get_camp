from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Sum, Q
from django.core.paginator import Paginator
from django.contrib import messages

from core.utils import role_required
from employees.models import Employee
from payroll.models import Expense, Salary
from schedule.models import Schedule
from students.models import Student
from branches.models import Branch
from .models import Ticket
from .forms import TicketForm, TicketAdminForm


@login_required
def dashboard(request):
    """
    Отображает главную страницу с плитками разделов в зависимости от роли пользователя.
    """
    role = request.user.role
    context = {"role": role}
    return render(request, "core/dashboard.html", context)


@role_required(["manager", "admin"])
def analytics_dashboard(request):
    """
    Сводная аналитика с фильтрацией по городу для администраторов.
    """
    user = request.user
    branches = Branch.objects.all()

    # Для администраторов фильтруем по городу
    if user.role == "admin" and user.city:
        branches = branches.filter(city=user.city)

    # Получаем все смены для выбранных филиалов
    schedules = Schedule.objects.filter(branch__in=branches)

    # Получаем студентов через смены
    students = Student.objects.filter(schedule__in=schedules).distinct()

    # Получаем сотрудников через смены
    employees = Employee.objects.filter(schedule__in=schedules).distinct()

    # Общая статистика
    stats = {
        "schedule_count": schedules.count(),
        "employee_count": employees.count(),
        "student_count": students.count(),
        "total_expenses": Expense.objects.filter(schedule__in=schedules).aggregate(
            Sum("amount")
        )["amount__sum"]
        or 0,
        "total_salaries": Salary.objects.filter(employee__in=employees).aggregate(
            Sum("total_payment")
        )["total_payment__sum"]
        or 0,
    }

    # Статистика по филиалам
    branches_stats = []
    for branch in branches:
        branch_schedules = Schedule.objects.filter(branch=branch)

        # Студенты филиала (через смены)
        branch_students = Student.objects.filter(
            schedule__in=branch_schedules
        ).distinct()

        # Сотрудники филиала (через смены)
        branch_employees = Employee.objects.filter(
            schedule__in=branch_schedules
        ).distinct()

        branch_expenses = (
            Expense.objects.filter(schedule__in=branch_schedules).aggregate(
                Sum("amount")
            )["amount__sum"]
            or 0
        )

        branch_salaries = (
            Salary.objects.filter(employee__in=branch_employees).aggregate(
                Sum("total_payment")
            )["total_payment__sum"]
            or 0
        )

        branches_stats.append(
            {
                "name": branch.name,
                "city": branch.city.name if branch.city else "Не указан",
                "address": branch.address,
                "schedule_count": branch_schedules.count(),
                "employee_count": branch_employees.count(),
                "student_count": branch_students.count(),
                "total_expenses": branch_expenses,
                "total_salaries": branch_salaries,
            }
        )

    context = {
        "stats": stats,
        "branches_stats": branches_stats,
        "user_city": user.city.name if user.city else "Все города",
    }

    return render(request, "core/analytics_dashboard.html", context)


@login_required
def create_ticket(request):
    if request.method == "POST":
        form = TicketForm(request.POST, request.FILES)  # Добавлен request.FILES
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()

            messages.success(
                request,
                "Ваше сообщение об ошибке успешно отправлено! Мы рассмотрим его в ближайшее время.",
            )
            return redirect("dashboard")
    else:
        form = TicketForm()

    return render(request, "core/create_ticket.html", {"form": form})


@login_required
def my_tickets(request):
    if request.method == "GET":
        Ticket.objects.filter(user=request.user, has_unread_admin_response=True).update(
            has_unread_admin_response=False
        )

    tickets = Ticket.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "core/my_tickets.html", {"tickets": tickets})


@role_required(["manager", "admin"])
def ticket_list(request):
    tickets = Ticket.objects.all().order_by("-created_at")

    # Фильтрация по статусу
    status_filter = request.GET.get("status")
    if status_filter:
        tickets = tickets.filter(status=status_filter)

    paginator = Paginator(tickets, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Статистика для менеджера
    open_tickets_count = Ticket.objects.filter(status="open").count()
    in_progress_count = Ticket.objects.filter(status="in_progress").count()

    context = {
        "page_obj": page_obj,
        "open_tickets_count": open_tickets_count,
        "in_progress_count": in_progress_count,
        "total_tickets": tickets.count(),
        "current_filter": status_filter,
    }

    return render(request, "core/ticket_list.html", context)


@role_required(["manager", "admin"])
def update_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.method == "POST":
        form = TicketAdminForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, "Тикет успешно обновлен.")
            return redirect("ticket_list")
    else:
        form = TicketAdminForm(instance=ticket)

    return render(request, "core/update_ticket.html", {"form": form, "ticket": ticket})


# Контекстный процессор для отображения количества открытых тикетов
def get_open_tickets_count(request):
    """Контекстный процессор для отображения количества открытых тикетов"""
    if request.user.is_authenticated and request.user.role == "manager":
        return {"open_tickets_count": Ticket.objects.filter(status="open").count()}
    return {"open_tickets_count": 0}
