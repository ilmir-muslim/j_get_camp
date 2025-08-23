from ninja import Router
from .models import Branch
from .schemas import BranchSchema, BranchCreateSchema
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

router = Router(tags=["Branches"])

@router.get("/", response=list[BranchSchema])
def list_branches(request):
    return Branch.objects.all()

@router.get("/{branch_id}/", response=BranchSchema)
def get_branch(request, branch_id: int):
    try:
        return Branch.objects.get(id=branch_id)
    except Branch.DoesNotExist:
        return JsonResponse({"error": "Branch not found"}, status=404)

@router.post("/", response=BranchSchema)
def create_branch(request, data: BranchCreateSchema):
    branch = Branch.objects.create(**data.dict())
    return branch

@router.put("/{branch_id}/", response=BranchSchema)
def update_branch(request, branch_id: int, data: BranchCreateSchema):
    branch = Branch.objects.get(id=branch_id)
    for attr, value in data.dict().items():
        setattr(branch, attr, value)
    branch.save()
    return branch


@router.delete("/{branch_id}/")
def delete_branch(request, branch_id: int):
    try:
        branch = Branch.objects.get(id=branch_id)
    except Branch.DoesNotExist:
        return JsonResponse({"success": False, "error": "Филиал не найден"}, status=404)

    # Проверка наличия связанных расписаний
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
