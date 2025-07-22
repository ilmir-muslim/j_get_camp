from ninja import Router
from django.shortcuts import get_object_or_404
from .models import Regulation
from .schemas import RegulationSchema, RegulationCreateSchema

router = Router(tags=["Education"])


@router.get("/regulations/", response=list[RegulationSchema])
def list_regulations(request):
    """
    Получить список всех положений.
    """
    queryset = Regulation.objects.all()
    return [
        {
            "id": obj.id,
            "title": obj.title,
            "file": obj.file.url if obj.file else "",
            "uploaded_at": obj.uploaded_at.isoformat(),
        }
        for obj in queryset
    ]


@router.get("/regulations/{regulation_id}/", response=RegulationSchema)
def get_regulation(request, regulation_id: int):
    """
    Получить конкретное положение.
    """
    obj = get_object_or_404(Regulation, id=regulation_id)
    return {
        "id": obj.id,
        "title": obj.title,
        "file": obj.file.url if obj.file else "",
        "uploaded_at": obj.uploaded_at.isoformat(),
    }

@router.post("/regulations/", response=RegulationSchema)
def create_regulation(request, data: RegulationCreateSchema):
    regulation = Regulation.objects.create(**data.dict())
    return regulation


@router.put("/regulations/{regulation_id}/", response=RegulationSchema)
def update_regulation(request, regulation_id: int, data: RegulationCreateSchema):
    regulation = Regulation.objects.get(id=regulation_id)
    for attr, value in data.dict().items():
        setattr(regulation, attr, value)
    regulation.save()
    return regulation


@router.delete("/regulations/{regulation_id}/")
def delete_regulation(request, regulation_id: int):
    Regulation.objects.filter(id=regulation_id).delete()
    return {"success": True}
