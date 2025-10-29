from ninja import Router
from .models import Branch, City
from .schemas import BranchSchema, BranchCreateSchema
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

router = Router(tags=["Branches"])


@router.get("/", response=list[BranchSchema])
def list_branches(request):
    user = request.user
    # Для администраторов показываем только филиалы их города
    if user.is_authenticated and user.role == "admin" and user.city:
        return Branch.objects.filter(city=user.city)
    return Branch.objects.all()


@router.get("/{branch_id}/", response=BranchSchema)
def get_branch(request, branch_id: int):
    try:
        branch = Branch.objects.get(id=branch_id)
        # Проверка доступа для администраторов
        user = request.user
        if (
            user.is_authenticated
            and user.role == "admin"
            and user.city
            and branch.city != user.city
        ):
            return JsonResponse({"error": "Доступ запрещен"}, status=403)
        return branch
    except Branch.DoesNotExist:
        return JsonResponse({"error": "Branch not found"}, status=404)


@router.post("/", response=BranchSchema)
def create_branch(request, data: BranchCreateSchema):
    user = request.user
    branch_data = data.dict()

    # Для администраторов автоматически устанавливаем город
    if user.is_authenticated and user.role == "admin" and user.city:
        branch_data["city"] = user.city
    elif branch_data.get("city_id"):
        # Для менеджеров используем переданный город
        branch_data["city"] = get_object_or_404(City, id=branch_data.pop("city_id"))
    else:
        branch_data["city"] = None

    branch = Branch.objects.create(**branch_data)
    return branch


@router.put("/{branch_id}/", response=BranchSchema)
def update_branch(request, branch_id: int, data: BranchCreateSchema):
    branch = Branch.objects.get(id=branch_id)
    # Проверка доступа для администраторов
    user = request.user
    if (
        user.is_authenticated
        and user.role == "admin"
        and user.city
        and branch.city != user.city
    ):
        return JsonResponse({"error": "Доступ запрещен"}, status=403)

    update_data = data.dict()

    # Для администраторов оставляем текущий город
    if user.is_authenticated and user.role == "admin" and user.city:
        update_data.pop("city_id", None)
    elif "city_id" in update_data:
        # Для менеджеров обновляем город
        if update_data["city_id"]:
            branch.city = get_object_or_404(City, id=update_data.pop("city_id"))
        else:
            branch.city = None

    for attr, value in update_data.items():
        setattr(branch, attr, value)
    branch.save()
    return branch


@router.delete("/{branch_id}/")
def delete_branch(request, branch_id: int):
    try:
        branch = Branch.objects.get(id=branch_id)
        # Проверка доступа для администраторов
        user = request.user
        if (
            user.is_authenticated
            and user.role == "admin"
            and user.city
            and branch.city != user.city
        ):
            return JsonResponse({"error": "Доступ запрещен"}, status=403)

        if branch.schedule.exists():
            return JsonResponse(
                {
                    "success": False,
                    "error": "Невозможно удалить филиал с активными сменами",
                },
                status=400,
            )
        branch.delete()
        return JsonResponse({"success": True})
    except Branch.DoesNotExist:
        return JsonResponse({"success": False, "error": "Филиал не найден"}, status=404)
