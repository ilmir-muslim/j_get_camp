from ninja import Router
from .models import Branch
from .schemas import BranchSchema, BranchCreateSchema

router = Router(tags=["Branches"])

@router.get("/", response=list[BranchSchema])
def list_branches(request):
    return Branch.objects.all()

@router.get("/{branch_id}/", response=BranchSchema)
def get_branch(request, branch_id: int):
    branch = Branch.objects.get(id=branch_id)
    return branch

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
    Branch.objects.filter(id=branch_id).delete()
    return {"success": True}