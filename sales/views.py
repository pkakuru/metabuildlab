from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, Count
from operations.models import Client, Sample
from operations.forms import ClientForm


def check_sales_access(user):
    """
    Check if user has access to Sales module
    Technicians are not allowed access to Sales
    """
    return user.can_access_module('sales')

def get_base_context(user):
    """Get common context data needed by all views"""
    return {
        'accessible_modules': user.get_accessible_modules() if user.is_authenticated else [],
        'user_role': user.role if user.is_authenticated else None,
    }


@login_required
def sales_dashboard(request):
    """
    Sales module dashboard - role-specific content
    """
    if not check_sales_access(request.user):
        messages.error(request, "You don't have permission to access the Sales module.")
        return redirect('home')
    
    user = request.user
    
    # Role-specific dashboard data
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Sales Dashboard',
        'role_display': user.get_role_display(),
    })
    
    return render(request, 'sales/dashboard.html', context)


@login_required  
def quotations(request):
    """All Quotations view"""
    if not check_sales_access(request.user):
        raise PermissionDenied("No access to Sales module")
    
    context = {
        'page_title': 'All Quotations',
        'quotations': [],  # TODO: Add actual quotations data
    }
    return render(request, 'sales/quotations.html', context)


@login_required
def new_quotation(request):
    """New Quotation creation view"""  
    if not check_sales_access(request.user):
        raise PermissionDenied("No access to Sales module")
        
    context = get_base_context(request.user)
    context.update({
        'page_title': 'New Quotation',
    })
    return render(request, 'sales/new_quotation.html', context)


@login_required
def quotation_kanban(request):
    """Quotation Kanban Board - Director only"""
    if not check_sales_access(request.user) or request.user.role != 'director':
        raise PermissionDenied("Director access required")
        
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Quotation Kanban Board',
    })
    return render(request, 'sales/quotation_kanban.html', context)


@login_required
def activity_log(request):
    """Activity Log - Director only"""
    if not check_sales_access(request.user) or request.user.role != 'director':
        raise PermissionDenied("Director access required")
        
    context = {
        'page_title': 'Sales Activity Log',
    }
    return render(request, 'sales/activity_log.html', context)


def check_client_management_access(user):
    """Check if user can manage clients (Office Staff, Lab Manager, Directors only - not Technicians)"""
    return user.role in ['office_staff', 'lab_manager', 'director']


@login_required
def clients(request):
    """Client Management - Office Staff, Lab Manager, and Directors only"""
    if not check_client_management_access(request.user):
        raise PermissionDenied("Client management access required. Office Staff, Lab Manager, and Directors only.")
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Build queryset
    clients = Client.objects.all().annotate(
        sample_count=Count('samples')
    )
    
    # Apply filters
    if search_query:
        clients = clients.filter(
            Q(name__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(company_registration__icontains=search_query)
        )
    
    if status_filter == 'active':
        clients = clients.filter(is_active=True)
    elif status_filter == 'inactive':
        clients = clients.filter(is_active=False)
    
    # Order by name
    clients = clients.order_by('name')
    
    # Get statistics
    total_clients = Client.objects.count()
    active_clients = Client.objects.filter(is_active=True).count()
    inactive_clients = Client.objects.filter(is_active=False).count()
    
    # Pagination
    paginator = Paginator(clients, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Client Management',
        'page_obj': page_obj,
        'clients': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_clients': total_clients,
        'active_clients': active_clients,
        'inactive_clients': inactive_clients,
        'can_manage_clients': check_client_management_access(request.user),
    })
    return render(request, 'sales/clients.html', context)


@login_required
def client_create(request):
    """Create a new client - Office Staff, Lab Manager, Directors only"""
    if not check_client_management_access(request.user):
        raise PermissionDenied("Client management access required. Office Staff, Lab Manager, and Directors only.")
    
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f"Client '{client.name}' has been created successfully.")
            return redirect('sales:client_detail', client_id=client.id)
    else:
        form = ClientForm()
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Create New Client',
        'form': form,
        'action': 'create',
    })
    return render(request, 'sales/client_form.html', context)


