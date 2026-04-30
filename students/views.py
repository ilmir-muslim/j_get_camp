from decimal import Decimal
import io
import json
import openpyxl
import logging
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST, require_http_methods, require_GET
from django.utils import timezone
from django.db.models import Q
from weasyprint import HTML

from core.utils import role_required
from schedule.models import Schedule
from students.forms import (
    BalanceForm,
    PaymentForm,
    SquadForm,
    StudentForm,
    StudentScheduleForm,
)
from .models import Balance, Payment, Student, Squad, StudentSchedule

logger = logging.getLogger(__name__)


def student_list(request):
    students = Student.objects.all()

    # Фильтрация по доступным сменам
    if request.user.role in ["camp_head", "lab_head"]:
        user_branch = request.user.branch
        if user_branch:
            students = students.filter(
                Q(schedules__branch=user_branch) | Q(schedules__isnull=True)
            ).distinct()
    elif request.user.role == "admin":
        user_city = request.user.city
        if user_city:
            students = students.filter(
                Q(schedules__branch__city=user_city) | Q(schedules__isnull=True)
            ).distinct()

    # Список смен больше не нужен в контексте, т.к. мы убрали поле выбора смены из формы создания
    return render(
        request,
        "students/student_list.html",
        {"students": students},
    )


@role_required(["manager", "admin", "camp_head", "lab_head"])
def student_create(request):
    """
    Представление для создания ученика (базовые данные).
    """
    if request.method == "POST":
        form = StudentForm(request.POST, request=request)
        if form.is_valid():
            form.save()
            return redirect("student_list")
    else:
        form = StudentForm(request=request)

    return render(request, "students/student_form.html", {"form": form})


@role_required(["manager", "admin", "camp_head", "lab_head"])
def student_edit(request, pk):
    """
    Представление для редактирования персональных данных ученика.
    """
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        form = StudentForm(request.POST, instance=student, request=request)
        if form.is_valid():
            form.save()
            return redirect("student_list")
    else:
        form = StudentForm(instance=student, request=request)

    return render(request, "students/student_form.html", {"form": form})


@role_required(["manager", "admin", "camp_head", "lab_head"])
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        # Удаляем связанные данные
        student.attendance_set.all().delete()
        student.payments.all().delete()
        student.studentschedule_set.all().delete()
        student.delete()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return redirect("student_list")

    return render(request, "students/student_confirm_delete.html", {"student": student})


@role_required(["manager", "admin", "camp_head", "lab_head"])
def student_export_excel(request):
    # Экспорт базовых данных + список смен
    students = Student.objects.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ученики"

    ws.append(["ФИО", "Телефон", "Родитель", "Смены"])

    for student in students:
        schedules_str = ", ".join(str(s) for s in student.schedules.all())
        ws.append(
            [
                student.full_name,
                student.phone,
                student.parent_name,
                schedules_str,
            ]
        )

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = "attachment; filename=students.xlsx"
    return response


@role_required(["manager", "admin", "camp_head", "lab_head"])
def student_export_pdf(request):
    """
    Выгрузка списка учеников в формате PDF (базовые данные).
    """
    students = Student.objects.all()

    html_string = render_to_string(
        "students/student_pdf_template.html", {"students": students}
    )
    html = HTML(string=html_string)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=students.pdf"
    html.write_pdf(response)

    return response


