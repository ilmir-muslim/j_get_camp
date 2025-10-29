# students/views.py
from decimal import Decimal
import io
import json
import openpyxl
import logging
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.db.models import Q
from weasyprint import HTML

from core.utils import role_required
import schedule
from schedule.models import Schedule
from students.forms import BalanceForm, PaymentForm, StudentForm
from .models import Balance, Payment, Student

logger = logging.getLogger(__name__)


def student_list(request):
    students = Student.objects.all()

    # Фильтрация по филиалам для начальников
    if request.user.role in ["camp_head", "lab_head"]:
        # Получаем филиал пользователя
        user_branch = request.user.branch
        if user_branch:
            # Фильтруем учеников по сменам, принадлежащим филиалу пользователя
            students = students.filter(
                Q(schedule__branch=user_branch)
                | Q(schedule__isnull=True)  # Или ученики без смены
            )

    schedules = Schedule.objects.all()

    # Для начальников показываем только смены их филиала
    if request.user.role in ["camp_head", "lab_head"]:
        user_branch = request.user.branch
        if user_branch:
            schedules = schedules.filter(branch=user_branch)

    return render(
        request,
        "students/student_list.html",
        {"students": students, "schedules": schedules},
    )


@role_required(["manager", "admin", "camp_head", "lab_head"])
def student_create(request):
    """
    Представление для создания ученика.
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
    Представление для редактирования ученика.
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
        # Удаляем все связанные объекты
        student.attendance_set.all().delete()
        student.payments.all().delete()
        student.delete()

        # Возвращаем JSON-ответ для AJAX
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

    ws.append(["ФИО", "Телефон", "Родитель", "Смена", "Тип посещения", "Цена"])

    for student in students:
        ws.append(
            [
                student.full_name,
                student.phone,
                student.parent_name,
                str(student.schedule),
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
    """
    Выгрузка списка учеников в формате PDF.
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
    try:
        data = json.loads(request.body)
        # Фильтрация смен по филиалу для начальников
        if request.user.role in ["camp_head", "lab_head"]:
            user_branch = request.user.branch
            if user_branch:
                schedule_id = data.get("schedule")
                if schedule_id:
                    # Проверяем, принадлежит ли выбранная смена филиалу пользователя
                    try:
                        schedule = Schedule.objects.get(
                            id=schedule_id, branch=user_branch
                        )
                    except Schedule.DoesNotExist:
                        return JsonResponse(
                            {"success": False, "error": "Недоступная смена"}, status=400
                        )

        # Преобразуем значение типа посещения если нужно
        if data.get("attendance_type") == "full_day":
            data["attendance_type"] = "full_day"

        # Обработка цены
        if "default_price" in data:
            try:
                data["default_price"] = float(data["default_price"])
            except (TypeError, ValueError):
                return JsonResponse(
                    {"success": False, "error": "Некорректное значение цены"},
                    status=400,
                )

        form = StudentForm(data)
        if form.is_valid():
            student = form.save()

            # Возвращаем те же данные, что и при редактировании
            response_data = {
                "success": True,
                "student": {
                    "id": student.id,
                    "full_name": student.full_name,
                    "phone": student.phone,
                    "parent_name": student.parent_name,
                    "schedule_name": (
                        student.schedule.name if student.schedule else None
                    ),
                    "branch_name": (
                        student.schedule.branch.name
                        if student.schedule and student.schedule.branch
                        else "—"
                    ),
                    "attendance_type_display": student.get_attendance_type_display(),
                    "default_price": str(student.default_price),
                    "individual_price": (
                        str(student.individual_price)
                        if student.individual_price
                        else None
                    ),
                    "price_comment": student.price_comment,
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
                        "schedule_name": (
                            student.schedule.name if student.schedule else None
                        ),
                        "branch_name": (
                            student.schedule.branch.name
                            if student.schedule and student.schedule.branch
                            else "—"
                        ),
                        "attendance_type_display": student.get_attendance_type_display(),
                        "default_price": str(student.default_price),
                        "individual_price": (
                            str(student.individual_price)
                            if student.individual_price
                            else None
                        ),
                        "price_comment": student.price_comment,
                    },
                }
            )
        return JsonResponse({"success": False, "errors": form.errors})

    # GET-запрос — отрисовать форму
    form = StudentForm(instance=student, request=request)
    return render(
        request,
        "students/student_quick_form.html",
        {
            "form": form,
            "student": student,
        },
    )


@require_POST
@role_required(["manager", "admin", "camp_head", "lab_head"])
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
    balance_operations = student.balance_operations.all().order_by("-date")[
        :20
    ]  # Последние 20 операций

    # Преобразуем данные в JSON-совместимый формат
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
    """Проверить достаточно ли средств на балансе для платежа"""
    student = get_object_or_404(Student, id=student_id)
    amount = request.GET.get("amount", 0)
    schedule_id = request.GET.get("schedule_id")

    try:
        amount = Decimal(amount)

        # Проверяем, есть ли существующий платеж для этой смены
        existing_payment = None
        if schedule_id:
            existing_payment = Payment.objects.filter(
                student_id=student_id, schedule_id=schedule_id
            ).first()

        # При редактировании платежа мы сначала "возвращаем" старую сумму
        if existing_payment:
            available_balance = student.current_balance + existing_payment.amount
        else:
            available_balance = student.current_balance

        can_pay = available_balance >= amount

        return JsonResponse(
            {
                "can_pay": can_pay,
                "balance": float(student.current_balance),
                "required": float(amount),
            }
        )
    except (ValueError, TypeError):
        return JsonResponse({"error": "Неверная сумма"}, status=400)


@require_POST
@role_required(["manager", "admin", "camp_head", "lab_head"])
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

        # Создаем операцию списания в Balance
        Balance.objects.create(
            student=student,
            amount=payment.amount,
            operation_type="payment",
            comment=f"Платеж за смену {schedule.name}",
            created_by=request.user,
        )

        # Получаем общую сумму оплаченного за смену (все платежи студента)
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


@role_required(["manager", "admin", "camp_head", "lab_head"])
def add_payment_form(request, student_id):
    """Отображение формы добавления платежа"""
    student = get_object_or_404(Student, id=student_id)
    schedule_id = request.GET.get("schedule_id")

    if not schedule_id:
        return JsonResponse({"success": False, "error": "Не указана смена"}, status=400)

    schedule = get_object_or_404(Schedule, id=schedule_id)

    # Проверяем, есть ли уже платежи
    existing_payments = Payment.objects.filter(student=student, schedule=schedule)
    total_paid = student.get_total_paid_for_schedule(schedule)

    # Определяем текст кнопки
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
