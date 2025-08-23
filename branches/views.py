from django.shortcuts import render, redirect, get_object_or_404

from core.utils import role_required
from branches.models import Branch
from branches.forms import BranchForm

@role_required(['manager', 'admin'])
def branch_list(request):
    branches = Branch.objects.all()
    return render(request, 'branches/branch_list.html', {'branches': branches})

@role_required(['manager', 'admin'])
def branch_create(request):
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
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        branch.delete()
        return redirect('branch_list')
    return render(request, 'branches/branch_confirm_delete.html', {'branch': branch})


@role_required(["manager", "admin"])
def branch_detail_modal(request, pk):
    branch = get_object_or_404(Branch, pk=pk)

    # Получаем сотрудников филиала без прямого импорта
    try:
        from employees.models import Employee

        employees = Employee.objects.filter(branch=branch)
    except ImportError:
        employees = []

    return render(
        request,
        "branches/branch_detail_modal.html",
        {
            "branch": branch,
            "employees": employees,
        },
    )