@require_POST
def student_create_ajax(request):
    """
    Создание ученика через AJAX (без параметров смены).
    Может сразу привязать к смене, если передан schedule_id.
    Поддерживает force_create для игнорирования дубликатов.
    """
    try:
        data = json.loads(request.body)
        force_create = data.get("force_create", False)

        # Проверка дубликатов (только если не принудительное создание)
        if not force_create:
            full_name = data.get("full_name", "").strip()
            if full_name:
                duplicates = Student.objects.filter(full_name__iexact=full_name)
                if duplicates.exists():
                    dup_list = [
                        {
                            "id": d.id,
                            "full_name": d.full_name,
                            "phone": d.phone,
                            "parent_name": d.parent_name,
                        }
                        for d in duplicates
                    ]
                    return JsonResponse(
                        {
                            "success": False,
                            "duplicates": dup_list,
                            "message": "Найдены ученики с таким же ФИО, рекомендуется выбрать ученика из списка существующих. Создать нового всё равно?",
                        }
                    )

        # Проверка прав на смену, если она указана
        schedule = None
        schedule_id = data.get("schedule_id")
        if schedule_id:
            schedule = get_object_or_404(Schedule, id=schedule_id)
            user = request.user
            if user.role == "admin" and user.city and schedule.branch.city != user.city:
                return JsonResponse(
                    {"success": False, "error": "Доступ запрещен"}, status=403
                )
            elif (
                user.role in ["camp_head", "lab_head"]
                and schedule.branch != user.branch
            ):
                return JsonResponse(
                    {"success": False, "error": "Доступ запрещен"}, status=403
                )

        # Формируем данные для формы (только персональные поля)
        form_data = {
            "full_name": data.get("full_name"),
            "phone": data.get("phone", ""),
            "parent_name": data.get("parent_name", ""),
        }
        if "squad" in data and data["squad"]:
            form_data["squad"] = data["squad"]

        form = StudentForm(form_data, request=request)
        if form.is_valid():
            student = form.save()

            # Если указана смена, создаём запись StudentSchedule
            if schedule:
                attendance_type = data.get("attendance_type", "full_day")
                default_price = data.get("default_price", 11400)
                individual_price = data.get("individual_price")
                price_comment = data.get("price_comment", "")

                StudentSchedule.objects.create(
                    student=student,
                    schedule=schedule,
                    attendance_type=attendance_type,
                    default_price=default_price,
                    individual_price=individual_price,
                    price_comment=price_comment,
                )
                student.charge_for_schedule(schedule, request.user)

            response_data = {
                "success": True,
                "student": {
                    "id": student.id,
                    "full_name": student.full_name,
                    "phone": student.phone,
                    "parent_name": student.parent_name,
                    "squad_name": student.squad.name if student.squad else None,
                    "squad_id": student.squad.id if student.squad else None,
                    # дополнительные поля, если нужны
                },
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Неверный формат JSON"}, status=400
        )


@role_required(["manager", "admin", "camp_head", "lab_head"])
def student_quick_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    schedule_id = request.GET.get("schedule_id") or request.POST.get("schedule_id")

    if not schedule_id:
        return JsonResponse(
            {"success": False, "error": "schedule_id обязателен"}, status=400
        )

    schedule = get_object_or_404(Schedule, id=schedule_id)

    # Получаем или создаём запись StudentSchedule
    student_schedule, created = StudentSchedule.objects.get_or_create(
        student=student,
        schedule=schedule,
        defaults={"attendance_type": "full_day", "default_price": 11400},
    )

    if request.method == "POST":
        # Форма для персональных данных студента
        student_form = StudentForm(request.POST, instance=student, request=request)
        # Форма для настроек в смене
        schedule_form = StudentScheduleForm(request.POST, instance=student_schedule)

        if student_form.is_valid() and schedule_form.is_valid():
            student_form.save()
            schedule_form.save()

            # Возвращаем обновлённые данные для JS
            return JsonResponse(
                {
                    "success": True,
                    "student": {
                        "id": student.id,
                        "full_name": student.full_name,
                        "phone": student.phone,
                        "parent_name": student.parent_name,
                        "schedule_name": schedule.name,
                        "branch_name": schedule.branch.name,
                        "squad_id": student.squad.id if student.squad else None,
                        "squad_name": student.squad.name if student.squad else None,
                        "squad_leader_name": (
                            student.squad.leader.full_name
                            if student.squad and student.squad.leader
                            else None
                        ),
                        "attendance_type": student_schedule.get_attendance_type_display(),
                        "default_price": str(student_schedule.default_price),
                        "individual_price": (
                            str(student_schedule.individual_price)
                            if student_schedule.individual_price
                            else None
                        ),
                        "price_comment": student_schedule.price_comment,
                        "special_notes": student_schedule.special_notes,
                    },
                }
            )
        else:
            errors = {}
            errors.update(student_form.errors)
            errors.update(schedule_form.errors)
            return JsonResponse({"success": False, "errors": errors}, status=400)

    # GET: отображаем обе формы
    student_form = StudentForm(instance=student, request=request)
    schedule_form = StudentScheduleForm(instance=student_schedule)

    context = {
        "student_form": student_form,
        "schedule_form": schedule_form,
        "student": student,
        "schedule": schedule,
        "schedule_id": schedule_id,
    }
    return render(request, "students/student_quick_form.html", context)


