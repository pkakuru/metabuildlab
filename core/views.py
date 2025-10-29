from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages


@login_required
def home(request):
    """
    Home page view with role-based dashboard layout
    """
    user = request.user
    
    # Get user's accessible modules
    accessible_modules = user.get_accessible_modules()
    
    # Role-specific dashboard data
    dashboard_data = {
        'director': {
            'title': 'Director Dashboard',
            'stats': [
                {'label': 'Total Revenue (YTD)', 'value': 'UGX 485M', 'icon': 'currency-dollar', 'color': 'primary'},
                {'label': 'Active Projects', 'value': '89', 'icon': 'clipboard-data', 'color': 'success'},
                {'label': 'Total Staff', 'value': '24', 'icon': 'people', 'color': 'info'},
                {'label': 'Lab Capacity', 'value': '95%', 'icon': 'speedometer2', 'color': 'warning'},
            ]
        },
        'lab_manager': {
            'title': 'Lab Manager Dashboard',
            'stats': [
                {'label': 'Active Test Jobs', 'value': '47', 'icon': 'clipboard-data', 'color': 'success'},
                {'label': 'Pending Results', 'value': '12', 'icon': 'hourglass-split', 'color': 'warning'},
                {'label': 'Lab Utilization', 'value': '85%', 'icon': 'speedometer2', 'color': 'info'},
                {'label': 'Quality Score', 'value': '98.5%', 'icon': 'award', 'color': 'primary'},
            ]
        },
        'office_staff': {
            'title': 'Office Staff Dashboard', 
            'stats': [
                {'label': 'Pending Quotations', 'value': '12', 'icon': 'file-earmark-text', 'color': 'warning'},
                {'label': 'Active Clients', 'value': '156', 'icon': 'people', 'color': 'info'},
                {'label': 'Monthly Revenue', 'value': 'UGX 28.5M', 'icon': 'currency-dollar', 'color': 'primary'},
                {'label': 'Outstanding Invoices', 'value': '8', 'icon': 'receipt', 'color': 'danger'},
            ]
        },
        'technician': {
            'title': 'Technician Dashboard',
            'stats': [
                {'label': 'My Assigned Jobs', 'value': '7', 'icon': 'tools', 'color': 'primary'},
                {'label': 'Completed Today', 'value': '3', 'icon': 'check-circle', 'color': 'success'},
                {'label': 'Pending Tests', 'value': '4', 'icon': 'clock', 'color': 'warning'},
                {'label': 'Equipment Status', 'value': 'OK', 'icon': 'gear', 'color': 'success'},
            ]
        }
    }
    
    current_role_data = dashboard_data.get(user.role, dashboard_data['office_staff'])
    
    context = {
        'page_title': current_role_data['title'],
        'user_role': user.role,
        'accessible_modules': accessible_modules,
        'role_display': user.get_role_display(),
        'dashboard_stats': current_role_data['stats'],
        'department': user.department,
    }
    return render(request, 'home.html', context)


def user_logout(request):
    """
    Custom logout view
    """
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')
