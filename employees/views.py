#employees/views.py
from datetime import datetime, timedelta
import json

from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from branches.models import Branch
from employees.forms import EmployeeAttendanceForm, EmployeeForm
from core.utils import role_required
from schedule.models import Schedule
from .models import Employee, EmployeeAttendance


@role_required(["manager", "admin", "camp_head", "lab_head"])
def employees_list(request):
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

    # Добавляем дополнительные данные для формы создания
    branches = Branch.objects.all()
    schedules = Schedule.objects.all()

    return render(
        request,
        "employees/employees_list.html",
        {"employees": employees, "branches": branches, "schedules": schedules},
    )


@role_required(["manager", "admin"])
def employee_create(request):
    """
    Представление для создания сотрудника.
    """
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("employees_list")
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
            return redirect("employees_list")
    else:
        form = EmployeeForm(instance=employee)

    return render(request, "employees/employee_form.html", {"form": form})


@role_required(["manager", "admin"])
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        employee.delete()

        # Возвращаем JSON-ответ для AJAX
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return redirect("employees_list")

    return render(
        request, "employees/employee_confirm_delete.html", {"employee": employee}
    )


@role_required(["manager", "admin"])
def employee_attendance_list(request):
    # Определяем период по умолчанию (текущая неделя)
    today = timezone.now().date()
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)

    # Обработка выбора периода пользователем
    if request.method == "GET":
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

                # Корректируем если даты перепутаны
                if start_date > end_date:
                    start_date, end_date = end_date, start_date
            except ValueError:
                # В случае ошибки оставляем значения по умолчанию
                pass

    # Получаем даты периода
    dates = [
        start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)
    ]

    # Получаем сотрудников
    employees = Employee.objects.all()

    # Получаем посещения за период
    attendances = EmployeeAttendance.objects.filter(date__range=(start_date, end_date))

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
        "dates": dates,
        "employees": employees,
        "attendance_matrix": attendance_matrix,
        "start_date": start_date,
        "end_date": end_date,
        "selected_start_date": start_date.isoformat(),
        "selected_end_date": end_date.isoformat(),
    }
    return render(request, "employees/employee_attendance_calendar.html", context)


@role_required(["manager", "admin"])
def employee_attendance_create(request):
    """
    Создание посещения сотрудника.
    """
    if request.method == "POST":
        form = EmployeeAttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("employee_attendance_list")
    else:
        form = EmployeeAttendanceForm()

    return render(request, "employees/employee_attendance_form.html", {"form": form})


@role_required(["manager", "admin"])
def employee_attendance_edit(request, pk):
    """
    Редактирование посещения сотрудника.
    """
    attendance = get_object_or_404(EmployeeAttendance, pk=pk)

    if request.method == "POST":
        form = EmployeeAttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            return redirect("employee_attendance_list")
    else:
        form = EmployeeAttendanceForm(instance=attendance)

    return render(request, "employees/employee_attendance_form.html", {"form": form})


@role_required(["manager", "admin"])
def employee_attendance_delete(request, pk):
    """
    Удаление посещения сотрудника.
    """
    attendance = get_object_or_404(EmployeeAttendance, pk=pk)

    if request.method == "POST":
        attendance.delete()
        return redirect("employee_attendance_list")

    return render(
        request,
        "employees/employee_attendance_confirm_delete.html",
        {"attendance": attendance},
    )


@role_required(["manager", "admin"])
def toggle_employee_attendance(request):
    if request.method == "POST":
        data = json.loads(request.body)
        employee_id = data.get("employee_id")
        date_str = data.get("date")

        try:
            employee = Employee.objects.get(id=employee_id)
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Ищем существующую запись
            attendance, created = EmployeeAttendance.objects.get_or_create(
                employee=employee, date=date_obj, defaults={"present": True}
            )

            if not created:
                # Инвертируем статус присутствия
                attendance.present = not attendance.present
                attendance.save()

            return JsonResponse({"status": "success", "present": attendance.present})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error"}, status=400)


def employee_quick_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save()
            return JsonResponse(
                {
                    "success": True,
                    "employee": {
                        "id": employee.id,
                        "full_name": employee.full_name,
                        "position_display": employee.get_position_display(),
                        "branch_name": (
                            employee.branch.name if employee.branch else None
                        ), 
                        "schedule_name": (
                            employee.schedule.name if employee.schedule else None
                        ), 
                        "rate_per_day": employee.rate_per_day,
                    },
                }
            )
        return JsonResponse({"success": False, "errors": form.errors})
    # GET-запрос — отрисовать форму
    form = EmployeeForm(instance=employee)
    return render(
        request,
        "employees/employee_quick_form.html",
        {"form": form, "employee": employee},
    )


@require_POST
@role_required(["manager", "admin"])
def employee_create_ajax(request):
    try:
        data = json.loads(request.body)
        # Преобразуем ключи для формы
        if "branch_id" in data:
            data["branch"] = data.pop("branch_id") or None
        if "schedule_id" in data:
            data["schedule"] = data.pop("schedule_id") or None

        form = EmployeeForm(data)
        if form.is_valid():
            employee = form.save()
            return JsonResponse(
                {
                    "success": True,
                    "employee": {
                        "id": employee.id,
                        "full_name": employee.full_name,
                        "position": employee.position,
                        "position_display": employee.get_position_display(),
                        "branch_name": (
                            employee.branch.name if employee.branch else None
                        ),
                        "schedule_name": (
                            employee.schedule.name if employee.schedule else None
                        ),
                        "rate_per_day": str(employee.rate_per_day),
                    },
                }
            )
        return JsonResponse(
            {"success": False, "error": form.errors.as_json()}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
