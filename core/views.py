from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Sum

from core.utils import role_required
from employees.models import Employee
from payroll.models import Expense, Salary
from schedule.models import Schedule
from students.models import Student

@login_required
def dashboard(request):
    """
    Отображает главную страницу с плитками разделов в зависимости от роли пользователя.
    
    Менеджер — полный доступ ко всем плиткам.
    Администратор — без аналитики.
    Начальник лагеря и лаборатории — только расписание, сотрудники, ученики и обучение.
    """
    role = request.user.role
    context = {'role': role}
    return render(request, 'core/dashboard.html', context)

@role_required(['manager', 'admin'])
def analytics_dashboard(request):
    """
    Сводная аналитика для менеджера.
    Доступна только пользователю с ролью manager.
    """
    stats = {
        'schedule_count': Schedule.objects.count(),
        'employee_count': Employee.objects.count(),
        'student_count': Student.objects.count(),
        'total_expenses': Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_salaries': Salary.objects.aggregate(Sum('total_payment'))['total_payment__sum'] or 0,
    }

    return render(request, 'core/analytics_dashboard.html', {'stats': stats})

