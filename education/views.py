from django.shortcuts import render, redirect, get_object_or_404

from core.utils import role_required
from education.forms import RegulationForm
from .models import Regulation

@role_required(['manager', 'admin'])
def regulation_list(request):
    """
    Список обучающих материалов и регламентов.
    """
    regulations = Regulation.objects.all()
    return render(request, 'education/regulation_list.html', {'regulations': regulations})


@role_required(['manager', 'admin'])
def regulation_create(request):
    """
    Добавление нового обучающего материала.
    """
    if request.method == 'POST':
        form = RegulationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('regulation_list')
    else:
        form = RegulationForm()
    return render(request, 'education/regulation_form.html', {'form': form})


@role_required(['manager', 'admin'])
def regulation_edit(request, pk):
    """
    Редактирование обучающего материала.
    """
    regulation = get_object_or_404(Regulation, pk=pk)
    if request.method == 'POST':
        form = RegulationForm(request.POST, request.FILES, instance=regulation)
        if form.is_valid():
            form.save()
            return redirect('regulation_list')
    else:
        form = RegulationForm(instance=regulation)
    return render(request, 'education/regulation_form.html', {'form': form})


@role_required(['manager', 'admin'])
def regulation_delete(request, pk):
    """
    Удаление обучающего материала.
    """
    regulation = get_object_or_404(Regulation, pk=pk)
    if request.method == 'POST':
        regulation.delete()
        return redirect('regulation_list')
    return render(request, 'education/regulation_confirm_delete.html', {'regulation': regulation})
