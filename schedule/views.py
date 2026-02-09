from decimal import Decimal, InvalidOperation
import io
import json
import openpyxl

from datetime import datetime, timedelta
from weasyprint import HTML

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Sum
from django.views.decorators.http import require_POST

from branches.models import Branch
from core.utils import role_required
from employees.models import Employee, EmployeeAttendance, Position
from payroll.forms import PaymentForm
from payroll.models import Expense, ExpenseCategory, Salary
from students.forms import SquadForm
from students.models import Balance, Payment, Squad, Student
from schedule.forms import ScheduleForm
from students.models import Attendance, Student

from .models import COLOR_CHOICES, Schedule


@role_required(["manager", "admin"])
def schedule_create(request):
    initial = {}

    if "branch" in request.GET:
        try:
            initial["branch"] = Branch.objects.get(pk=request.GET["branch"])
        except Branch.DoesNotExist:
            pass

    if "start_date" in request.GET and "end_date" in request.GET:
        initial["start_date"] = request.GET["start_date"]
        initial["end_date"] = request.GET["end_date"]

    if request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save()
            return redirect("schedule_calendar")
    else:
        form = ScheduleForm(initial=initial)

    return render(request, "schedule/schedule_form.html", {"form": form})


@role_required(["manager", "admin"])
def schedule_delete(request, pk):
    schedule_obj = get_object_or_404(Schedule, pk=pk)

    if request.method == "POST":
        schedule_obj.delete()

        # Поддержка AJAX-запросов
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        else:
            return redirect("schedule_calendar")

    return render(
        request, "schedule/schedule_confirm_delete.html", {"schedule": schedule_obj}
    )


@role_required(["manager", "admin", "camp_head", "lab_head"])
def schedule_calendar(request):
    month = request.GET.get("month")
    if month:
        try:
            current_date = datetime.strptime(month, "%Y-%m").date()
        except ValueError:
            current_date = timezone.now().date()
    else:
        current_date = timezone.now().date()

    first_day = current_date.replace(day=1)
    if first_day.month == 12:
        next_month = first_day.replace(year=first_day.year + 1, month=1, day=1)
    else:
        next_month = first_day.replace(month=first_day.month + 1, day=1)
    last_day = next_month - timedelta(days=1)

    prev_month = (first_day - timedelta(days=1)).strftime("%Y-%m")
    next_month = next_month.strftime("%Y-%m")

    weeks = []
    current = first_day - timedelta(days=first_day.weekday())

    while current <= last_day:
        friday = current + timedelta(days=4)
        weeks.append((current, friday))
        current += timedelta(days=7)

    # ФИЛЬТРАЦИЯ ФИЛИАЛОВ ДЛЯ АДМИНИСТРАТОРОВ И НАЧАЛЬНИКОВ
    user = request.user
    if user.role == "admin" and user.city:
        branches = Branch.objects.filter(city=user.city)
    elif user.role in ["camp_head", "lab_head"]:
        branches = Branch.objects.filter(id=user.branch.id)
    else:
        branches = Branch.objects.all()

    matrix = {}
    for branch in branches:
        branch_schedules = {}
        for week_start, week_end in weeks:
            schedules = Schedule.objects.filter(
                branch=branch, start_date__lte=week_end, end_date__gte=week_start
            )
            branch_schedules[week_start] = schedules
        matrix[branch.id] = branch_schedules

    week_headers = []
    for week_start, week_end in weeks:
        week_headers.append(
            f"{week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m')}"
        )

    context = {
        "current_date": current_date,
        "prev_month": prev_month,
        "next_month": next_month,
        "weeks": weeks,
        "week_headers": week_headers,
        "branches": branches,
        "matrix": matrix,
        "color_choices": COLOR_CHOICES,
    }
    return render(request, "schedule/schedule_calendar.html", context)


