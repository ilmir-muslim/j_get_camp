from ninja import Router
from students.models import Student
from students.schemas import StudentSchema, StudentCreateSchema, StudentUpdateSchema
from django.shortcuts import get_object_or_404

router = Router(tags=["Students"])


@router.get("/", response=list[StudentSchema])
def list_students(request):
    return Student.objects.all()


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
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(student, attr, value)
    student.save()
    return student


@router.delete("/{student_id}/")
def delete_student(request, student_id: int):
    student = get_object_or_404(Student, id=student_id)
    student.delete()
    return {"success": True}