@require_POST
@role_required(["manager", "admin"])
def add_balance(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    form = BalanceForm(request.POST)

    if form.is_valid():
        try:
            balance = form.save(commit=False)
            balance.student = student
            balance.operation_type = "deposit"
            balance.created_by = request.user
            balance.save()

            return JsonResponse(
                {
                    "success": True,
                    "new_balance": str(student.current_balance),
                    "message": "Баланс успешно пополнен",
                }
            )
        except Exception as e:
            logger.exception("Ошибка при пополнении баланса")
            return JsonResponse(
                {"success": False, "error": f"Ошибка при сохранении: {str(e)}"},
                status=500,
            )

    return JsonResponse({"success": False, "errors": form.errors.as_json()}, status=400)


@require_GET
@role_required(["manager", "admin", "camp_head", "lab_head"])
def get_balance_history(request, student_id):
    """Получить историю операций по балансу студента"""
    student = get_object_or_404(Student, id=student_id)
    balance_operations = student.balance_operations.all().order_by("-date")[:20]

    operations_data = []
    for operation in balance_operations:
        operations_data.append(
            {
                "date": operation.date.strftime("%d.%m.%Y %H:%M"),
                "operation_type": operation.get_operation_type_display(),
                "amount": str(operation.amount),
                "comment": operation.comment or "",
                "created_by": (
                    operation.created_by.get_full_name()
                    if operation.created_by
                    else "Система"
                ),
            }
        )

    return JsonResponse({"success": True, "operations": operations_data})


@require_GET
@role_required(["manager", "admin", "camp_head", "lab_head"])
def check_balance(request, student_id):
    """Проверить баланс студента (без блокировки платежа)"""
    student = get_object_or_404(Student, id=student_id)
    try:
        amount = Decimal(request.GET.get("amount", 0))
    except (ValueError, TypeError):
        return JsonResponse({"error": "Неверная сумма"}, status=400)

    return JsonResponse(
        {
            "can_pay": True,
            "balance": float(student.current_balance),
            "required": 0,
        }
    )


@require_POST
@role_required(["manager", "admin"])
def add_payment(request, student_id):
    """Обработка добавления платежа"""
    student = get_object_or_404(Student, id=student_id)
    schedule_id = request.GET.get("schedule_id")
    if not schedule_id:
        return JsonResponse({"success": False, "error": "Не указана смена"}, status=400)

    schedule = get_object_or_404(Schedule, id=schedule_id)
    form = PaymentForm(request.POST)

    if form.is_valid():
        payment = form.save(commit=False)
        payment.student = student
        payment.schedule = schedule
        payment.save()

        Balance.objects.create(
            student=student,
            amount=payment.amount,
            operation_type="payment",
            comment=f"Платеж за смену {schedule.name} (ID {schedule.id})",
            created_by=request.user,
        )

        total_paid = student.get_total_paid_for_schedule(schedule)
        return JsonResponse(
            {
                "success": True,
                "message": "Платеж успешно добавлен",
                "student_id": student_id,
                "schedule_id": schedule_id,
                "payment_amount": float(payment.amount),
                "total_paid": float(total_paid),
            }
        )
    else:
        return JsonResponse({"success": False, "errors": form.errors}, status=400)


@require_http_methods(["POST", "DELETE"])
@role_required(["manager", "admin"])
def delete_payment(request, student_id, payment_id):
    """Удаление платежа и связанной записи баланса"""
    student = get_object_or_404(Student, id=student_id)
    payment = get_object_or_404(Payment, id=payment_id, student=student)

    balance = Balance.objects.filter(
        student=student,
        operation_type="payment",
        amount=payment.amount,
        comment__contains=f"(ID {payment.schedule.id})",
    ).first()
    if balance:
        balance.delete()

    payment.delete()

    total_paid = student.get_total_paid_for_schedule(payment.schedule)
    current_balance = student.current_balance

    return JsonResponse(
        {
            "success": True,
            "total_paid": float(total_paid),
            "current_balance": float(current_balance),
            "schedule_id": payment.schedule.id,
            "student_id": student.id,
        }
    )


@require_GET
@role_required(["manager", "admin", "camp_head", "lab_head"])
def payment_history(request, student_id):
    """Получить историю платежей студента для конкретной смены"""
    student = get_object_or_404(Student, id=student_id)
    schedule_id = request.GET.get("schedule_id")

    payments = Payment.objects.filter(student=student)
    if schedule_id:
        payments = payments.filter(schedule_id=schedule_id)

    payments = payments.order_by("-date")

    html = render_to_string(
        "students/payment_history_partial.html",
        {"payments": payments, "student": student},
    )

    return JsonResponse({"success": True, "html": html})


@require_POST
@role_required(["manager", "admin", "camp_head", "lab_head"])
def student_payment_info(request, student_id):
    """Получить информацию о платежах студента для конкретной смены"""
    student = get_object_or_404(Student, id=student_id)
    schedule_id = request.GET.get("schedule_id")

    total_paid = student.get_total_paid_for_schedule(schedule_id) if schedule_id else 0

    return JsonResponse(
        {
            "success": True,
            "student_id": student_id,
            "student_name": student.full_name,
            "total_paid": total_paid,
            "balance": student.current_balance,
        }
    )


@role_required(["manager", "admin"])
def add_payment_form(request, student_id):
    """Отображение формы добавления платежа"""
    student = get_object_or_404(Student, id=student_id)
    schedule_id = request.GET.get("schedule_id")

    if not schedule_id:
        return JsonResponse({"success": False, "error": "Не указана смена"}, status=400)

    schedule = get_object_or_404(Schedule, id=schedule_id)

    # Получаем или создаём StudentSchedule для текущей пары
    student_schedule, _ = StudentSchedule.objects.get_or_create(
        student=student,
        schedule=schedule,
        defaults={"attendance_type": "full_day", "default_price": 11400},
    )

    existing_payments = Payment.objects.filter(student=student, schedule=schedule)
    total_paid = student.get_total_paid_for_schedule(schedule)

    button_text = "Добавить платеж" if existing_payments.exists() else "Создать платеж"

    form = PaymentForm(initial={"date": timezone.now().date()})

    return render(
        request,
        "students/payment_form.html",
        {
            "form": form,
            "student": student,
            "schedule": schedule,
            "student_schedule": student_schedule,
            "button_text": button_text,
            "total_paid": total_paid,
        },
    )


@require_GET
@role_required(["manager", "admin", "camp_head", "lab_head"])
def get_squad(request, pk):
    """Получить информацию об отряде с вожатым"""
    squad = get_object_or_404(Squad, pk=pk)

    squad_data = {
        "id": squad.id,
        "name": squad.name,
        "schedule_id": squad.schedule.id,
        "leader": None,
    }
    if squad.leader:
        squad_data["leader"] = {
            "id": squad.leader.id,
            "full_name": squad.leader.full_name,
            "position": squad.leader.position.name if squad.leader.position else "",
        }

    return JsonResponse(squad_data)


@role_required(["manager", "admin", "camp_head", "lab_head"])
def squad_create(request, schedule_id):
    """Создание отряда для конкретной смены"""
    schedule = get_object_or_404(Schedule, pk=schedule_id)

    if request.method == "POST":
        form = SquadForm(request.POST, schedule=schedule)
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
                        "roman_name": squad.roman_name,
                        "leader_id": squad.leader.id if squad.leader else None,
                        "leader_name": squad.leader.full_name if squad.leader else None,
                    },
                }
            )
        else:
            return JsonResponse({"success": False, "errors": form.errors})

    form = SquadForm(schedule=schedule)
    return render(
        request, "students/squad_form.html", {"form": form, "schedule": schedule}
    )