def schedule_quick_edit(request, pk=None):
    schedule = get_object_or_404(Schedule, pk=pk) if pk else None

    if request.method == "POST":
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            schedule = form.save()
            return JsonResponse({"success": True})
        else:
            # Возвращаем форму с ошибками
            form_html = render_to_string(
                "schedule/schedule_quick_form.html",
                {"form": form, "schedule": schedule},
                request=request,
            )
            return JsonResponse({"success": False, "html": form_html})

    # GET-запрос: отображаем форму
    if schedule:
        form = ScheduleForm(instance=schedule)
    else:
        initial = {}
        if request.GET.get("branch"):
            initial["branch"] = request.GET["branch"]
        if request.GET.get("week_start") and request.GET.get("week_end"):
            initial["start_date"] = request.GET["week_start"]
            initial["end_date"] = request.GET["week_end"]
        form = ScheduleForm(initial=initial)

    return render(
        request,
        "schedule/schedule_quick_form.html",
        {"form": form, "schedule": schedule},
    )


@role_required(["manager", "admin", "camp_head", "lab_head"])
def schedule_detail(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    user = request.user

    # Проверяем параметр в URL
    from_param = request.GET.get("from", "")
    from_schedule_list = from_param == "list" or "schedule/list" in request.META.get(
        "HTTP_REFERER", ""
    )

    dates = []
    current_date = schedule.start_date
    while current_date <= schedule.end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)

    employees = Employee.objects.filter(schedule=schedule)
    students = Student.objects.filter(schedule=schedule).order_by("full_name")

    attendance = {}
    for student in students:
        for date in dates:
            att, created = Attendance.objects.get_or_create(
                student=student,
                date=date,
                defaults={"present": False, "excused": False},
            )
            key = f"{student.id}_{date}"
            if att.present:
                status = "present"
            elif att.excused:
                status = "excused"
            else:
                status = "absent"
            attendance[key] = status

    student_attendance_counts = {}
    for student in students:
        count = Attendance.objects.filter(
            student=student, date__in=dates, present=True
        ).count()
        student_attendance_counts[student.id] = count

    employee_attendance = {}
    employee_attendance_counts = {}

    # РАСЧЕТ ЗАРПЛАТ СОТРУДНИКОВ И ИНФОРМАЦИЯ О ВЫПЛАТАХ
    employee_salaries = {}
    employee_paid_salaries = {}

    for employee in employees:
        total = 0
        for date in dates:
            # Получаем или создаем запись посещаемости
            att, created = EmployeeAttendance.objects.get_or_create(
                employee=employee,
                date=date,
                defaults={"present": False, "excused": False},
            )
            key = f"{employee.id}_{date}"
            if att.present:
                status = "present"
                total += 1
            elif att.excused:
                status = "excused"
            else:
                status = "absent"
            employee_attendance[key] = status

        employee_attendance_counts[employee.id] = total

        # Рассчитываем зарплату: ставка * количество посещений
        rate = employee.rate_per_day or 0
        calculated_salary = rate * total

        # Проверяем, есть ли уже выплаченная зарплата для этого сотрудника и смены
        paid_salary = Salary.objects.filter(
            employee=employee, schedule=schedule, is_paid=True
        ).first()

        if paid_salary:
            # Если зарплата уже выплачена, используем сумму из выплаты
            employee_salaries[employee.id] = paid_salary.total_payment
            employee_paid_salaries[employee.id] = {
                "amount": paid_salary.total_payment,
                "is_paid": True,
                "salary_id": paid_salary.id,
            }
        else:
            # Иначе используем рассчитанную сумму
            employee_salaries[employee.id] = calculated_salary
            employee_paid_salaries[employee.id] = {
                "amount": calculated_salary,
                "is_paid": False,
                "salary_id": None,
            }

    student_total_payments = {}
    for student in students:
        total_paid = student.get_total_paid_for_schedule(schedule)
        student_total_payments[student.id] = total_paid

    # Общая сумма платежей по смене (для футера)
    total_payments = (
        Payment.objects.filter(schedule=schedule).aggregate(total=Sum("amount"))[
            "total"
        ]
        or 0
    )

    available_employees = Employee.objects.exclude(schedule=schedule)
    available_students = Student.objects.exclude(schedule=schedule)

    # Объединяем расходы и зарплаты для отображения
    expenses = Expense.objects.filter(schedule=schedule)
    salaries = Salary.objects.filter(schedule=schedule, is_paid=True)

    # Создаем объединенный список финансовых записей
    financial_records = []

    # Добавляем расходы
    for expense in expenses:
        financial_records.append(
            {
                "type": "expense",
                "id": expense.id,
                "category_display": expense.category.name,
                "comment": expense.comment,
                "amount": expense.amount,
            }
        )

    # Добавляем зарплаты
    for salary in salaries:
        financial_records.append(
            {
                "type": "salary",
                "id": salary.id,
                "category_display": "Выплата зарплаты",
                "comment": f"Зарплата сотрудника {salary.employee.full_name}",
                "amount": salary.total_payment,
            }
        )

    # Сортируем по ID в обратном порядке, чтобы новые были сверху
    financial_records.sort(key=lambda x: x["id"], reverse=True)

    # Общая сумма расходов и зарплат
    total_expenses_sum = (expenses.aggregate(total=Sum("amount"))["total"] or 0) + (
        salaries.aggregate(total=Sum("total_payment"))["total"] or 0
    )

    # Получаем категорию для выплаты зарплаты (теперь не используется при выплате, но может пригодиться)
    salary_category, created = ExpenseCategory.objects.get_or_create(
        name="выплата зарплаты",
        defaults={"description": "Выплата заработной платы сотрудникам"},
    )

    # Получаем отряды с вожатыми
    squads_with_leaders = {}
    for student in students:
        if student.squad and student.squad.leader:
            squads_with_leaders[student.squad.id] = {
                "name": student.squad.name,
                "leader_name": student.squad.leader.full_name,
            }

    if user.role == "admin" and user.city:
        available_branches = Branch.objects.filter(city=user.city)
        available_schedules = Schedule.objects.filter(branch__city=user.city)
    elif user.role in ["camp_head", "lab_head"]:
        available_branches = Branch.objects.filter(id=user.branch.id)
        available_schedules = Schedule.objects.filter(branch=user.branch)
    else:
        available_branches = Branch.objects.all()
        available_schedules = Schedule.objects.all()

    context = {
        "schedule": schedule,
        "employees": employees,
        "students": students,
        "dates": dates,
        "attendance": attendance,
        "available_employees": available_employees,
        "available_students": available_students,
        "student_attendance_counts": student_attendance_counts,
        "financial_records": financial_records,
        "employee_attendance": employee_attendance,
        "employee_attendance_counts": employee_attendance_counts,
        "employee_salaries": employee_salaries,
        "employee_paid_salaries": employee_paid_salaries,
        "total_expenses_sum": total_expenses_sum,
        "student_total_payments": student_total_payments,
        "total_payments": total_payments,
        "from_schedule_list": from_schedule_list,
        "available_branches": available_branches,
        "available_schedules": available_schedules,
        "salary_category_id": salary_category.id,
        "squads_with_leaders": squads_with_leaders,  # Добавляем информацию о вожатых
    }
    return render(request, "schedule/schedule_detail.html", context)


