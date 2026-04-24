# students/views.py
from decimal import Decimal
import io
import json
import logging
import openpyxl

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST, require_http_methods, require_GET
from django.utils import timezone
from django.db.models import Q
from weasyprint import HTML

from core.utils import role_required
from schedule.models import Schedule
from students.forms import BalanceForm, PaymentForm, SquadForm, StudentForm
from .models import Balance, Payment, Student, Squad

logger = logging.getLogger(__name__)


def student_list(request):
    students = Student.objects.all()

    # Фильтрация по доступным сменам для начальников/админов по городу/филиалу
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

    schedules = Schedule.objects.all()
    if request.user.role in ["camp_head", "lab_head"]:
        user_branch = request.user.branch
        if user_branch:
            schedules = schedules.filter(branch=user_branch)
    elif request.user.role == "admin":
        user_city = request.user.city
        if user_city:
            schedules = schedules.filter(branch__city=user_city)

    return render(
        request,
        "students/student_list.html",
        {"students": students, "schedules": schedules},
    )


@role_required(["manager", "admin", "camp_head", "lab_head"])
def student_create(request):
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
        student.attendance_set.all().delete()
        student.payments.all().delete()
        student.delete()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return redirect("student_list")

    return render(request, "students/student_confirm_delete.html", {"student": student})


@role_required(["manager", "admin", "camp_head", "lab_head"])
def student_export_excel(request):
    students = Student.objects.all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ученики"

    ws.append(["ФИО", "Телефон", "Родитель", "Смены", "Тип посещения", "Цена"])

    for student in students:
        schedules_str = ", ".join(str(s) for s in student.schedules.all())
        ws.append(
            [
                student.full_name,
                student.phone,
                student.parent_name,
                schedules_str,
                student.get_attendance_type_display(),
                student.individual_price or student.default_price,
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
    try:
        data = json.loads(request.body)

        # Проверка доступа к смене, если указан schedule_id
        schedule_id = data.get("schedule_id")
        schedule = None
        if schedule_id:
            schedule = get_object_or_404(Schedule, id=schedule_id)
            user = request.user
            if user.role in ["camp_head", "lab_head"] and user.branch:
                if schedule.branch != user.branch:
                    return JsonResponse(
                        {"success": False, "error": "Недоступная смена"}, status=400
                    )
            elif user.role == "admin" and user.city:
                if schedule.branch.city != user.city:
                    return JsonResponse(
                        {"success": False, "error": "Недоступная смена"}, status=400
                    )

        # Убираем из данных schedule_id, так как модель Student больше не содержит этого поля
        data.pop("schedule_id", None)
        data.pop("schedule", None)  # на всякий случай

        if data.get("attendance_type") == "full_day":
            data["attendance_type"] = "full_day"

        form = StudentForm(data, request=request)
        if form.is_valid():
            student = form.save()

            # Если была указана смена, добавляем ученика в неё и списываем стоимость
            if schedule:
                student.schedules.add(schedule)
                student.charge_for_schedule(schedule, request.user)

            response_data = {
                "success": True,
                "student": {
                    "id": student.id,
                    "full_name": student.full_name,
                    "phone": student.phone,
                    "parent_name": student.parent_name,
                    "attendance_type_display": student.get_attendance_type_display(),
                    "default_price": str(student.default_price),
                    "individual_price": (
                        str(student.individual_price)
                        if student.individual_price
                        else None
                    ),
                    "squad_name": student.squad.name if student.squad else None,
                    "squad_id": student.squad.id if student.squad else None,
                    "squad_leader_name": (
                        student.squad.leader.full_name
                        if student.squad and student.squad.leader
                        else None
                    ),
                    "price_comment": student.price_comment,
                    "special_notes": student.special_notes,
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

    if request.method == "POST":
        form = StudentForm(request.POST, instance=student, request=request)
        if form.is_valid():
            student = form.save()
            return JsonResponse(
                {
                    "success": True,
                    "student": {
                        "id": student.id,
                        "full_name": student.full_name,
                        "phone": student.phone,
                        "parent_name": student.parent_name,
                        "attendance_type_display": student.get_attendance_type_display(),
                        "default_price": str(student.default_price),
                        "individual_price": (
                            str(student.individual_price)
                            if student.individual_price
                            else None
                        ),
                        "squad_name": student.squad.name if student.squad else None,
                        "squad_id": student.squad.id if student.squad else None,
                        "squad_leader_name": (
                            student.squad.leader.full_name
                            if student.squad and student.squad.leader
                            else None
                        ),
                        "price_comment": student.price_comment,
                        "special_notes": student.special_notes,
                    },
                }
            )
        return JsonResponse({"success": False, "errors": form.errors})

    form = StudentForm(instance=student, request=request)
    return render(
        request,
        "students/student_quick_form.html",
        {"form": form, "student": student},
    )


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
    student = get_object_or_404(Student, id=student_id)
    amount = request.GET.get("amount", 0)

    try:
        amount = Decimal(amount)
        # В текущей логике оплаты проверка не требуется, возвращаем true
        return JsonResponse(
            {
                "can_pay": True,
                "balance": float(student.current_balance),
                "required": 0,
            }
        )
    except (ValueError, TypeError):
        return JsonResponse({"error": "Неверная сумма"}, status=400)


@require_POST
@role_required(["manager", "admin"])
def add_payment(request, student_id):
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
    student = get_object_or_404(Student, id=student_id)
    schedule_id = request.GET.get("schedule_id")

    if not schedule_id:
        return JsonResponse({"success": False, "error": "Не указана смена"}, status=400)

    schedule = get_object_or_404(Schedule, id=schedule_id)

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
            "button_text": button_text,
            "total_paid": total_paid,
        },
    )


@require_GET
@role_required(["manager", "admin", "camp_head", "lab_head"])
def get_squad(request, pk):
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
