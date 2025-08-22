from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404, redirect
from django.db import models

from core.utils import role_required
from payroll.forms import ExpenseForm, SalaryForm
from .models import Expense, Salary

@role_required(['manager', 'admin'])
def expense_list(request):
    """
    Список расходов с фильтрацией по сменам и выводом итоговой суммы.
    """
    user = request.user

    if user.role == 'manager':
        expenses = Expense.objects.all()
    else:
        expenses = Expense.objects.filter(schedule__branch=user.branch)

    total_amount = expenses.aggregate(models.Sum('amount'))['amount__sum'] or 0

    return render(request, 'payroll/expense_list.html', {
        'expenses': expenses,
        'total_amount': total_amount,
    })


@role_required(["manager", "admin"])
def salary_list(request):
    """
    Список зарплат с фильтрацией: все или только невыплаченные.
    """
    show_unpaid = request.GET.get("unpaid") == "1"

    if request.user.role == "manager":
        salaries = Salary.objects.all()
    else:
        salaries = Salary.objects.filter(schedule__branch=request.user.branch)

    if show_unpaid:
        salaries = salaries.filter(is_paid=False)

    # Создаем временный атрибут для отображения в шаблоне
    for salary in salaries:
        salary.days_worked_display = salary.calculate_days_worked()

    total_salary = (
        salaries.aggregate(models.Sum("total_payment"))["total_payment__sum"] or 0
    )

    return render(
        request,
        "payroll/salary_list.html",
        {
            "salaries": salaries,
            "total_salary": total_salary,
            "show_unpaid": show_unpaid,
        },
    )


@role_required(["manager", "admin"])
def salary_create(request):
    """
    Создание новой зарплаты.
    """
    if request.method == "POST":
        form = SalaryForm(request.POST)
        if form.is_valid():
            salary = form.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": True})
            return redirect("salary_list")
        else:
            # Возвращаем форму с ошибками в формате JSON
            html = render_to_string(
                "payroll/salary_form.html",
                {"form": form, "salary": None},
                request=request,
            )
            return JsonResponse({"success": False, "form_html": html})
    else:
        form = SalaryForm()

    # Для AJAX-запросов возвращаем только HTML формы
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "payroll/salary_form.html",
            {"form": form, "salary": None},
            request=request,
        )
        return JsonResponse({"html": html})

    return render(request, "payroll/salary_form.html", {"form": form, "salary": None})


@role_required(["manager", "admin"])
def salary_edit(request, pk):
    """
    Редактирование зарплаты.
    """
    salary = get_object_or_404(Salary, pk=pk)

    if request.method == "POST":
        form = SalaryForm(request.POST, instance=salary)
        if form.is_valid():
            salary = form.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": True})
            return redirect("salary_list")
        else:
            # Возвращаем форму с ошибками в формате JSON
            html = render_to_string(
                "payroll/salary_form.html",
                {"form": form, "salary": salary},
                request=request,
            )
            return JsonResponse({"success": False, "form_html": html})
    else:
        form = SalaryForm(instance=salary)

    # Для AJAX-запросов
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "payroll/salary_form.html",
            {"form": form, "salary": salary},
            request=request,
        )
        return JsonResponse({"html": html})

    return render(request, "payroll/salary_form.html", {"form": form, "salary": salary})


@role_required(["manager", "admin"])
def salary_delete(request, pk):
    """
    Удаление зарплаты.
    """
    salary = get_object_or_404(Salary, pk=pk)

    if request.method == "POST":
        salary.delete()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return redirect("salary_list")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": False, "error": "Invalid request method"})


@role_required(["manager", "admin"])
def expense_create(request):
    """
    Создание нового расхода.
    """
    initial = (
        {"schedule": request.GET.get("schedule")} if request.GET.get("schedule") else {}
    )

    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "expense": {
                            "id": expense.id,
                            "schedule_name": f"{expense.schedule.name} ({expense.schedule.start_date} - {expense.schedule.end_date})",
                            "category_display": expense.get_category_display(),
                            "comment": expense.comment,
                            "amount": expense.amount,
                        },
                    }
                )
            return redirect("expense_list")
    else:
        form = ExpenseForm(initial=initial)

    # Для AJAX-запросов возвращаем только HTML формы
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "payroll/expense_form.html",
            {"form": form, "expense": None},
            request=request,
        )
        return JsonResponse({"html": html})

    return render(request, "payroll/expense_form.html", {"form": form, "expense": None})


@role_required(["manager", "admin"])
def expense_edit(request, pk):
    """
    Редактирование существующего расхода.
    """
    expense = get_object_or_404(Expense, pk=pk)

    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            expense = form.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "expense": {
                            "id": expense.id,
                            "schedule_name": f"{expense.schedule.name} ({expense.schedule.start_date} - {expense.schedule.end_date})",
                            "category_display": expense.get_category_display(),
                            "comment": expense.comment,
                            "amount": expense.amount,
                        },
                    }
                )
            return redirect("expense_list")
    else:
        form = ExpenseForm(instance=expense)

    # Для AJAX-запросов
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "payroll/expense_form.html",
            {"form": form, "expense": expense},
            request=request,
        )
        return JsonResponse({"html": html})

    return render(
        request, "payroll/expense_form.html", {"form": form, "expense": expense}
    )


@role_required(['manager', 'admin'])
def expense_delete(request, pk):
    """
    Удаление расхода.
    """
    expense = get_object_or_404(Expense, pk=pk)

    if request.method == 'POST':
        expense.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest': 
            return JsonResponse({'success': True})
        return redirect('expense_list')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest': 
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
