from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied


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


@login_required
def clients(request):
    """Clients management view"""
    if not check_sales_access(request.user):
        raise PermissionDenied("No access to Sales module")
        
    context = {
        'page_title': 'Clients',
        'clients': [],  # TODO: Add actual clients data
    }
    return render(request, 'sales/clients.html', context)


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
