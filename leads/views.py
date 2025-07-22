from django.shortcuts import render, redirect, get_object_or_404

from core.utils import role_required
from leads.forms import LeadForm
from .models import Lead

def lead_list(request):
    leads = Lead.objects.all()
    return render(request, 'leads/lead_list.html', {'leads': leads})

@role_required(['manager', 'admin'])
def lead_create(request):
    """
    Представление для создания лида.
    """
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lead_list')
    else:
        form = LeadForm()

    return render(request, 'leads/lead_form.html', {'form': form})

@role_required(['manager', 'admin'])
def lead_edit(request, pk):
    """
    Представление для редактирования лида.
    """
    lead = get_object_or_404(Lead, pk=pk)

    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            return redirect('lead_list')
    else:
        form = LeadForm(instance=lead)

    return render(request, 'leads/lead_form.html', {'form': form})

@role_required(['manager', 'admin'])
def lead_delete(request, pk):
    """
    Представление для удаления лида.
    Доступно только менеджеру и администратору.
    """
    lead = get_object_or_404(Lead, pk=pk)

    if request.method == 'POST':
        lead.delete()
        return redirect('lead_list')

    return render(request, 'leads/lead_confirm_delete.html', {'lead': lead})


