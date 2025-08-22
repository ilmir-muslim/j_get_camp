# schedule/views.py
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
from employees.models import Employee, EmployeeAttendance
from payroll.forms import PaymentForm
from payroll.models import Expense
from students.models import Payment, Student
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
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
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
            return JsonResponse({'success': True})
        else:
            # Возвращаем форму с ошибками
            form_html = render_to_string("schedule/schedule_quick_form.html", {
                "form": form,
                "schedule": schedule
            }, request=request)
            return JsonResponse({'success': False, 'html': form_html})
    
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

    return render(request, "schedule/schedule_quick_form.html", {"form": form, "schedule": schedule})

@role_required(["manager", "admin", "camp_head", "lab_head"])
def schedule_detail(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    user = request.user
    # Проверяем параметр в URL
    from_param = request.GET.get("from", "")
    from_schedule_list = from_param == "list" or "schedule/list" in request.META.get(
        "HTTP_REFERER", ""
    )

    if (
        user.role in ["camp_head", "lab_head"]
        and schedule not in user.schedule_set.all()
    ):
        raise PermissionDenied

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
                defaults={"present": False, "excused": False}
            )
            key = f"{student.id}_{date}"
            if att.present:
                status = 'present'
            elif att.excused:
                status = 'excused'
            else:
                status = 'absent'
            attendance[key] = status

    student_attendance_counts = {}
    for student in students:
        count = Attendance.objects.filter(
            student=student, 
            date__in=dates,
            present=True
        ).count()
        student_attendance_counts[student.id] = count

    employee_attendance = {}
    employee_attendance_counts = {}
    for employee in employees:
        total = 0
        for date in dates:
            # Получаем или создаем запись посещаемости
            att, created = EmployeeAttendance.objects.get_or_create(
                employee=employee,
                date=date,
                defaults={"present": False, "excused": False}
            )
            key = f"{employee.id}_{date}"
            if att.present:
                status = 'present'
                total += 1
            elif att.excused:
                status = 'excused'
            else:
                status = 'absent'
            employee_attendance[key] = status
        employee_attendance_counts[employee.id] = total

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

    expenses = Expense.objects.filter(schedule=schedule)
    total_expenses_sum = expenses.aggregate(total=Sum('amount'))['total'] or 0

    if request.method == "POST":
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

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
                        defaults={"present": False, "excused": False}
                    )

                    if not att.present and not att.excused:
                        att.present = True
                        status = 'present'
                    elif att.present:
                        att.present = False
                        att.excused = True
                        status = 'excused'
                    else:
                        att.excused = False
                        status = 'absent'
                    att.save()

                    key = f"{student_id}_{date_str}"
                    attendance[key] = status

                    total_attendance = Attendance.objects.filter(
                        student=student,
                        date__in=dates,
                        present=True
                    ).count()

                    return JsonResponse({
                        "status": "success",
                        "present": att.present,
                        "excused": att.excused,
                        "total_attendance": total_attendance,
                        "student_id": student_id,
                        "date": date_str,
                    })

                elif "employee_id" in data:
                    employee_id = data.get("employee_id")
                    date_str = data.get("date")
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

                    employee = get_object_or_404(Employee, id=employee_id)
                    att, created = EmployeeAttendance.objects.get_or_create(
                        employee=employee,
                        date=date_obj,
                        defaults={"present": False, "excused": False}
                    )

                    # Циклическое переключение статусов
                    if not att.present and not att.excused:
                        att.present = True
                        status = 'present'
                    elif att.present:
                        att.present = False
                        att.excused = True
                        status = 'excused'
                    else:  # excused: True
                        att.excused = False
                        status = 'absent'
                    att.save()

                    # Пересчет общего количества посещений
                    total_attendance = EmployeeAttendance.objects.filter(
                        employee=employee,
                        date__in=dates,
                        present=True
                    ).count()

                    return JsonResponse({
                        "status": "success",
                        "present": att.present,
                        "excused": att.excused,
                        "total_attendance": total_attendance,
                        "employee_id": employee_id,
                        "date": date_str,
                    })
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)})

        else:
            action = request.POST.get("action")

            if action == "add_employee":
                employee_id = request.POST.get("employee")
                if employee_id:
                    employee = get_object_or_404(Employee, id=employee_id)

                    # Проверка, что сотрудник не добавлен
                    if employee in employees:
                        if is_ajax:
                            return JsonResponse({'success': False, 'error': 'Сотрудник уже добавлен'})
                        return redirect("schedule_detail", pk=pk)

                    employee.schedule = schedule
                    employee.save()

                    # Создание записей посещаемости для каждого дня смены
                    employee_attendance = {}
                    total_attendance = 0
                    for date in dates:
                        att, created = EmployeeAttendance.objects.get_or_create(
                            employee=employee,
                            date=date,
                            defaults={"present": False, "excused": False}
                        )
                        key = f"{employee.id}_{date}"
                        if att.present:
                            status = 'present'
                            total_attendance += 1
                        elif att.excused:
                            status = 'excused'
                        else:
                            status = 'absent'
                        employee_attendance[key] = status

                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'employee': {
                                'id': employee.id,
                                'full_name': employee.full_name,
                                'position': employee.get_position_display(),
                                'rate_per_day': employee.rate_per_day,
                                'attendance': employee_attendance,
                                'total_attendance': total_attendance 
                            }
                        })
                    return redirect("schedule_detail", pk=pk)

            elif action == "add_student":
                student_id = request.POST.get("student")
                if student_id:
                    student = get_object_or_404(Student, id=student_id)

                    # Проверка, что студент не добавлен
                    if student in students:
                        if is_ajax:
                            return JsonResponse({'success': False, 'error': 'Студент уже добавлен'})
                        return redirect("schedule_detail", pk=pk)

                    student.schedule = schedule
                    student.save()

                    # Создание записей посещаемости
                    for date in dates:
                        Attendance.objects.get_or_create(
                            student=student, 
                            date=date, 
                            defaults={"present": False, "excused": False}
                        )

                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'student': {
                                'id': student.id,
                                'full_name': student.full_name,
                                'attendance_type': student.get_attendance_type_display(),
                                'price': student.individual_price or student.default_price,
                            }
                        })
                    return redirect("schedule_detail", pk=pk)

                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Ученик не выбран'})
                return redirect("schedule_detail", pk=pk)

    context = {
        "schedule": schedule,
        "employees": employees,
        "students": students,
        "dates": dates,
        "attendance": attendance,
        "available_employees": available_employees,
        "available_students": available_students,
        "student_attendance_counts": student_attendance_counts,
        "expenses": expenses,
        "employee_attendance": employee_attendance,
        "employee_attendance_counts": employee_attendance_counts,
        "total_expenses_sum": total_expenses_sum,
        "student_total_payments": student_total_payments,
        "total_payments": total_payments,
        "from_schedule_list": from_schedule_list,
    }
    return render(request, "schedule/schedule_detail.html", context)

