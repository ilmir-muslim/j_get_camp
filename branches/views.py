from django.shortcuts import render, redirect, get_object_or_404
from branches.models import Branch
from branches.forms import BranchForm
from core.utils import role_required

@role_required(['manager', 'admin'])
def branch_list(request):
    """
    Список филиалов.
    """
    branches = Branch.objects.all()
    return render(request, 'branches/branch_list.html', {'branches': branches})


@role_required(['manager', 'admin'])
def branch_create(request):
    """
    Добавление нового филиала.
    """
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('branch_list')
    else:
        form = BranchForm()
    return render(request, 'branches/branch_form.html', {'form': form})


@role_required(['manager', 'admin'])
def branch_edit(request, pk):
    """
    Редактирование филиала.
    """
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
            return redirect('branch_list')
    else:
        form = BranchForm(instance=branch)
    return render(request, 'branches/branch_form.html', {'form': form})


@role_required(['manager', 'admin'])
def branch_delete(request, pk):
    """
    Удаление филиала.
    """
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        branch.delete()
        return redirect('branch_list')
    return render(request, 'branches/branch_confirm_delete.html', {'branch': branch})
