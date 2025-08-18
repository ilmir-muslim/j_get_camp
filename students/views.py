import io
import json
import openpyxl
import logging
from django import forms
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from weasyprint import HTML

from core.utils import role_required
from schedule.models import Schedule
from students.forms import PaymentForm, StudentForm
from .models import Payment, Student

logger = logging.getLogger(__name__)

def student_list(request):
    students = Student.objects.all()
    return render(request, "students/student_list.html", {"students": students})


@role_required(["manager", "admin"])
def student_create(request):
    """
    Представление для создания ученика.
    """
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("student_list")
    else:
        form = StudentForm()

    return render(request, "students/student_form.html", {"form": form})


@role_required(["manager", "admin"])
def student_edit(request, pk):
    """
    Представление для редактирования ученика.
    """
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect("student_list")
    else:
        form = StudentForm(instance=student)

    return render(request, "students/student_form.html", {"form": form})


@role_required(["manager", "admin"])
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


@role_required(["manager", "admin"])
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


@role_required(["manager", "admin"])
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

        # Извлекаем schedule_id из данных (если есть)
        schedule_id = data.pop("schedule_id", None)

        form = StudentForm(data)
        if form.is_valid():
            student = form.save()

            # Создаем платеж если указана смена
            payment_data = None
            if schedule_id:
                try:
                    schedule = Schedule.objects.get(id=schedule_id)
                    amount = student.individual_price or student.default_price

                    payment = Payment.objects.create(
                        student=student,
                        schedule=schedule,
                        amount=amount,
                        date=timezone.now().date(),
                        comment="Автоматически созданный платеж",
                    )
                    payment_data = {
                        "id": payment.id,
                        "amount": str(payment.amount),
                        "date": payment.date.strftime("%Y-%m-%d"),
                    }
                except Schedule.DoesNotExist:
                    # Не прерываем создание студента, но логируем ошибку
                    pass
                except Exception as e:
                    # Не прерываем создание студента, но логируем ошибку
                    pass

            # Возвращаем больше данных о созданном студенте
            response_data = {
                "success": True,
                "student": {
                    "id": student.id,
                    "full_name": student.full_name,
                    "attendance_type_display": student.get_attendance_type_display(),
                    "default_price": str(student.default_price),
                    "individual_price": (
                        str(student.individual_price)
                        if student.individual_price
                        else None
                    ),
                },
            }

            # Добавляем информацию о платеже если он был создан
            if payment_data:
                response_data["payment"] = payment_data

            return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Неверный формат JSON"}, status=400
        )


@role_required(["manager", "admin"])
def student_quick_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            student = form.save()
            return JsonResponse(
                {
                    "success": True,
                    "student": {
                        "id": student.id,
                        "full_name": student.full_name,
                        "attendance_type_display": student.get_attendance_type_display(),
                        "default_price": str(student.default_price),
                        "individual_price": (
                            str(student.individual_price)
                            if student.individual_price
                            else None
                        ),
                    },
                }
            )
        return JsonResponse({"success": False, "errors": form.errors})

    # GET-запрос — отрисовать форму
    form = StudentForm(instance=student)
    return render(
        request,
        "students/student_quick_form.html",
        {
            "form": form,
            "student": student,
        },
    )


def create_payment(request):
    logger.info(f"Create payment request: {request.method}")

    if request.method == "POST":
        try:
            form = PaymentForm(request.POST)
            logger.info(f"Form data: {request.POST}")

            if form.is_valid():
                student = form.cleaned_data["student"]
                schedule = form.cleaned_data["schedule"]

                # Поиск существующего платежа
                existing_payment = Payment.objects.filter(
                    student=student, schedule=schedule
                ).first()

                if existing_payment:
                    # Обновление существующего платежа
                    existing_payment.amount = form.cleaned_data["amount"]
                    existing_payment.date = form.cleaned_data["date"]
                    existing_payment.comment = form.cleaned_data["comment"]
                    existing_payment.save()
                    logger.info(f"Updated payment: {existing_payment.id}")
                    return JsonResponse(
                        {"success": True, "payment_id": existing_payment.id}
                    )
                else:
                    # Создание нового платежа
                    payment = form.save()
                    logger.info(f"Created new payment: {payment.id}")
                    return JsonResponse({"success": True, "payment_id": payment.id})

            # Форма не валидна
            logger.warning(f"Form errors: {form.errors}")
            html = render_to_string(
                "students/payment_form.html", {"form": form}, request=request
            )
            return JsonResponse({"success": False, "html": html}, status=400)

        except Exception as e:
            logger.exception("Error in create_payment")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    # GET-запрос
    try:
        student_id = request.GET.get("student_id")
        schedule_id = request.GET.get("schedule_id")

        # Поиск существующего платежа
        payment = Payment.objects.filter(
            student_id=student_id, schedule_id=schedule_id
        ).first()

        if payment:
            form = PaymentForm(instance=payment)
        else:
            initial = {
                "student": student_id,
                "schedule": schedule_id,
                "date": timezone.now().date(),
            }
            form = PaymentForm(initial=initial)

        return render(request, "students/payment_form.html", {"form": form})

    except Exception as e:
        logger.exception("Error in GET create_payment")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def edit_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    form = PaymentForm(instance=payment)
    return render(request, "students/payment_form.html", {"form": form})
