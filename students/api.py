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

router = Router(tags=["Students"])


@router.get("/", response=list[StudentSchema])
def list_students(request):
    students = Student.objects.all()

    # Фильтрация для начальников лагеря/лаборатории
    if request.user.role in ["camp_head", "lab_head"]:
        user_branch = request.user.branch
        if user_branch:
            students = students.filter(
                Q(schedule__branch=user_branch) | Q(schedule__isnull=True)
            )

    # Фильтрация по городу для администратора
    elif request.user.role == "admin":
        user_city = request.user.city
        if user_city:
            students = students.filter(
                Q(schedule__branch__city=user_city) | Q(schedule__isnull=True)
            )

    return students


@router.get("/{student_id}/", response=StudentSchema)
def get_student(request, student_id: int):
    student = get_object_or_404(Student, id=student_id)
    return student


@router.post("/", response=StudentSchema)
def create_student(request, data: StudentCreateSchema):
    student = Student.objects.create(**data.dict())
    return student


@router.patch("/{student_id}/", response=StudentSchema)
def partial_update_student(request, student_id: int, data: StudentUpdateSchema):
    student = get_object_or_404(Student, id=student_id)

    # Обновляем только переданные поля
    update_data = data.dict(exclude_unset=True)
    for attr, value in update_data.items():
        setattr(student, attr, value)

    # Если изменился тип посещения, сбрасываем цену для пересчета
    if "attendance_type" in update_data:
        student.default_price = None

    student.save()  # Автоматический расчет цены в методе save()
    return student


@router.delete("/{student_id}/")
def delete_student(request, student_id: int):
    student = get_object_or_404(Student, id=student_id)

    # Удаляем связанные объекты
    student.attendance_set.all().delete()
    student.payments.all().delete()

    student.delete()
    return {"success": True}


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


@router.get("/{student_id}/payments/", response=list[PaymentSchema])
def list_payments(request, student_id: int):
    student = get_object_or_404(Student, id=student_id)
    return student.payments.all()


@router.post("/{student_id}/payments/", response=PaymentSchema)
def create_payment(request, student_id: int, data: PaymentCreateSchema):
    student = get_object_or_404(Student, id=student_id)
    schedule = get_object_or_404(Schedule, id=data.schedule_id)
    payment = Payment.objects.create(student=student, schedule=schedule, **data.dict())
    return payment


@router.patch("/{student_id}/payments/{payment_id}/", response=PaymentSchema)
def update_payment(
    request, student_id: int, payment_id: int, data: PaymentUpdateSchema
):
    student = get_object_or_404(Student, id=student_id)
    payment = get_object_or_404(Payment, id=payment_id, student=student)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(payment, attr, value)
    payment.save()
    return payment


@router.delete("/{student_id}/payments/{payment_id}/")
def delete_payment(request, student_id: int, payment_id: int):
    student = get_object_or_404(Student, id=student_id)
    payment = get_object_or_404(Payment, id=payment_id, student=student)
    payment.delete()
    return {"success": True}


# API для работы с отрядами
@router.get("/squads/", response=list[SquadSchema])
def list_squads(request):
    squads = Squad.objects.all()

    # Фильтрация для начальников лагеря/лаборатории
    if request.user.role in ["camp_head", "lab_head"]:
        user_branch = request.user.branch
        if user_branch:
            squads = squads.filter(schedule__branch=user_branch)

    # Фильтрация по городу для администратора
    elif request.user.role == "admin":
        user_city = request.user.city
        if user_city:
            squads = squads.filter(schedule__branch__city=user_city)

    return squads
