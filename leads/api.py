from ninja import Router
from .models import Lead
from .schemas import LeadSchema, LeadCreateSchema

router = Router(tags=["Leads"])

@router.get("/", response=list[LeadSchema])
def list_leads(request):
    return Lead.objects.all()

@router.get("/{lead_id}/", response=LeadSchema)
def get_lead(request, lead_id: int):
    lead = Lead.objects.get(id=lead_id)
    return lead

@router.post("/", response=LeadSchema)
def create_lead(request, data: LeadCreateSchema):
    lead = Lead.objects.create(**data.dict())
    return lead

@router.put("/{lead_id}/", response=LeadSchema)
def update_lead(request, lead_id: int, data: LeadCreateSchema):
    lead = Lead.objects.get(id=lead_id)
    for attr, value in data.dict().items():
        setattr(lead, attr, value)
    lead.save()
    return lead

@router.delete("/{lead_id}/")
def delete_lead(request, lead_id: int):
    Lead.objects.filter(id=lead_id).delete()
    return {"success": True}