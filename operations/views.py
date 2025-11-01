from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import Client, Sample, SampleTest, SampleStatusHistory
from .forms import ClientForm, SampleIntakeForm, QuickSampleIntakeForm, SampleTestForm, SampleStatusUpdateForm
from pricing.models import TestItem


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
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    client_filter = request.GET.get('client', '')
    
    # Build queryset
    samples = Sample.objects.select_related('client', 'received_by').prefetch_related('requested_tests').all()
    
    # Apply filters
    if search_query:
        samples = samples.filter(
            Q(sample_id__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(client_reference__icontains=search_query) |
            Q(sample_description__icontains=search_query)
        )
    
    if status_filter:
        samples = samples.filter(status=status_filter)
    
    if priority_filter:
        samples = samples.filter(priority=priority_filter)
    
    if client_filter:
        samples = samples.filter(client_id=client_filter)
    
    # Order by received date (newest first)
    samples = samples.order_by('-received_date')
    
    # Pagination
    paginator = Paginator(samples, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    clients = Client.objects.filter(is_active=True).order_by('name')
    status_choices = Sample.STATUS_CHOICES
    priority_choices = Sample.PRIORITY_CHOICES
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Samples Intake',
        'page_obj': page_obj,
        'samples': page_obj,
        'clients': clients,
        'status_choices': status_choices,
        'priority_choices': priority_choices,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'client_filter': client_filter,
        'total_samples': paginator.count,
    })
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


# Sample Intake Views
@login_required
def sample_intake_dashboard(request):
    """Dedicated Sample Intake Dashboard - Available to all roles"""
    if not check_operations_access(request.user):
        raise PermissionDenied("Operations access required")
    
    # Get recent samples received by this user
    recent_samples = Sample.objects.filter(received_by=request.user).order_by('-received_date')[:5]
    
    # Get sample statistics
    total_samples_received = Sample.objects.filter(received_by=request.user).count()
    samples_today = Sample.objects.filter(
        received_by=request.user,
        received_date__date=timezone.now().date()
    ).count()
    
    # Get pending samples (received but not completed)
    pending_samples = Sample.objects.filter(
        received_by=request.user,
        status__in=['received', 'in_progress', 'testing']
    ).count()
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Sample Intake Dashboard',
        'recent_samples': recent_samples,
        'total_samples_received': total_samples_received,
        'samples_today': samples_today,
        'pending_samples': pending_samples,
    })
    return render(request, 'operations/sample_intake_dashboard.html', context)


@login_required
def new_sample_intake(request):
    """New Sample Intake - Available to all roles"""
    if not check_operations_access(request.user):
        raise PermissionDenied("Operations access required")
    
    if request.method == 'POST':
        form = SampleIntakeForm(request.POST)
        client_form = ClientForm(request.POST) if request.POST.get('client_choice') == 'new' else None
        
        if form.is_valid():
            # Handle client creation or selection
            if request.POST.get('client_choice') == 'new' and client_form and client_form.is_valid():
                client = client_form.save()
            elif request.POST.get('client_choice') == 'existing':
                client = form.cleaned_data['existing_client']
            else:
                messages.error(request, "Please provide valid client information.")
                return render(request, 'operations/new_sample_intake.html', {
                    'form': form,
                    'client_form': client_form or ClientForm(),
                    'page_title': 'New Sample Intake',
                    **get_base_context(request.user)
                })
            
            # Create sample
            sample = form.save(commit=False)
            sample.client = client
            sample.received_by = request.user
            sample.save()
            
            # Add requested tests
            requested_tests = form.cleaned_data['requested_tests']
            for test_item in requested_tests:
                SampleTest.objects.create(
                    sample=sample,
                    test_item=test_item,
                    quantity_requested=1
                )
            
            # Create status history entry
            SampleStatusHistory.objects.create(
                sample=sample,
                new_status=sample.status,
                changed_by=request.user,
                notes="Sample received and entered into system"
            )
            
            messages.success(request, f"Sample {sample.sample_id} has been successfully received and entered into the system.")
            return redirect('operations:sample_detail', sample_id=sample.sample_id)
    else:
        form = SampleIntakeForm()
        client_form = ClientForm()
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'New Sample Intake',
        'form': form,
        'client_form': client_form,
    })
    return render(request, 'operations/new_sample_intake.html', context)


