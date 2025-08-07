import io
import json
import openpyxl
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.http import JsonResponse
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
        # Удаляем все связанные объекты
        student.attendance_set.all().delete()
        student.payments.all().delete()
        student.delete()
        
        # Возвращаем JSON-ответ для AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
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

@require_POST
def student_create_ajax(request):
    try:
        data = json.loads(request.body)
        # Преобразуем значение типа посещения если нужно
        if data.get('attendance_type') == 'full_day':
            data['attendance_type'] = 'full_day'
            
        # Обработка цены
        if 'default_price' in data:
            try:
                data['default_price'] = float(data['default_price'])
            except (TypeError, ValueError):
                return JsonResponse({
                    'success': False,
                    'error': 'Некорректное значение цены'
                }, status=400)
        
        form = StudentForm(data)
        if form.is_valid():
            student = form.save()
            # Возвращаем больше данных о созданном студенте
            return JsonResponse({
                'success': True,
                'student': {
                    'id': student.id,
                    'full_name': student.full_name,
                    'attendance_type_display': student.get_attendance_type_display(),
                    'default_price': str(student.default_price),
                    'individual_price': str(student.individual_price) if student.individual_price else None
                }
            })
        else:
            # Возвращаем более понятные ошибки
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(e) for e in error_list]
            return JsonResponse({
                'success': False,
                'error': json.dumps(errors)
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат JSON'
        }, status=400)

def student_quick_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            student = form.save()
            return JsonResponse({
                'success': True,
                'student': {
                    'id': student.id,
                    'full_name': student.full_name,
                    'attendance_type_display': student.get_attendance_type_display(),
                    'default_price': str(student.default_price),
                    'individual_price': str(student.individual_price) if student.individual_price else None,
                }
            })
        return JsonResponse({'success': False, 'errors': form.errors})

    # GET-запрос — отрисовать форму
    form = StudentForm(instance=student)
    return render(request, 'students/student_quick_form.html', {
        'form': form,
        'student': student
    })