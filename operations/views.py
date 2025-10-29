from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def check_operations_access(user):
    """
    Check if user has access to Operations module
    All roles except undefined have some level of operations access
    """
    return user.can_access_module('operations')

def get_base_context(user):
    """Get common context data needed by all views"""
    return {
        'accessible_modules': user.get_accessible_modules() if user.is_authenticated else [],
        'user_role': user.role if user.is_authenticated else None,
    }


@login_required
def operations_dashboard(request):
    """
    Operations module dashboard - role-specific content
    """
    if not check_operations_access(request.user):
        messages.error(request, "You don't have permission to access the Operations module.")
        return redirect('home')
    
    user = request.user
    
    # Role-specific dashboard data
    context = {
        'page_title': 'Operations Dashboard',
        'user_role': user.role,
        'accessible_modules': user.get_accessible_modules(),
        'role_display': user.get_role_display(),
    }
    
    return render(request, 'operations/dashboard.html', context)


@login_required  
def job_board(request):
    """Job Board - All Jobs (Director) or filtered (Lab Manager)"""
    if not check_operations_access(request.user) or request.user.role == 'office_staff':
        raise PermissionDenied("Lab access required")
    
    context = {
        'page_title': 'Job Board - All Jobs' if request.user.role == 'director' else 'Job Board',
        'jobs': [],  # TODO: Add actual jobs data
    }
    return render(request, 'operations/job_board.html', context)


@login_required
def samples_intake(request):
    """Samples Intake - Available to all roles"""  
    if not check_operations_access(request.user):
        raise PermissionDenied("Operations access required")
        
    context = {
        'page_title': 'Samples Intake',
        'samples': [],  # TODO: Add actual samples data
    }
    return render(request, 'operations/samples_intake.html', context)


@login_required
def technician_worklist(request):
    """Technician Worklist - Director only"""
    if not check_operations_access(request.user) or request.user.role != 'director':
        raise PermissionDenied("Director access required")
        
    context = {
        'page_title': 'Technician Worklist',
        'worklist': [],  # TODO: Add actual worklist data
    }
    return render(request, 'operations/technician_worklist.html', context)


@login_required
def results_review(request):
    """Results Review - Director and Lab Manager"""
    if not check_operations_access(request.user) or request.user.role in ['office_staff', 'technician']:
        raise PermissionDenied("Manager level access required")
        
    context = {
        'page_title': 'Results Review',
        'pending_results': [],  # TODO: Add actual results data
    }
    return render(request, 'operations/results_review.html', context)


@login_required
def attachments(request):
    """Attachments - Director only"""
    if not check_operations_access(request.user) or request.user.role != 'director':
        raise PermissionDenied("Director access required")
        
    context = {
        'page_title': 'Job Attachments',
        'attachments': [],  # TODO: Add actual attachments data
    }
    return render(request, 'operations/attachments.html', context)


@login_required
def turnaround_tracker(request):
    """Turnaround Tracker - Director and Lab Manager"""
    if not check_operations_access(request.user) or request.user.role in ['office_staff', 'technician']:
        raise PermissionDenied("Manager level access required")
        
    context = {
        'page_title': 'Turnaround Tracker',
        'turnaround_data': [],  # TODO: Add actual turnaround data
    }
    return render(request, 'operations/turnaround_tracker.html', context)


@login_required
def job_reports(request):
    """Job Reports - Director only"""
    if not check_operations_access(request.user) or request.user.role != 'director':
        raise PermissionDenied("Director access required")
        
    context = {
        'page_title': 'Job Reports',
    }
    return render(request, 'operations/job_reports.html', context)


# Technician-specific views
@login_required
def my_jobs(request):
    """My Jobs - Technician only"""
    if not check_operations_access(request.user) or request.user.role != 'technician':
        raise PermissionDenied("Technician access required")
        
    context = {
        'page_title': 'My Jobs',
        'my_jobs': [],  # TODO: Add technician's assigned jobs
    }
    return render(request, 'operations/my_jobs.html', context)


@login_required
def results_entry(request):
    """Results Entry - Technician only"""
    if not check_operations_access(request.user) or request.user.role != 'technician':
        raise PermissionDenied("Technician access required")
        
    context = {
        'page_title': 'Results Entry',
    }
    return render(request, 'operations/results_entry.html', context)


@login_required
def my_attachments(request):
    """My Attachments - Technician only"""
    if not check_operations_access(request.user) or request.user.role != 'technician':
        raise PermissionDenied("Technician access required")
        
    context = {
        'page_title': 'My Attachments',
        'attachments': [],  # TODO: Add technician's attachments
    }
    return render(request, 'operations/my_attachments.html', context)


@login_required
def activity_log(request):
    """Activity Log - Technician only"""
    if not check_operations_access(request.user) or request.user.role != 'technician':
        raise PermissionDenied("Technician access required")
        
    context = {
        'page_title': 'My Activity Log',
        'activities': [],  # TODO: Add technician's activity log
    }
    return render(request, 'operations/activity_log.html', context)
