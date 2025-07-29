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

from branches.models import Branch
from core.utils import role_required
from employees.models import Employee
from payroll.forms import PaymentForm
from students.models import Payment
from schedule.forms import ScheduleForm
from students.models import Attendance, Student

from .models import COLOR_CHOICES, Schedule

@role_required(["manager", "admin"])
def schedule_create(request):
    initial = {}

    # Предзаполняем данные из параметров URL
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
    """
    Представление для удаления смены.
    Доступно только менеджеру и администратору.
    """
    schedule_obj = get_object_or_404(Schedule, pk=pk)

    if request.method == "POST":
        schedule_obj.delete()
        return redirect("schedule_calendar")

    return render(
        request, "schedule/schedule_confirm_delete.html", {"schedule": schedule_obj}
    )


@role_required(["manager", "admin", "camp_head", "lab_head"])
def schedule_calendar(request):
    # Определяем месяц для отображения
    month = request.GET.get("month")
    if month:
        try:
            current_date = datetime.strptime(month, "%Y-%m").date()
        except ValueError:
            current_date = timezone.now().date()
    else:
        current_date = timezone.now().date()

    # Рассчитываем первый и последний день месяца
    first_day = current_date.replace(day=1)
    if first_day.month == 12:
        next_month = first_day.replace(year=first_day.year + 1, month=1, day=1)
    else:
        next_month = first_day.replace(month=first_day.month + 1, day=1)
    last_day = next_month - timedelta(days=1)

    # Рассчитываем предыдущий и следующий месяц
    prev_month = (first_day - timedelta(days=1)).strftime("%Y-%m")
    next_month = next_month.strftime("%Y-%m")

    # Создаем список недель (понедельник-пятница)
    weeks = []
    current = first_day
    while current <= last_day:
        # Находим понедельник текущей недели
        if current.weekday() == 0:  # 0 = понедельник
            monday = current
        else:
            monday = current - timedelta(days=current.weekday())

        # Пятница - через 4 дня от понедельника
        friday = monday + timedelta(days=4)
        if friday > last_day:
            friday = last_day

        weeks.append((monday, friday))

        # Переходим к следующей неделе
        current = friday + timedelta(days=3)  # Пропускаем выходные

    # Получаем филиалы
    branches = Branch.objects.all()

    # Создаем матрицу расписаний: {branch_id: {week_start: [schedule1, schedule2]}}
    matrix = {}
    for branch in branches:
        branch_schedules = {}
        for week_start, week_end in weeks:
            schedules = Schedule.objects.filter(
                branch=branch, start_date__lte=week_end, end_date__gte=week_start
            )
            branch_schedules[week_start] = schedules
        matrix[branch.id] = branch_schedules

    # Создаем список заголовков для столбцов (недели)
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
        "week_headers": week_headers,  # Добавлено
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
            form.save()
            return HttpResponse(status=200)
        else:
            return render(request, "schedule/schedule_quick_form.html", {"form": form})

    # GET-запрос: создаём форму
    if schedule:
        # Существующая смена — только instance
        form = ScheduleForm(instance=schedule)
    else:
        # Новая смена — используем initial
        initial = {}
        if request.GET.get("branch"):
            initial["branch"] = request.GET["branch"]
        if request.GET.get("week_start") and request.GET.get("week_end"):
            initial["start_date"] = request.GET["week_start"]
            initial["end_date"] = request.GET["week_end"]
        form = ScheduleForm(initial=initial)

    return render(request, "schedule/schedule_quick_form.html", {"form": form})


