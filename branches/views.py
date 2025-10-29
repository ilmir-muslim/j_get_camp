from django.shortcuts import render, redirect, get_object_or_404

from core.utils import role_required
from branches.models import Branch, City
from branches.forms import BranchForm


@role_required(["manager", "admin"])
def branch_list(request):
    user = request.user
    # Для администраторов показываем только филиалы их города
    if user.is_authenticated and user.role == "admin" and user.city:
        branches = Branch.objects.filter(city=user.city)
    else:
        branches = Branch.objects.all()

    # Получаем список всех городов для форм
    cities = City.objects.all()

    return render(
        request,
        "branches/branch_list.html",
        {"branches": branches, "cities": cities},  # Передаем города в контекст
    )


@role_required(["manager", "admin"])
def branch_create(request):
    if request.method == "POST":
        form = BranchForm(request.POST)
        if form.is_valid():
            branch = form.save(commit=False)
            # Для администраторов автоматически устанавливаем город
            if request.user.role == "admin" and request.user.city:
                branch.city = request.user.city
            branch.save()
            return redirect("branch_list")
    else:
        form = BranchForm()
    return render(request, "branches/branch_form.html", {"form": form})


@role_required(["manager", "admin"])
def branch_edit(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    # Проверка доступа для администраторов
    user = request.user
    if (
        user.is_authenticated
        and user.role == "admin"
        and user.city
        and branch.city != user.city
    ):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied

    if request.method == "POST":
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
            return redirect("branch_list")
    else:
        form = BranchForm(instance=branch)
    return render(request, "branches/branch_form.html", {"form": form})


@role_required(["manager", "admin"])
def branch_delete(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    # Проверка доступа для администраторов
    user = request.user
    if (
        user.is_authenticated
        and user.role == "admin"
        and user.city
        and branch.city != user.city
    ):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied

    if request.method == "POST":
        branch.delete()
        return redirect("branch_list")
    return render(request, "branches/branch_confirm_delete.html", {"branch": branch})


@role_required(["manager", "admin"])
def branch_detail_modal(request, pk):
    branch = get_object_or_404(Branch, pk=pk)

    # Проверка доступа для администраторов
    user = request.user
    if (
        user.is_authenticated
        and user.role == "admin"
        and user.city
        and branch.city != user.city
    ):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied

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
