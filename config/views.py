from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect

def check_config_access(user):
    """Check if user can access config module - Directors and Lab Managers only"""
    return user.can_access_module('config')

def get_base_context(user):
    """Get common context data needed by all views"""
    return {
        'accessible_modules': user.get_accessible_modules() if user.is_authenticated else [],
        'user_role': user.role if user.is_authenticated else None,
    }

@login_required
def config_dashboard(request):
    if not check_config_access(request.user):
        messages.error(request, "You don't have permission to access the Configuration module.")
        return redirect('home')
    
    # Only Directors and Lab Managers can access Config
    if not (request.user.is_director or request.user.is_lab_manager):
        raise PermissionDenied("Access to Configuration module is restricted to Directors and Lab Managers.")
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Configuration Dashboard',
    })
    return render(request, 'config/dashboard.html', context)

@login_required
def administration(request):
    # Director only - full admin access
    if not (request.user.is_director and check_config_access(request.user)):
        raise PermissionDenied("Only Directors can access Administration.")
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'System Administration',
    })
    return render(request, 'config/administration.html', context)

@login_required
def users_roles(request):
    # Director only - user management
    if not (request.user.is_director and check_config_access(request.user)):
        raise PermissionDenied("Only Directors can manage Users & Roles.")
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Users & Roles Management',
    })
    return render(request, 'config/users_roles.html', context)

@login_required
def labs_instruments(request):
    # Director (full access), Lab Manager (view only)
    if not check_config_access(request.user):
        raise PermissionDenied("You don't have permission to access Labs & Instruments.")
    
    if not (request.user.is_director or request.user.is_lab_manager):
        raise PermissionDenied("You don't have permission to access Labs & Instruments.")
    
    # Determine if user has edit access
    can_edit = request.user.is_director
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Labs & Instruments',
        'can_edit': can_edit,
    })
    return render(request, 'config/labs_instruments.html', context)

@login_required
def test_catalog_config(request):
    # Director only - test catalog configuration
    if not (request.user.is_director and check_config_access(request.user)):
        raise PermissionDenied("Only Directors can configure the Test Catalog.")
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Test Catalog Configuration',
    })
    return render(request, 'config/test_catalog_config.html', context)

@login_required
def pricing_rules_config(request):
    # Director only - pricing rules configuration
    if not (request.user.is_director and check_config_access(request.user)):
        raise PermissionDenied("Only Directors can configure Pricing Rules.")
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Pricing Rules Configuration',
    })
    return render(request, 'config/pricing_rules_config.html', context)

@login_required
def audit_log(request):
    # Director (full access), Lab Manager (view only)
    if not check_config_access(request.user):
        raise PermissionDenied("You don't have permission to access the Audit Log.")
    
    if not (request.user.is_director or request.user.is_lab_manager):
        raise PermissionDenied("You don't have permission to access the Audit Log.")
    
    # Determine if user has admin access
    can_admin = request.user.is_director
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'System Audit Log',
        'can_admin': can_admin,
    })
    return render(request, 'config/audit_log.html', context)