@role_required(["manager", "admin", "camp_head", "lab_head"])
def schedule_detail(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    user = request.user

    # Проверка прав доступа
    if (
        user.role in ["camp_head", "lab_head"]
        and schedule not in user.schedule_set.all()
    ):
        raise PermissionDenied

    # Генерация списка дат смены
    dates = []
    current_date = schedule.start_date
    while current_date <= schedule.end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)

    # Сотрудники смены
    employees = Employee.objects.filter(schedule=schedule)

    # Ученики смены
    students = Student.objects.filter(schedule=schedule).order_by("full_name")

    # Сбор данных о посещаемости
    attendance = {}
    for student in students:
        for date in dates:
            # Используем get_or_create для получения или создания записи
            att, created = Attendance.objects.get_or_create(
                student=student, date=date, defaults={"present": False}
            )
            key = f"{student.id}_{date}"
            attendance[key] = att.present

    # Платежи
    payments = Payment.objects.filter(schedule=schedule)
    total_payments = payments.aggregate(total=Sum('amount'))['total'] or 0
    payment_form = PaymentForm()
    payment_form.fields["student"].queryset = students

    # Обработка форм
    if request.method == "POST":
        # Проверяем content-type для обработки JSON
        if request.content_type == "application/json":
            try:
                data = json.loads(request.body)
                action = data.get("action")

                if action == "toggle_attendance":
                    student_id = data.get("student_id")
                    date_str = data.get("date")
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

                    student = get_object_or_404(Student, id=student_id)
                    att, created = Attendance.objects.get_or_create(
                        student=student, 
                        date=date_obj, 
                        defaults={"present": False}
                    )
                    att.present = not att.present
                    att.save()
                    
                    # Обновляем кеш посещаемости
                    key = f"{student_id}_{date_str}"
                    attendance[key] = att.present
                    
                    return JsonResponse({
                        "status": "success",
                        "present": att.present,
                        "student_id": student_id,
                        "date": date_str,
                    })
                elif action == "remove_employee":
                    employee_id = data.get("employee_id")
                    employee = get_object_or_404(Employee, id=employee_id)
                    
                    if employee.schedule == schedule:
                        employee.schedule = None
                        employee.save()
                    
                    return JsonResponse({"success": True})
                elif action == "remove_student":
                    student_id = data.get("student_id")
                    student = get_object_or_404(Student, id=student_id)
                    
                    if student.schedule == schedule:
                        student.schedule = None
                        student.save()
                    
                    return JsonResponse({"success": True})
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)})
        
        else:  # Обработка обычных POST-запросов
            action = request.POST.get("action")
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

            if action == "add_employee":
                employee_id = request.POST.get("employee")
                if employee_id:
                    employee = get_object_or_404(Employee, id=employee_id)
                    employee.schedule = schedule
                    employee.save()
                    
                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'employee': {
                                'id': employee.id,
                                'full_name': employee.full_name,
                                'position': employee.get_position_display(),
                                'rate_per_day': employee.rate_per_day,
                            }
                        })
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Сотрудник не выбран'})
                return redirect("schedule_detail", pk=pk)

            elif action == "add_student":
                student_id = request.POST.get("student")
                if student_id:
                    student = get_object_or_404(Student, id=student_id)
                    student.schedule = schedule
                    student.save()
                    
                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'student': {
                                'id': student.id,
                                'full_name': student.full_name,
                                'attendance_count': student.attendance_set.count(),
                                'attendance_type': student.get_attendance_type_display(),
                                'price': student.individual_price or student.default_price,
                                'price_comment': student.price_comment or '',
                            }
                        })
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Ученик не выбран'})
                return redirect("schedule_detail", pk=pk)

            elif action == "add_payment":
                form = PaymentForm(request.POST)
                if form.is_valid():
                    payment = form.save(commit=False)
                    payment.schedule = schedule
                    payment.save()
                    
                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'payment': {
                                'student_full_name': payment.student.full_name,
                                'amount': payment.amount,
                                'date': payment.date.strftime('%Y-%m-%d'),
                                'comment': payment.comment or '',
                            }
                        })
                elif is_ajax:
                    return JsonResponse({
                        'success': False,
                        'errors': form.errors.as_json()
                    }, status=400)
                    
                return redirect("schedule_detail", pk=pk)

    # Получим всех доступных сотрудников и учеников
    all_employees = Employee.objects.all()
    all_students = Student.objects.all()

    context = {
        "schedule": schedule,
        "employees": employees,
        "students": students,
        "payments": payments,
        "total_payments": total_payments,
        "dates": dates,
        "attendance": attendance,
        "all_employees": all_employees,
        "all_students": all_students,
        "payment_form": payment_form,
    }
    return render(request, "schedule/schedule_detail.html", context)

@role_required(["manager", "admin", "camp_head", "lab_head"])
def remove_employee_from_schedule(request, schedule_id, employee_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    employee = get_object_or_404(Employee, pk=employee_id)

    # Проверка прав
    user = request.user
    if (
        user.role in ["camp_head", "lab_head"]
        and schedule not in user.schedule_set.all()
    ):
        raise PermissionDenied

    if employee.schedule == schedule:
        employee.schedule = None
        employee.save()

    return redirect("schedule_detail", pk=schedule_id)


@role_required(["manager", "admin", "camp_head", "lab_head"])
def remove_student_from_schedule(request, schedule_id, student_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    student = get_object_or_404(Student, pk=student_id)

    # Проверка прав
    user = request.user
    if (
        user.role in ["camp_head", "lab_head"]
        and schedule not in user.schedule_set.all()
    ):
        raise PermissionDenied

    if student.schedule == schedule:
        student.schedule = None
        student.save()

    return redirect("schedule_detail", pk=schedule_id)


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
    """
    Отображает список всех смен с основной информацией.
    """
    schedules = Schedule.objects.select_related('branch').all()
    
    # Формируем данные для таблицы
    schedule_data = []
    for schedule in schedules:
        # Находим преподавателей в смене
        teachers = schedule.employee_set.filter(position='teacher')
        teacher_names = ", ".join([t.full_name for t in teachers]) if teachers.exists() else "—"
        
        schedule_data.append({
            'id': schedule.id,
            'name': schedule.name,
            'teacher': teacher_names,
            'theme': schedule.theme,
            'dates': f"{schedule.start_date.strftime('%d.%m.%Y')} – {schedule.end_date.strftime('%d.%m.%Y')}",
            'branch': schedule.branch.name,
        })

    return render(request, 'schedule/schedule_list.html', {'schedule_data': schedule_data})