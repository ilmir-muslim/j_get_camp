from core.utils import role_required
from django.shortcuts import render, redirect, get_object_or_404

from employees.forms import EmployeeAttendanceForm, EmployeeForm
from .models import Employee, EmployeeAttendance


@role_required(["manager", "admin", "camp_head", "lab_head"])
def employee_list(request):
    """
    Выводит список сотрудников, фильтруя по роли пользователя:
    - Менеджер видит всех.
    - Администратор видит только сотрудников своего филиала.
    - Начальник лагеря/лаборатории видит сотрудников своей смены.
    """
    user = request.user

    if user.role == "manager":
        employees = Employee.objects.all()
    elif user.role == "admin":
        employees = Employee.objects.filter(branch=user.branch)
    else:  # camp_head, lab_head
        employees = Employee.objects.filter(schedule__in=user.schedule_set.all())

    return render(request, "employees/employee_list.html", {"employees": employees})


@role_required(["manager", "admin"])
def employee_create(request):
    """
    Представление для создания сотрудника.
    """
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("employee_list")
    else:
        form = EmployeeForm()

    return render(request, "employees/employee_form.html", {"form": form})


@role_required(["manager", "admin"])
def employee_edit(request, pk):
    """
    Представление для редактирования сотрудника.
    """
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect("employee_list")
    else:
        form = EmployeeForm(instance=employee)

    return render(request, "employees/employee_form.html", {"form": form})

@role_required(['manager', 'admin'])
def employee_delete(request, pk):
    """
    Представление для удаления сотрудника.
    Доступно только менеджеру и администратору.
    """
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        employee.delete()
        return redirect('employee_list')

    return render(request, 'employees/employee_confirm_delete.html', {'employee': employee})

@role_required(['manager', 'admin'])
def employee_attendance_list(request):
    """
    Список всех посещений сотрудников.
    """
    attendances = EmployeeAttendance.objects.all()
    return render(request, 'employees/employee_attendance_list.html', {'attendances': attendances})


@role_required(['manager', 'admin'])
def employee_attendance_create(request):
    """
    Создание посещения сотрудника.
    """
    if request.method == 'POST':
        form = EmployeeAttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employee_attendance_list')
    else:
        form = EmployeeAttendanceForm()

    return render(request, 'employees/employee_attendance_form.html', {'form': form})

@role_required(['manager', 'admin'])
def employee_attendance_edit(request, pk):
    """
    Редактирование посещения сотрудника.
    """
    attendance = get_object_or_404(EmployeeAttendance, pk=pk)

    if request.method == 'POST':
        form = EmployeeAttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            return redirect('employee_attendance_list')
    else:
        form = EmployeeAttendanceForm(instance=attendance)

    return render(request, 'employees/employee_attendance_form.html', {'form': form})

@role_required(['manager', 'admin'])
def employee_attendance_delete(request, pk):
    """
    Удаление посещения сотрудника.
    """
    attendance = get_object_or_404(EmployeeAttendance, pk=pk)

    if request.method == 'POST':
        attendance.delete()
        return redirect('employee_attendance_list')

    return render(request, 'employees/employee_attendance_confirm_delete.html', {'attendance': attendance})