@require_POST
@role_required(["manager", "admin", "camp_head", "lab_head"])
def remove_employee_from_schedule(request, schedule_id, employee_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    employee = get_object_or_404(Employee, pk=employee_id)

    user = request.user
    if (
        user.role in ["camp_head", "lab_head"]
        and schedule not in user.schedule_set.all()
    ):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    if employee.schedule == schedule:
        employee.schedule = None
        employee.save()

    return JsonResponse({'success': True})

@require_POST
@role_required(["manager", "admin", "camp_head", "lab_head"])
def remove_student_from_schedule(request, schedule_id, student_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    student = get_object_or_404(Student, pk=student_id)

    user = request.user
    if (
        user.role in ["camp_head", "lab_head"]
        and schedule not in user.schedule_set.all()
    ):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    if student.schedule == schedule:
        student.schedule = None
        student.save()

    return JsonResponse({'success': True})

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
    schedules = (
        Schedule.objects.select_related("branch")
        .prefetch_related("employee_set", "student_set")
        .all()
    )

    schedule_data = []
    for schedule in schedules:
        # Получаем начальника лагеря
        camp_head = schedule.employee_set.filter(position="camp_head").first()
        # Получаем начальника лаборатории
        lab_head = schedule.employee_set.filter(position="lab_head").first()
        # Считаем количество студентов
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
    user = request.user
    
    if user.role in ["camp_head", "lab_head"] and schedule not in user.schedule_set.all():
        return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)
    
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
                defaults={"present": False, "excused": False}
            )
            
            # Циклическое переключение: отсутствует -> присутствует -> по уважительной -> отсутствует
            if not att.present and not att.excused:
                att.present = True
                status = 'present'
            elif att.present:
                att.present = False
                att.excused = True
                status = 'excused'
            else:  # excused: True
                att.excused = False
                status = 'absent'
            att.save()
            
            # Пересчитываем общее количество посещений
            total_attendance = Attendance.objects.filter(
                student=student,
                date__range=(schedule.start_date, schedule.end_date),
                present=True
            ).count()
            
            return JsonResponse({
                "status": "success",
                "present": att.present,
                "excused": att.excused,
                "total_attendance": total_attendance,
                "student_id": student_id,
                "date": date_str,
            })
        
        # Обработка сотрудников
        elif "employee_id" in data:
            employee_id = data.get("employee_id")
            date_str = data.get("date")
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            employee = get_object_or_404(Employee, id=employee_id)
            att, created = EmployeeAttendance.objects.get_or_create(
                employee=employee,
                date=date_obj,
                defaults={"present": False, "excused": False}
            )
            
            # Циклическое переключение статусов
            if not att.present and not att.excused:
                att.present = True
                status = 'present'
            elif att.present:
                att.present = False
                att.excused = True
                status = 'excused'
            else:  # excused: True
                att.excused = False
                status = 'absent'
            att.save()
            
            # Пересчет общего количества посещений
            total_attendance = EmployeeAttendance.objects.filter(
                employee=employee,
                date__range=(schedule.start_date, schedule.end_date),
                present=True
            ).count()
            
            return JsonResponse({
                "status": "success",
                "present": att.present,
                "excused": att.excused,
                "total_attendance": total_attendance,
                "employee_id": employee_id,
                "date": date_str,
            })
        
        else:
            return JsonResponse({"status": "error", "message": "Не указан student_id или employee_id"}, status=400)
            
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