@login_required
def quick_sample_intake(request):
    """Quick Sample Intake - Simplified form for walk-in clients"""
    if not check_operations_access(request.user):
        raise PermissionDenied("Operations access required")
    
    if request.method == 'POST':
        form = QuickSampleIntakeForm(request.POST)
        
        if form.is_valid():
            # Create or get client
            client_name = form.cleaned_data['client_name']
            contact_phone = form.cleaned_data.get('contact_phone', '')
            
            client, created = Client.objects.get_or_create(
                name=client_name,
                defaults={
                    'phone': contact_phone,
                    'contact_person': client_name
                }
            )
            
            # Create sample
            sample = form.save(commit=False)
            sample.client = client
            sample.received_by = request.user
            sample.status = 'received'
            sample.save()
            
            # Create status history entry
            SampleStatusHistory.objects.create(
                sample=sample,
                new_status=sample.status,
                changed_by=request.user,
                notes="Quick sample intake - tests to be added later"
            )
            
            messages.success(request, f"Sample {sample.sample_id} has been quickly received. You can add tests later.")
            return redirect('operations:sample_detail', sample_id=sample.sample_id)
    else:
        form = QuickSampleIntakeForm()
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Quick Sample Intake',
        'form': form,
    })
    return render(request, 'operations/quick_sample_intake.html', context)


@login_required
def sample_detail(request, sample_id):
    """Sample Detail View - Available to all roles"""
    if not check_operations_access(request.user):
        raise PermissionDenied("Operations access required")
    
    sample = get_object_or_404(Sample, sample_id=sample_id)
    sample_tests = SampleTest.objects.filter(sample=sample).select_related('test_item')
    status_history = SampleStatusHistory.objects.filter(sample=sample).order_by('-changed_at')
    
    # Status update form
    if request.method == 'POST' and 'update_status' in request.POST:
        status_form = SampleStatusUpdateForm(request.POST, instance=sample)
        if status_form.is_valid():
            old_status = sample.status
            sample = status_form.save()
            
            # Create status history entry
            SampleStatusHistory.objects.create(
                sample=sample,
                old_status=old_status,
                new_status=sample.status,
                changed_by=request.user,
                notes=request.POST.get('status_notes', '')
            )
            
            messages.success(request, f"Sample status updated to {sample.get_status_display()}")
            return redirect('operations:sample_detail', sample_id=sample.sample_id)
    else:
        status_form = SampleStatusUpdateForm(instance=sample)
    
    context = get_base_context(request.user)
    context.update({
        'page_title': f'Sample {sample.sample_id}',
        'sample': sample,
        'sample_tests': sample_tests,
        'status_history': status_history,
        'status_form': status_form,
    })
    return render(request, 'operations/sample_detail.html', context)


@login_required
def add_tests_to_sample(request, sample_id):
    """Add tests to existing sample - Available to all roles"""
    if not check_operations_access(request.user):
        raise PermissionDenied("Operations access required")
    
    sample = get_object_or_404(Sample, sample_id=sample_id)
    
    if request.method == 'POST':
        form = SampleTestForm(request.POST)
        if form.is_valid():
            test_item = form.cleaned_data['test_item']
            quantity_requested = form.cleaned_data['quantity_requested']
            special_requirements = form.cleaned_data['special_requirements']
            
            # Check if test already exists for this sample
            if SampleTest.objects.filter(sample=sample, test_item=test_item).exists():
                messages.warning(request, f"Test {test_item.test_name} is already assigned to this sample.")
            else:
                SampleTest.objects.create(
                    sample=sample,
                    test_item=test_item,
                    quantity_requested=quantity_requested,
                    special_requirements=special_requirements
                )
                messages.success(request, f"Test {test_item.test_name} has been added to the sample.")
            
            return redirect('operations:sample_detail', sample_id=sample.sample_id)
    else:
        form = SampleTestForm()
    
    context = get_base_context(request.user)
    context.update({
        'page_title': f'Add Tests to Sample {sample.sample_id}',
        'sample': sample,
        'form': form,
    })
    return render(request, 'operations/add_tests_to_sample.html', context)


def check_client_management_access(user):
    """Check if user can manage clients (Office Staff, Lab Manager, Directors only - not Technicians)"""
    return user.role in ['office_staff', 'lab_manager', 'director']


@login_required
def client_management(request):
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
    return render(request, 'operations/client_management.html', context)


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
            return redirect('operations:client_detail', client_id=client.id)
    else:
        form = ClientForm()
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Create New Client',
        'form': form,
        'action': 'create',
    })
    return render(request, 'operations/client_form.html', context)


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
    return render(request, 'operations/client_detail.html', context)


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
            return redirect('operations:client_detail', client_id=client.id)
    else:
        form = ClientForm(instance=client)
    
    context = get_base_context(request.user)
    context.update({
        'page_title': f'Edit Client: {client.name}',
        'form': form,
        'client': client,
        'action': 'update',
    })
    return render(request, 'operations/client_form.html', context)


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
        
        return redirect('operations:client_management')
    
    context = get_base_context(request.user)
    context.update({
        'page_title': f'Delete Client: {client.name}',
        'client': client,
        'has_samples': client.samples.exists(),
    })
    return render(request, 'operations/client_delete.html', context)
