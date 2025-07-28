import io
import openpyxl
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from weasyprint import HTML

from core.utils import role_required
from students.forms import StudentForm
from .models import Student

def student_list(request):
    students = Student.objects.all()
    return render(request, 'students/student_list.html', {'students': students})

@role_required(['manager', 'admin'])
def student_create(request):
    """
    Представление для создания ученика.
    """
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = StudentForm()

    return render(request, 'students/student_form.html', {'form': form})

@role_required(['manager', 'admin'])
def student_edit(request, pk):
    """
    Представление для редактирования ученика.
    """
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)

    return render(request, 'students/student_form.html', {'form': form})

@role_required(['manager', 'admin'])
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        # Удаляем все связанные объекты перед удалением студента
        student.attendance_set.all().delete()
        student.payments.all().delete()
        
        student.delete()
        return redirect('student_list')

    return render(request, 'students/student_confirm_delete.html', {'student': student})

@role_required(['manager', 'admin'])
def student_export_excel(request):
    students = Student.objects.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ученики"

    ws.append(["ФИО", "Телефон", "Родитель", "Смена", "Тип посещения", "Цена"])

    for student in students:
        ws.append([
            student.full_name,
            student.phone,
            student.parent_name,
            str(student.schedule),
            student.get_attendance_type_display(),
            student.individual_price or student.default_price,
        ])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=students.xlsx'
    return response



@role_required(['manager', 'admin'])
def student_export_pdf(request):
    """
    Выгрузка списка учеников в формате PDF.
    """
    students = Student.objects.all()

    html_string = render_to_string('students/student_pdf_template.html', {'students': students})
    html = HTML(string=html_string)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename=students.pdf'
    html.write_pdf(response)

    return response

