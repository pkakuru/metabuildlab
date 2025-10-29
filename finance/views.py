from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def check_finance_access(user):
    """
    Check if user has access to Finance module
    Technicians are not allowed access to Finance
    """
    return user.can_access_module('finance')

def get_base_context(user):
    """Get common context data needed by all views"""
    return {
        'accessible_modules': user.get_accessible_modules() if user.is_authenticated else [],
        'user_role': user.role if user.is_authenticated else None,
    }


@login_required
def finance_dashboard(request):
    """
    Finance module dashboard - role-specific content
    """
    if not check_finance_access(request.user):
        messages.error(request, "You don't have permission to access the Finance module.")
        return redirect('home')
    
    user = request.user
    
    # Role-specific dashboard data
    context = {
        'page_title': 'Finance Dashboard',
        'user_role': user.role,
        'accessible_modules': user.get_accessible_modules(),
        'role_display': user.get_role_display(),
    }
    
    return render(request, 'finance/dashboard.html', context)


@login_required  
def invoices(request):
    """All Invoices - Available to Director, Lab Manager, Office Staff"""
    if not check_finance_access(request.user):
        raise PermissionDenied("No access to Finance module")
    
    context = {
        'page_title': 'All Invoices',
        'invoices': [],  # TODO: Add actual invoices data
    }
    return render(request, 'finance/invoices.html', context)


@login_required
def new_invoice(request):
    """New Invoice creation - Director and Office Staff only"""  
    if not check_finance_access(request.user) or request.user.role == 'lab_manager':
        raise PermissionDenied("Invoice creation requires Office Staff or Director access")
        
    context = {
        'page_title': 'New Invoice',
    }
    return render(request, 'finance/new_invoice.html', context)


@login_required
def record_payment(request):
    """Record Payment - Director and Office Staff only"""
    if not check_finance_access(request.user) or request.user.role == 'lab_manager':
        raise PermissionDenied("Payment recording requires Office Staff or Director access")
        
    context = {
        'page_title': 'Record Payment',
    }
    return render(request, 'finance/record_payment.html', context)


@login_required
def receipts(request):
    """Receipts management - Director and Office Staff only"""
    if not check_finance_access(request.user) or request.user.role == 'lab_manager':
        raise PermissionDenied("Receipt management requires Office Staff or Director access")
        
    context = {
        'page_title': 'Receipts',
        'receipts': [],  # TODO: Add actual receipts data
    }
    return render(request, 'finance/receipts.html', context)


@login_required
def credit_notes(request):
    """Credit Notes - Director only"""
    if not check_finance_access(request.user) or request.user.role != 'director':
        raise PermissionDenied("Director access required")
        
    context = {
        'page_title': 'Credit Notes',
        'credit_notes': [],  # TODO: Add actual credit notes data
    }
    return render(request, 'finance/credit_notes.html', context)


@login_required
def statements(request):
    """Statements - Director only"""
    if not check_finance_access(request.user) or request.user.role != 'director':
        raise PermissionDenied("Director access required")
        
    context = {
        'page_title': 'Financial Statements',
    }
    return render(request, 'finance/statements.html', context)


@login_required
def unpaid_ageing(request):
    """Unpaid/Ageing Analysis - Director only"""
    if not check_finance_access(request.user) or request.user.role != 'director':
        raise PermissionDenied("Director access required")
        
    context = {
        'page_title': 'Unpaid / Ageing Analysis',
        'ageing_data': [],  # TODO: Add actual ageing analysis data
    }
    return render(request, 'finance/unpaid_ageing.html', context)


@login_required
def revenue_reports(request):
    """Revenue Reports - Director and Lab Manager only"""
    if not check_finance_access(request.user) or request.user.role == 'office_staff':
        raise PermissionDenied("Manager level access required")
        
    context = {
        'page_title': 'Revenue Reports',
        'revenue_data': [],  # TODO: Add actual revenue reports data
    }
    return render(request, 'finance/revenue_reports.html', context)
