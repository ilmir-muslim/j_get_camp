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


@role_required(['manager', 'admin'])
def salary_list(request):
    """
    Список зарплат с фильтрацией: все или только невыплаченные.
    """
    show_unpaid = request.GET.get('unpaid') == '1'

    if request.user.role == 'manager':
        salaries = Salary.objects.all()
    else:
        salaries = Salary.objects.filter(schedule__branch=request.user.branch)

    if show_unpaid:
        salaries = salaries.filter(is_paid=False)

    total_salary = salaries.aggregate(models.Sum('total_payment'))['total_payment__sum'] or 0

    return render(request, 'payroll/salary_list.html', {
        'salaries': salaries,
        'total_salary': total_salary,
        'show_unpaid': show_unpaid,
    })

@role_required(['manager', 'admin'])
def salary_create(request):
    """
    Создание новой зарплаты.
    """
    if request.method == 'POST':
        form = SalaryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('salary_list')
    else:
        form = SalaryForm()

    return render(request, 'payroll/salary_form.html', {'form': form})


@role_required(['manager', 'admin'])
def salary_edit(request, pk):
    """
    Редактирование зарплаты.
    """
    salary = get_object_or_404(Salary, pk=pk)

    if request.method == 'POST':
        form = SalaryForm(request.POST, instance=salary)
        if form.is_valid():
            form.save()
            return redirect('salary_list')
    else:
        form = SalaryForm(instance=salary)

    return render(request, 'payroll/salary_form.html', {'form': form})

@role_required(['manager', 'admin'])
def salary_delete(request, pk):
    """
    Удаление зарплаты.
    """
    salary = get_object_or_404(Salary, pk=pk)

    if request.method == 'POST':
        salary.delete()
        return redirect('salary_list')

    return render(request, 'payroll/salary_confirm_delete.html', {'salary': salary})


@role_required(['manager', 'admin'])
def expense_create(request):
    """
    Создание нового расхода.
    """
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm()

    return render(request, 'payroll/expense_form.html', {'form': form})

@role_required(['manager', 'admin'])
def expense_edit(request, pk):
    """
    Редактирование существующего расхода.
    """
    expense = get_object_or_404(Expense, pk=pk)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'payroll/expense_form.html', {'form': form})

@role_required(['manager', 'admin'])
def expense_delete(request, pk):
    """
    Удаление расхода.
    """
    expense = get_object_or_404(Expense, pk=pk)

    if request.method == 'POST':
        expense.delete()
        return redirect('expense_list')

    return render(request, 'payroll/expense_confirm_delete.html', {'expense': expense})