@login_required
def client_detail(request, client_id):
    """View client details - Office Staff, Lab Manager, Directors only"""
    if not check_client_management_access(request.user):
        raise PermissionDenied("Client management access required. Office Staff, Lab Manager, and Directors only.")
    
    client = get_object_or_404(Client, id=client_id)
    samples = client.samples.order_by('-received_date')[:10]  # Recent samples
    
    # Get sample statistics
    total_samples = client.samples.count()
    active_samples = client.samples.filter(status__in=['received', 'in_progress', 'testing']).count()
    completed_samples = client.samples.filter(status__in=['completed', 'reported']).count()
    
    context = get_base_context(request.user)
    context.update({
        'page_title': f'Client: {client.name}',
        'client': client,
        'samples': samples,
        'total_samples': total_samples,
        'active_samples': active_samples,
        'completed_samples': completed_samples,
        'can_manage_clients': check_client_management_access(request.user),
    })
    return render(request, 'sales/client_detail.html', context)


@login_required
def client_update(request, client_id):
    """Update client information - Office Staff, Lab Manager, Directors only"""
    if not check_client_management_access(request.user):
        raise PermissionDenied("Client management access required. Office Staff, Lab Manager, and Directors only.")
    
    client = get_object_or_404(Client, id=client_id)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save()
            messages.success(request, f"Client '{client.name}' has been updated successfully.")
            return redirect('sales:client_detail', client_id=client.id)
    else:
        form = ClientForm(instance=client)
    
    context = get_base_context(request.user)
    context.update({
        'page_title': f'Edit Client: {client.name}',
        'form': form,
        'client': client,
        'action': 'update',
    })
    return render(request, 'sales/client_form.html', context)


@login_required
def client_delete(request, client_id):
    """Delete (deactivate) a client - Lab Manager and Directors only"""
    # Only Lab Managers and Directors can delete clients
    if request.user.role not in ['lab_manager', 'director']:
        raise PermissionDenied("Only Lab Managers and Directors can delete clients.")
    
    client = get_object_or_404(Client, id=client_id)
    
    if request.method == 'POST':
        # Soft delete - set is_active to False
        if client.samples.exists():
            client.is_active = False
            client.save()
            messages.success(request, f"Client '{client.name}' has been deactivated. They cannot receive new samples.")
        else:
            client.delete()
            messages.success(request, f"Client '{client.name}' has been permanently deleted.")
        
        return redirect('sales:clients')
    
    context = get_base_context(request.user)
    context.update({
        'page_title': f'Delete Client: {client.name}',
        'client': client,
        'has_samples': client.samples.exists(),
    })
    return render(request, 'sales/client_delete.html', context)


@login_required
def leads(request):
    """Leads management - Director only"""
    if not check_sales_access(request.user) or request.user.role != 'director':
        raise PermissionDenied("Director access required")
        
    context = {
        'page_title': 'Leads',
        'leads': [],  # TODO: Add actual leads data
    }
    return render(request, 'sales/leads.html', context)


@login_required
def contracts(request):
    """Contracts view - Director and Lab Manager"""
    if not check_sales_access(request.user) or request.user.role == 'office_staff':
        raise PermissionDenied("Manager level access required")
        
    context = {
        'page_title': 'Contracts',
        'contracts': [],  # TODO: Add actual contracts data
    }
    return render(request, 'sales/contracts.html', context)


@login_required
def sales_summary(request):
    """Sales Summary Reports - Director only"""
    if not check_sales_access(request.user) or request.user.role != 'director':
        raise PermissionDenied("Director access required")
        
    context = {
        'page_title': 'Sales Summary',
    }
    return render(request, 'sales/sales_summary.html', context)


@login_required
def conversion_rates(request):
    """Conversion Rates Reports - Director only"""
    if not check_sales_access(request.user) or request.user.role != 'director':
        raise PermissionDenied("Director access required")
        
    context = {
        'page_title': 'Conversion Rates',
    }
    return render(request, 'sales/conversion_rates.html', context)
