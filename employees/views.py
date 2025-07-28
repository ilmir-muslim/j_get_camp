from datetime import datetime, timedelta
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from employees.forms import EmployeeAttendanceForm, EmployeeForm
from core.utils import role_required
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
    # Определяем период по умолчанию (текущая неделя)
    today = timezone.now().date()
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)
    
    # Обработка выбора периода пользователем
    if request.method == 'GET':
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                
                # Корректируем если даты перепутаны
                if start_date > end_date:
                    start_date, end_date = end_date, start_date
            except ValueError:
                # В случае ошибки оставляем значения по умолчанию
                pass
    
    # Получаем даты периода
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    
    # Получаем сотрудников
    employees = Employee.objects.all()
    
    # Получаем посещения за период
    attendances = EmployeeAttendance.objects.filter(
        date__range=(start_date, end_date)
    )
    
    # Создаем матрицу посещений: {employee_id: {date: attendance}}
    attendance_matrix = {}
    for employee in employees:
        employee_matrix = {}
        for date in dates:
            try:
                attendance = attendances.get(employee=employee, date=date)
                employee_matrix[date] = attendance
            except EmployeeAttendance.DoesNotExist:
                employee_matrix[date] = None
        attendance_matrix[employee.id] = employee_matrix

    context = {
        'dates': dates,
        'employees': employees,
        'attendance_matrix': attendance_matrix,
        'start_date': start_date,
        'end_date': end_date,
        'selected_start_date': start_date.isoformat(),
        'selected_end_date': end_date.isoformat(),
    }
    return render(request, 'employees/employee_attendance_calendar.html', context)

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


@role_required(['manager', 'admin'])
def toggle_employee_attendance(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        employee_id = data.get('employee_id')
        date_str = data.get('date')
        
        try:
            employee = Employee.objects.get(id=employee_id)
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Ищем существующую запись
            attendance, created = EmployeeAttendance.objects.get_or_create(
                employee=employee,
                date=date_obj,
                defaults={'present': True}
            )
            
            if not created:
                # Инвертируем статус присутствия
                attendance.present = not attendance.present
                attendance.save()
            
            return JsonResponse({
                'status': 'success',
                'present': attendance.present
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)