@require_POST
@role_required(["manager", "admin", "camp_head", "lab_head"])
def remove_employee_from_schedule(request, schedule_id, employee_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    employee = get_object_or_404(Employee, pk=employee_id)

    if employee.schedule == schedule:
        employee.schedule = None
        employee.save()

    return JsonResponse({"success": True})


@require_POST
@role_required(["manager", "admin", "camp_head", "lab_head"])
def remove_student_from_schedule(request, schedule_id, student_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    student = get_object_or_404(Student, pk=student_id)

    # Получаем все платежи студента за эту смену
    payments = Payment.objects.filter(student=student, schedule=schedule)

    # Суммируем все платежи
    total_amount = payments.aggregate(total=Sum("amount"))["total"] or 0

    # Если есть платежи, создаем операцию возврата на баланс
    if total_amount > 0:
        Balance.objects.create(
            student=student,
            amount=total_amount,
            operation_type="deposit",
            comment=f'Возврат средств при удалении из смены "{schedule.name}"',
            created_by=request.user,
        )

    # Возвращаем списание за смену
    student.refund_schedule_charge(schedule, request.user)

    # Удаляем все платежи студента за эту смену
    payments.delete()

    # Отвязываем студента от смены
    if student.schedule == schedule:
        student.schedule = None
        student.save()

    return JsonResponse(
        {"success": True, "student_id": student.id, "student_name": student.full_name}
    )


@role_required(["manager", "admin", "camp_head", "lab_head"])
def export_schedule_students_excel(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    students = Student.objects.filter(schedule=schedule)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Ученики {schedule.name}"

    ws.append(
        ["ФИО", "Телефон", "Родитель", "Тип посещения", "Цена", "Комментарий к цене"]
    )

    for student in students:
        ws.append(
            [
                student.full_name,
                student.phone,
                student.parent_name,
                student.get_attendance_type_display(),
                student.individual_price or student.default_price,
                student.price_comment,
            ]
        )

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f"attachment; filename=students_{schedule.name}.xlsx"
    )
    return response


@role_required(["manager", "admin", "camp_head", "lab_head"])
def export_schedule_students_pdf(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    students = Student.objects.filter(schedule=schedule).order_by("full_name")

    html_string = render_to_string(
        "schedule/schedule_students_pdf.html",
        {"schedule": schedule, "students": students},
    )
    html = HTML(string=html_string)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=students_{schedule.name}.pdf"
    html.write_pdf(response)

    return response


@role_required(["manager", "admin", "camp_head", "lab_head"])
def schedule_list(request):
    # ФИЛЬТРАЦИЯ СМЕН ДЛЯ АДМИНИСТРАТОРОВ И НАЧАЛЬНИКОВ
    user = request.user
    if user.role == "admin" and user.city:
        schedules = (
            Schedule.objects.select_related("branch")
            .prefetch_related("employee_set", "student_set")
            .filter(branch__city=user.city)
        )
    elif user.role in ["camp_head", "lab_head"]:
        schedules = (
            Schedule.objects.select_related("branch")
            .prefetch_related("employee_set", "student_set")
            .filter(branch=user.branch)
        )
    else:
        schedules = (
            Schedule.objects.select_related("branch")
            .prefetch_related("employee_set", "student_set")
            .all()
        )

    schedule_data = []
    for schedule in schedules:
        # ИСПРАВЛЕНИЕ: Получаем позиции по их названию
        camp_head_position = Position.objects.filter(name="Начальник лагеря").first()
        lab_head_position = Position.objects.filter(
            name="Начальник лаборатории"
        ).first()

        camp_head = schedule.employee_set.filter(position=camp_head_position).first()
        lab_head = schedule.employee_set.filter(position=lab_head_position).first()
        student_count = schedule.student_set.count()

        schedule_data.append(
            {
                "id": schedule.id,
                "name": schedule.name,
                "theme": schedule.theme,
                "dates": f"{schedule.start_date.strftime('%d.%m.%Y')} – {schedule.end_date.strftime('%d.%m.%Y')}",
                "branch": schedule.branch.name,
                "student_count": student_count,
                "camp_head": camp_head.full_name if camp_head else "—",
                "lab_head": lab_head.full_name if lab_head else "—",
            }
        )

    return render(
        request, "schedule/schedule_list.html", {"schedule_data": schedule_data}
    )


@require_POST
@role_required(["manager", "admin", "camp_head", "lab_head"])
def toggle_attendance(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)

    try:
        data = json.loads(request.body)

        # Обработка учеников
        if "student_id" in data:
            student_id = data.get("student_id")
            date_str = data.get("date")
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

            student = get_object_or_404(Student, id=student_id)
            att, created = Attendance.objects.get_or_create(
                student=student,
                date=date_obj,
                defaults={"present": False, "excused": False},
            )

            # Циклическое переключение: отсутствует -> присутствует -> по уважительной -> отсутствует
            if not att.present and not att.excused:
                att.present = True
                status = "present"
            elif att.present:
                att.present = False
                att.excused = True
                status = "excused"
            else:  # excused: True
                att.excused = False
                status = "absent"
            att.save()

            # Пересчитываем общее количество посещений
            total_attendance = Attendance.objects.filter(
                student=student,
                date__range=(schedule.start_date, schedule.end_date),
                present=True,
            ).count()

            return JsonResponse(
                {
                    "status": "success",
                    "present": att.present,
                    "excused": att.excused,
                    "total_attendance": total_attendance,
                    "student_id": student_id,
                    "date": date_str,
                }
            )

        # Обработка сотрудников
        elif "employee_id" in data:
            employee_id = data.get("employee_id")
            date_str = data.get("date")
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

            employee = get_object_or_404(Employee, id=employee_id)
            att, created = EmployeeAttendance.objects.get_or_create(
                employee=employee,
                date=date_obj,
                defaults={"present": False, "excused": False},
            )

            # Циклическое переключение статусов
            if not att.present and not att.excused:
                att.present = True
                status = "present"
            elif att.present:
                att.present = False
                att.excused = True
                status = "excused"
            else:  # excused: True
                att.excused = False
                status = "absent"
            att.save()

            # Пересчет общего количества посещений
            total_attendance = EmployeeAttendance.objects.filter(
                employee=employee,
                date__range=(schedule.start_date, schedule.end_date),
                present=True,
            ).count()

            return JsonResponse(
                {
                    "status": "success",
                    "present": att.present,
                    "excused": att.excused,
                    "total_attendance": total_attendance,
                    "employee_id": employee_id,
                    "date": date_str,
                }
            )

        else:
            return JsonResponse(
                {"status": "error", "message": "Не указан student_id или employee_id"},
                status=400,
            )

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


def get_updated_schedule_data(request, pk):
    try:
        schedule = Schedule.objects.get(pk=pk)

        # Получаем обновленные данные
        total_payments = (
            Payment.objects.filter(student__schedule_students=schedule).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        total_expenses = (
            Expense.objects.filter(schedule=schedule).aggregate(total=Sum("amount"))[
                "total"
            ]
            or 0
        )

        return JsonResponse(
            {
                "success": True,
                "total_payments": float(total_payments),
                "total_expenses": float(total_expenses),
            }
        )
    except Schedule.DoesNotExist:
        return JsonResponse({"success": False, "error": "Schedule not found"})


@role_required(["manager", "admin", "camp_head", "lab_head"])
def export_schedule_attendance_excel(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    students = Student.objects.filter(schedule=schedule).order_by("full_name")

    # Создаем workbook и worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Посещаемость {schedule.name}"

    # Заголовки - добавляем все колонки из таблицы
    headers = ["№", "ФИО", "Стоимость", "Платежи", "Тип", "Явка"]
    dates = []
    current_date = schedule.start_date
    while current_date <= schedule.end_date:
        dates.append(current_date)
        headers.append(current_date.strftime("%d.%m"))
        current_date += timedelta(days=1)

    ws.append(headers)

    # Данные
    for index, student in enumerate(students, 1):
        # Считаем количество посещенных дней
        attendance_count = Attendance.objects.filter(
            student=student, date__in=dates, present=True
        ).count()

        # Получаем общую сумму платежей студента
        total_paid = (
            Payment.objects.filter(student=student, schedule=schedule).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        row = [
            index,
            student.full_name,
            student.individual_price or student.default_price,
            total_paid,
            student.get_attendance_type_display(),
            attendance_count,
        ]

        # Для каждой даты получаем статус посещения
        for date in dates:
            try:
                att = Attendance.objects.get(student=student, date=date)
                if att.present:
                    status = "✓"
                elif att.excused:
                    status = "⚠"
                else:
                    status = "✗"
            except Attendance.DoesNotExist:
                status = "✗"

            row.append(status)

        ws.append(row)

    # Сохраняем в HttpResponse
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f"attachment; filename=attendance_{schedule.name}.xlsx"
    )
    return response


@role_required(["manager", "admin", "camp_head", "lab_head"])
def export_schedule_attendance_pdf(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    students = Student.objects.filter(schedule=schedule).order_by("full_name")

    dates = []
    current_date = schedule.start_date
    while current_date <= schedule.end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)

    # Подготовим данные для таблицы
    attendance_data = []
    for student in students:
        # Считаем количество посещенных дней
        attendance_count = Attendance.objects.filter(
            student=student, date__in=dates, present=True
        ).count()

        # Получаем общую сумму платежей студента
        total_paid = (
            Payment.objects.filter(student=student, schedule=schedule).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        row = {
            "full_name": student.full_name,
            "attendance_type": student.get_attendance_type_display(),
            "price": student.individual_price or student.default_price,
            "total_paid": total_paid,
            "current_balance": student.current_balance,  # Добавляем баланс
            "attendance_count": attendance_count,
            "daily_attendance": [],
        }

        for date in dates:
            try:
                att = Attendance.objects.get(student=student, date=date)
                if att.present:
                    status = "Присутствовал"
                elif att.excused:
                    status = "По уважительной"
                else:
                    status = "Отсутствовал"
            except Attendance.DoesNotExist:
                status = "Отсутствовал"

            row["daily_attendance"].append({"date": date, "status": status})

        attendance_data.append(row)

    html_string = render_to_string(
        "schedule/schedule_attendance_pdf.html",
        {"schedule": schedule, "dates": dates, "attendance_data": attendance_data},
    )

    html = HTML(string=html_string)
    buffer = io.BytesIO()
    html.write_pdf(buffer)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=attendance_{schedule.name}.pdf"
    return response


@role_required(["manager", "admin", "camp_head", "lab_head"])
def create_squad(request, pk):
    """Создание отряда через AJAX"""
    schedule = get_object_or_404(Schedule, pk=pk)

    if request.method == "POST":
        form = SquadForm(request.POST, schedule=schedule, request=request)
        if form.is_valid():
            squad = form.save(commit=False)
            squad.schedule = schedule
            squad.save()

            return JsonResponse(
                {
                    "success": True,
                    "squad": {
                        "id": squad.id,
                        "name": squad.name,
                        "leader_id": squad.leader.id if squad.leader else None,
                        "leader_name": squad.leader.full_name if squad.leader else None,
                    },
                    "message": f"Отряд {squad.name} успешно создан",
                }
            )
        else:
            return JsonResponse(
                {"success": False, "errors": form.errors.as_json()}, status=400
            )

    # GET запрос - отдать форму
    form = SquadForm(schedule=schedule, request=request)
    return render(
        request, "schedule/squad_form.html", {"form": form, "schedule": schedule}
    )


@role_required(["manager", "admin", "camp_head", "lab_head"])
def delete_squad(request, pk, squad_id):
    """Удаление отряда"""
    schedule = get_object_or_404(Schedule, pk=pk)
    squad = get_object_or_404(Squad, id=squad_id, schedule=schedule)

    if request.method == "POST":
        # Проверяем, нет ли учеников или сотрудников в отряде
        if squad.students.exists():
            return JsonResponse(
                {
                    "success": False,
                    "error": "Невозможно удалить отряд, в котором есть ученики",
                },
                status=400,
            )

        # Если у отряда есть вожатый, сбрасываем у него флаг is_leader
        if squad.leader:
            squad.leader.is_leader = False
            squad.leader.save(update_fields=["is_leader"])

        squad.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Метод не разрешен"}, status=405)
