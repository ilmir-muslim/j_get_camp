from ninja import File, Form, Router
from ninja.files import UploadedFile
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from typing import Optional
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
def create_regulation(request):
    """
    Загрузить новое положение (multipart).
    """
    title = request.POST.get("title")
    file = request.FILES.get("file")

    if not title or not file:
        return JsonResponse({"error": "Missing title or file"}, status=400)

    regulation = Regulation.objects.create(title=title, file=file)
    return {
        "id": regulation.id,
        "title": regulation.title,
        "file": regulation.file.url if regulation.file else "",
        "uploaded_at": regulation.uploaded_at.isoformat(),
    }


@router.patch("/regulations/{regulation_id}/", response=RegulationSchema)
def partial_update_regulation(
    request,
    regulation_id: int,
    title: Optional[str] = Form(None),
    file: Optional[UploadedFile] = File(None),
):
    regulation = Regulation.objects.get(id=regulation_id)
    if title is not None:
        regulation.title = title
    if file is not None:
        regulation.file.save(file.name, file.file)
    regulation.save()
    return regulation


@router.delete("/regulations/{regulation_id}/")
def delete_regulation(request, regulation_id: int):
    Regulation.objects.filter(id=regulation_id).delete()
    return {"success": True}
