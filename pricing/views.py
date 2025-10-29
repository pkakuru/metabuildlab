from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect

def check_pricing_access(user):
    """Check if user can access pricing module"""
    return user.can_access_module('pricing')

def get_base_context(user):
    """Get common context data needed by all views"""
    return {
        'accessible_modules': user.get_accessible_modules() if user.is_authenticated else [],
        'user_role': user.role if user.is_authenticated else None,
    }

@login_required
def pricing_dashboard(request):
    if not check_pricing_access(request.user):
        messages.error(request, "You don't have permission to access the Pricing module.")
        return redirect('home')
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Pricing Dashboard',
    })
    return render(request, 'pricing/dashboard.html', context)

@login_required
def catalog(request):
    # Director only
    if not (request.user.is_director and check_pricing_access(request.user)):
        raise PermissionDenied("Only Directors can access the Catalog.")
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Test Catalog',
    })
    return render(request, 'pricing/catalog.html', context)

@login_required
def master_price_list(request):
    # Director (full access), Lab Manager (full access), Office Staff (view only)
    if not check_pricing_access(request.user):
        raise PermissionDenied("You don't have permission to access the Master Price List.")
    
    if not (request.user.is_director or request.user.is_lab_manager or request.user.is_office_staff):
        raise PermissionDenied("You don't have permission to access the Master Price List.")
    
    # Determine if user has edit access
    can_edit = request.user.is_director or request.user.is_lab_manager
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Master Price List',
        'can_edit': can_edit,
    })
    return render(request, 'pricing/master_price_list.html', context)

@login_required
def categories(request):
    # Director (full access), Lab Manager (full access)
    if not check_pricing_access(request.user):
        raise PermissionDenied("You don't have permission to access Categories.")
    
    if not (request.user.is_director or request.user.is_lab_manager):
        raise PermissionDenied("You don't have permission to access Categories.")
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Test Categories',
    })
    return render(request, 'pricing/categories.html', context)

@login_required
def tests_parameters(request):
    # Director (full access), Lab Manager (full access), Technician (view only)
    if not check_pricing_access(request.user):
        raise PermissionDenied("You don't have permission to access Tests & Parameters.")
    
    if not (request.user.is_director or request.user.is_lab_manager or request.user.is_technician):
        raise PermissionDenied("You don't have permission to access Tests & Parameters.")
    
    # Determine if user has edit access
    can_edit = request.user.is_director or request.user.is_lab_manager
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Tests & Parameters',
        'can_edit': can_edit,
    })
    return render(request, 'pricing/tests_parameters.html', context)

@login_required
def search_filter(request):
    # Director only
    if not (request.user.is_director and check_pricing_access(request.user)):
        raise PermissionDenied("Only Directors can access Search & Filter.")
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Search & Filter',
    })
    return render(request, 'pricing/search_filter.html', context)

@login_required
def pricing_rules(request):
    # Director only
    if not (request.user.is_director and check_pricing_access(request.user)):
        raise PermissionDenied("Only Directors can access Pricing Rules.")
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Pricing Rules',
    })
    return render(request, 'pricing/pricing_rules.html', context)

@login_required
def discount_schemes(request):
    # Director only
    if not (request.user.is_director and check_pricing_access(request.user)):
        raise PermissionDenied("Only Directors can access Discount Schemes.")
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Discount Schemes',
    })
    return render(request, 'pricing/discount_schemes.html', context)