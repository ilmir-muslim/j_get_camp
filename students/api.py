from ninja import Router
from schedule.models import Schedule
from students.models import Attendance, Payment, Student, Squad
from students.schemas import (
    AttendanceCreateSchema,
    AttendanceSchema,
    AttendanceUpdateSchema,
    PaymentCreateSchema,
    PaymentSchema,
    PaymentUpdateSchema,
    StudentSchema,
    StudentCreateSchema,
    StudentUpdateSchema,
    SquadSchema,
)
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.exceptions import PermissionDenied

router = Router(tags=["Students"])


@router.get("/", response=list[StudentSchema])
def list_students(request):
    students = Student.objects.all()

    # Фильтрация для начальников лагеря/лаборатории и администраторов
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

    return students


@router.get("/{student_id}/", response=StudentSchema)
def get_student(request, student_id: int):
    student = get_object_or_404(Student, id=student_id)
    return student


@router.post("/", response=StudentSchema)
def create_student(request, data: StudentCreateSchema):
    # Создаём студента без привязки к конкретной смене
    student = Student.objects.create(
        full_name=data.full_name,
        phone=data.phone,
        parent_name=data.parent_name,
        attendance_type=data.attendance_type,
        default_price=data.default_price,
        individual_price=data.individual_price,
        price_comment=data.price_comment,
        special_notes=data.special_notes,
    )
    return student


@router.patch("/{student_id}/", response=StudentSchema)
def partial_update_student(request, student_id: int, data: StudentUpdateSchema):
    student = get_object_or_404(Student, id=student_id)

    update_data = data.dict(exclude_unset=True)
    for attr, value in update_data.items():
        setattr(student, attr, value)

    # Если изменился тип посещения, сбрасываем цену для пересчета
    if "attendance_type" in update_data:
        student.default_price = None

    student.save()
    return student


@router.delete("/{student_id}/")
def delete_student(request, student_id: int):
    student = get_object_or_404(Student, id=student_id)

    # Удаляем связанные объекты
    student.attendance_set.all().delete()
    student.payments.all().delete()
    student.delete()
    return {"success": True}


# ================================
# Посещаемость
# ================================
@router.get("/{student_id}/attendance/", response=list[AttendanceSchema])
def list_attendance(request, student_id: int):
    student = get_object_or_404(Student, id=student_id)
    return student.attendance_set.all()


@router.post("/{student_id}/attendance/", response=AttendanceSchema)
def create_attendance(request, student_id: int, data: AttendanceCreateSchema):
    student = get_object_or_404(Student, id=student_id)
    attendance = Attendance.objects.create(student=student, **data.dict())
    return attendance


@router.patch("/attendance/{attendance_id}/", response=AttendanceSchema)
def update_attendance(request, attendance_id: int, data: AttendanceUpdateSchema):
    attendance = get_object_or_404(Attendance, id=attendance_id)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(attendance, attr, value)
    attendance.save()
    return attendance


@router.delete("/attendance/{attendance_id}/")
def delete_attendance(request, attendance_id: int):
    attendance = get_object_or_404(Attendance, id=attendance_id)
    attendance.delete()
    return {"success": True}


# ================================
# Платежи
# ================================
@router.get("/{student_id}/payments/", response=list[PaymentSchema])
def list_payments(request, student_id: int):
    student = get_object_or_404(Student, id=student_id)
    return student.payments.all()


@router.post("/{student_id}/payments/", response=PaymentSchema)
def create_payment(request, student_id: int, data: PaymentCreateSchema):
    if request.user.role in ["camp_head", "lab_head"]:
        raise PermissionDenied
    student = get_object_or_404(Student, id=student_id)
    schedule = get_object_or_404(Schedule, id=data.schedule_id)
    payment = Payment.objects.create(
        student=student,
        schedule=schedule,
        amount=data.amount,
        date=data.date,
        comment=data.comment,
    )
    return payment


@router.patch("/{student_id}/payments/{payment_id}/", response=PaymentSchema)
def update_payment(
    request, student_id: int, payment_id: int, data: PaymentUpdateSchema
):
    if request.user.role in ["camp_head", "lab_head"]:
        raise PermissionDenied
    student = get_object_or_404(Student, id=student_id)
    payment = get_object_or_404(Payment, id=payment_id, student=student)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(payment, attr, value)
    payment.save()
    return payment


@router.delete("/{student_id}/payments/{payment_id}/")
def delete_payment(request, student_id: int, payment_id: int):
    if request.user.role in ["camp_head", "lab_head"]:
        raise PermissionDenied
    student = get_object_or_404(Student, id=student_id)
    payment = get_object_or_404(Payment, id=payment_id, student=student)
    payment.delete()
    return {"success": True}


# ================================
# Отряды
# ================================
@router.get("/squads/", response=list[SquadSchema])
def list_squads(request, schedule_id: int = None):
    squads = Squad.objects.all()

    if schedule_id:
        squads = squads.filter(schedule_id=schedule_id)

    # Фильтрация по правам доступа
    if request.user.role in ["camp_head", "lab_head"]:
        user_branch = request.user.branch
        if user_branch:
            squads = squads.filter(schedule__branch=user_branch)
    elif request.user.role == "admin":
        user_city = request.user.city
        if user_city:
            squads = squads.filter(schedule__branch__city=user_city)

    return squads


@router.get("/squads/{squad_id}/", response=SquadSchema)
def get_squad(request, squad_id: int):
    squad = get_object_or_404(Squad, id=squad_id)

    # Проверка доступа
    user = request.user
    if user.role == "admin" and user.city:
        if squad.schedule.branch.city != user.city:
            from django.http import JsonResponse

            return JsonResponse({"error": "Доступ запрещен"}, status=403)
    elif user.role in ["camp_head", "lab_head"]:
        if squad.schedule.branch != user.branch:
            from django.http import JsonResponse

            return JsonResponse({"error": "Доступ запрещен"}, status=403)

    return squad
