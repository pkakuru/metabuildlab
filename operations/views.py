from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Client, Sample, SampleTest, SampleStatusHistory, Job, SampleReceiptForm
from .forms import ClientForm, SampleIntakeForm, QuickSampleIntakeForm, SampleTestForm, SampleStatusUpdateForm, JobCreateForm, SampleReceiptFormForm
from pricing.models import TestItem
from core.models import User


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
    
    # Add manager/director progress tracking data
    if user.role in ['director', 'lab_manager', 'office_staff']:
        from django.db.models import Count, Q
        from datetime import timedelta
        
        # Get all active jobs with progress tracking
        all_jobs = Job.objects.select_related('sample', 'assigned_to', 'sample__client').all()
        
        # Jobs by status
        jobs_by_status = all_jobs.values('status').annotate(count=Count('id'))
        status_counts = {item['status']: item['count'] for item in jobs_by_status}
        
        # Recent job updates (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_updates = all_jobs.filter(
            updated_at__gte=week_ago
        ).order_by('-updated_at')[:10]
        
        # Samples in progress
        samples_in_progress = Sample.objects.filter(
            status__in=['received', 'assigned', 'in_progress', 'testing']
        ).select_related('client').prefetch_related('jobs').annotate(
            job_count=Count('jobs')
        ).order_by('-received_date')[:10]
        
        # Progress metrics
        total_active_samples = Sample.objects.filter(
            status__in=['received', 'assigned', 'in_progress', 'testing']
        ).count()
        
        samples_at_stage = {
            'received': Sample.objects.filter(status='received').count(),
            'assigned': Sample.objects.filter(status='assigned').count(),
            'in_progress': Sample.objects.filter(status='in_progress').count(),
            'testing': Sample.objects.filter(status='testing').count(),
        }
        
        context.update({
            'status_counts': status_counts,
            'recent_updates': recent_updates,
            'samples_in_progress': samples_in_progress,
            'total_active_samples': total_active_samples,
            'samples_at_stage': samples_at_stage,
        })
    
    # Add technician-specific personalized data
    if user.role == 'technician':
        from django.db.models import Count, Q
        from datetime import timedelta
        
        # Get technician's jobs
        my_jobs = Job.objects.filter(assigned_to=user)
        
        # Calculate statistics
        total_assigned = my_jobs.count()
        assigned_status = my_jobs.filter(status='assigned').count()
        in_progress = my_jobs.filter(status='in_progress').count()
        completed = my_jobs.filter(status='completed').count()
        
        # Jobs due today and overdue
        today = timezone.now().date()
        due_today = my_jobs.filter(due_date=today, status__in=['assigned', 'in_progress', 'pending']).count()
        overdue = my_jobs.filter(due_date__lt=today, status__in=['assigned', 'in_progress', 'pending']).count()
        
        # Completed today
        completed_today = my_jobs.filter(
            status='completed',
            completed_date__date=today
        ).count()
        
        # Completed this week
        week_ago = today - timedelta(days=7)
        completed_this_week = my_jobs.filter(
            status='completed',
            completed_date__date__gte=week_ago
        ).count()
        
        # Pending tests (jobs with tests not yet completed)
        pending_tests_count = 0
        for job in my_jobs.filter(status__in=['assigned', 'in_progress']):
            pending_tests = job.assigned_tests.filter(is_completed=False).count()
            pending_tests_count += pending_tests
        
        # Recent jobs (last 5)
        recent_jobs = my_jobs.select_related('sample', 'sample__client').order_by('-created_at')[:5]
        
        # Performance metrics
        # Average completion time for completed jobs
        completed_jobs_with_dates = my_jobs.filter(
            status='completed',
            started_date__isnull=False,
            completed_date__isnull=False
        )
        
        avg_completion_days = None
        if completed_jobs_with_dates.exists():
            total_days = 0
            count = 0
            for job in completed_jobs_with_dates:
                if job.started_date and job.completed_date:
                    days = (job.completed_date.date() - job.started_date.date()).days
                    total_days += days
                    count += 1
            if count > 0:
                avg_completion_days = round(total_days / count, 1)
        
        # Workload distribution
        jobs_by_priority = my_jobs.filter(status__in=['assigned', 'in_progress', 'pending']).values('priority').annotate(count=Count('id'))
        
        context.update({
            'total_assigned': total_assigned,
            'assigned_status': assigned_status,
            'in_progress': in_progress,
            'completed': completed,
            'due_today': due_today,
            'overdue': overdue,
            'completed_today': completed_today,
            'completed_this_week': completed_this_week,
            'pending_tests_count': pending_tests_count,
            'recent_jobs': recent_jobs,
            'avg_completion_days': avg_completion_days,
            'jobs_by_priority': jobs_by_priority,
        })
    
    return render(request, 'operations/dashboard.html', context)


@login_required
def technician_dashboard(request):
    """
    Shared Technician Dashboard - Common information for all technicians
    """
    if not check_operations_access(request.user) or request.user.role != 'technician':
        raise PermissionDenied("Technician access required")
    
    from django.db.models import Count, Q
    from datetime import timedelta
    
    # Shared statistics across all technicians
    all_jobs = Job.objects.filter(assigned_to__role='technician')
    all_active_jobs = all_jobs.exclude(status__in=['completed', 'cancelled'])
    
    # Lab-wide statistics
    total_lab_jobs = all_active_jobs.count()
    lab_jobs_by_status = all_active_jobs.values('status').annotate(count=Count('id'))
    
    # Recent lab activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_lab_activity = Job.objects.filter(
        created_at__gte=week_ago,
        assigned_to__role='technician'
    ).select_related('sample', 'sample__client', 'assigned_to').order_by('-created_at')[:10]
    
    # Most active technicians (by job count)
    from core.models import User
    active_technicians = User.objects.filter(
        role='technician',
        is_active=True
    ).annotate(
        job_count=Count('assigned_jobs', filter=Q(assigned_jobs__status__in=['assigned', 'in_progress', 'pending']))
    ).order_by('-job_count')[:5]
    
    # Common samples received this week
    week_samples = Sample.objects.filter(
        received_date__gte=week_ago,
        status__in=['received', 'in_progress', 'testing']
    ).select_related('client').order_by('-received_date')[:10]
    
    # Lab equipment/announcements placeholder
    # (This would come from a separate model in a real system)
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Technician Dashboard',
        'total_lab_jobs': total_lab_jobs,
        'lab_jobs_by_status': lab_jobs_by_status,
        'recent_lab_activity': recent_lab_activity,
        'active_technicians': active_technicians,
        'week_samples': week_samples,
    })
    
    return render(request, 'operations/technician_dashboard.html', context)


@login_required  
def job_board(request):
    """Job Board - All Jobs (Director, Lab Manager) or filtered (Office Staff)"""
    if not check_operations_access(request.user):
        raise PermissionDenied("Operations access required")
    
    # Office Staff can now access job board but see all jobs
    jobs = Job.objects.select_related('sample', 'assigned_to', 'created_by', 'sample__client').all()
    
    # Apply filters
    status_filter = request.GET.get('status', '')
    technician_filter = request.GET.get('technician', '')
    priority_filter = request.GET.get('priority', '')
    
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    if technician_filter:
        jobs = jobs.filter(assigned_to_id=technician_filter)
    if priority_filter:
        jobs = jobs.filter(priority=priority_filter)
    
    jobs = jobs.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(jobs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    technicians = User.objects.filter(role='technician', is_active=True).order_by('username')
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Job Board - All Jobs' if request.user.role == 'director' else 'Job Board',
        'page_obj': page_obj,
        'jobs': page_obj,
        'technicians': technicians,
        'status_filter': status_filter,
        'technician_filter': technician_filter,
        'priority_filter': priority_filter,
        'status_choices': Job.STATUS_CHOICES,
        'priority_choices': Sample.PRIORITY_CHOICES,
    })
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
    
    # Get jobs assigned to this technician
    jobs = Job.objects.filter(
        assigned_to=request.user
    ).select_related('sample', 'sample__client', 'created_by').prefetch_related('assigned_tests').order_by('-created_at')
    
    # Apply filters
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    if priority_filter:
        jobs = jobs.filter(priority=priority_filter)
    
    # Get statistics
    total_jobs = jobs.count()
    pending_jobs = jobs.filter(status='pending').count()
    in_progress_jobs = jobs.filter(status='in_progress').count()
    assigned_jobs = jobs.filter(status='assigned').count()
    completed_jobs = jobs.filter(status='completed').count()
    
    # Pagination
    paginator = Paginator(jobs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'My Jobs',
        'page_obj': page_obj,
        'jobs': page_obj,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'status_choices': Job.STATUS_CHOICES,
        'priority_choices': Sample.PRIORITY_CHOICES,
        'total_jobs': total_jobs,
        'pending_jobs': pending_jobs,
        'in_progress_jobs': in_progress_jobs,
        'assigned_jobs': assigned_jobs,
        'completed_jobs': completed_jobs,
    })
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


def check_job_creation_access(user):
    """Check if user can create jobs (Directors, Lab Managers, Office Staff - not Technicians)"""
    return user.role in ['director', 'lab_manager', 'office_staff']


@login_required
def available_samples(request):
    """View available samples that can be assigned as jobs"""
    if not check_job_creation_access(request.user):
        raise PermissionDenied("Only Directors, Lab Managers, and Office Staff can create jobs.")
    
    # Get samples that have requested tests but no assigned jobs (or incomplete jobs)
    samples = Sample.objects.filter(
        requested_tests__isnull=False
    ).exclude(
        status='cancelled'
    ).select_related('client', 'received_by').prefetch_related(
        'requested_tests', 'jobs'
    ).distinct()
    
    # Filter: only show samples without jobs or with all jobs completed/cancelled
    available_samples_list = []
    for sample in samples:
        active_jobs = sample.jobs.exclude(status__in=['completed', 'cancelled']).count()
        if active_jobs == 0:
            available_samples_list.append(sample)
    
    # Apply search filter
    search_query = request.GET.get('search', '')
    if search_query:
        available_samples_list = [
            s for s in available_samples_list 
            if search_query.lower() in s.sample_id.lower() 
            or search_query.lower() in s.client.name.lower()
            or search_query.lower() in s.sample_type.lower()
        ]
    
    # Pagination
    paginator = Paginator(available_samples_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Available Samples for Job Creation',
        'page_obj': page_obj,
        'samples': page_obj,
        'search_query': search_query,
    })
    return render(request, 'operations/available_samples.html', context)


@login_required
def create_job(request, sample_id):
    """Create a job from a sample and assign to technician"""
    if not check_job_creation_access(request.user):
        raise PermissionDenied("Only Directors, Lab Managers, and Office Staff can create jobs.")
    
    sample = get_object_or_404(Sample, sample_id=sample_id)
    
    # Check if sample has requested tests
    if not sample.requested_tests.exists():
        messages.error(request, f"Sample {sample.sample_id} has no requested tests. Please add tests first.")
        return redirect('operations:sample_detail', sample_id=sample.sample_id)
    
    if request.method == 'POST':
        form = JobCreateForm(request.POST, sample=sample)
        if form.is_valid():
            # Create the job
            job = Job.objects.create(
                sample=sample,
                assigned_to=form.cleaned_data['assigned_to'],
                created_by=request.user,
                priority=form.cleaned_data['priority'],
                due_date=form.cleaned_data.get('due_date'),
                instructions=form.cleaned_data.get('instructions', ''),
                status='assigned'
            )
            
            # Assign selected tests
            assigned_tests = form.cleaned_data['assigned_tests']
            job.assigned_tests.set(assigned_tests)
            
            # Update job assignment
            job.assign_to_technician(job.assigned_to, job.due_date)
            
            # Update sample status to in_progress if it was received
            if sample.status == 'received':
                sample.status = 'in_progress'
                sample.save()
                SampleStatusHistory.objects.create(
                    sample=sample,
                    old_status='received',
                    new_status='in_progress',
                    changed_by=request.user,
                    notes=f'Job {job.job_id} created and assigned to {job.assigned_to.get_full_name() or job.assigned_to.username}'
                )
            
            messages.success(request, f"Job {job.job_id} has been created and assigned to {job.assigned_to.get_full_name() or job.assigned_to.username}.")
            return redirect('operations:job_detail', job_id=job.job_id)
    else:
        form = JobCreateForm(sample=sample)
    
    # Get sample tests
    sample_tests = SampleTest.objects.filter(sample=sample).select_related('test_item')
    
    context = get_base_context(request.user)
    context.update({
        'page_title': f'Create Job from Sample {sample.sample_id}',
        'form': form,
        'sample': sample,
        'sample_tests': sample_tests,
    })
    return render(request, 'operations/create_job.html', context)


@login_required
def job_detail(request, job_id):
    """View job details"""
    if not check_operations_access(request.user):
        raise PermissionDenied("Operations access required")
    
    job = get_object_or_404(Job, job_id=job_id)
    assigned_tests = job.assigned_tests.select_related('test_item').all()
    
    # Check if user is the assigned technician
    is_assigned_technician = (request.user.role == 'technician' and 
                             job.assigned_to == request.user)
    
    context = get_base_context(request.user)
    context.update({
        'page_title': f'Job {job.job_id}',
        'job': job,
        'assigned_tests': assigned_tests,
        'can_manage_jobs': check_job_creation_access(request.user),
        'is_assigned_technician': is_assigned_technician,
        'today': timezone.now().date(),
    })
    return render(request, 'operations/job_detail.html', context)


@login_required
def update_job_status(request, job_id):
    """Update job status - Technician action"""
    if not check_operations_access(request.user) or request.user.role != 'technician':
        raise PermissionDenied("Only assigned technicians can update job status")
    
    job = get_object_or_404(Job, job_id=job_id)
    
    # Verify technician is assigned to this job
    if job.assigned_to != request.user:
        messages.error(request, "You are not assigned to this job.")
        return redirect('operations:my_jobs')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'start':
            if job.start_work(request.user):
                messages.success(request, f"You have started work on job {job.job_id}.")
            else:
                messages.error(request, "Cannot start work on this job. It may already be in progress or completed.")
        
        elif action == 'complete':
            if job.complete_job(request.user):
                messages.success(request, f"Job {job.job_id} has been marked as completed. Great work!")
            else:
                messages.error(request, "Cannot complete this job. Work must be started first.")
        
        elif action == 'hold':
            notes = request.POST.get('hold_notes', '')
            if job.put_on_hold(request.user, notes):
                messages.info(request, f"Job {job.job_id} has been put on hold.")
            else:
                messages.error(request, "Cannot put this job on hold in its current status.")
        
        elif action == 'resume':
            if job.resume_work(request.user):
                messages.success(request, f"Work resumed on job {job.job_id}.")
            else:
                messages.error(request, "Cannot resume this job. It must be on hold first.")
        else:
            messages.error(request, "Invalid action.")
        
        return redirect('operations:job_detail', job_id=job.job_id)
    
    return redirect('operations:job_detail', job_id=job.job_id)


# Sample Receipt Form (SRF) Views
@login_required
def create_receipt_form(request, sample_id=None):
    """Create a Sample Receipt Form (SRF) for one or more samples"""
    if not check_operations_access(request.user):
        raise PermissionDenied("Operations access required")
    
    from django.db.models import Q
    
    if request.method == 'POST':
        form = SampleReceiptFormForm(request.POST, user=request.user)
        if form.is_valid():
            srf = form.save(commit=False)
            srf.received_by = request.user
            if not srf.received_by_name:
                srf.received_by_name = request.user.get_full_name() or request.user.username
            srf.save()
            
            # Add selected samples
            samples = form.cleaned_data['samples']
            srf.samples.set(samples)
            
            messages.success(request, f"Sample Receipt Form {srf.receipt_number} created successfully.")
            return redirect('operations:receipt_form_detail', receipt_number=srf.receipt_number)
    else:
        sample_ids = None
        if sample_id:
            # Verify sample exists and is in received status
            sample_obj = get_object_or_404(Sample, sample_id=sample_id)
            if sample_obj.status != 'received':
                messages.warning(request, f"Sample {sample_id} is not in 'received' status. Only received samples can have receipt forms.")
            elif sample_obj.receipt_forms.exists():
                messages.info(request, f"Sample {sample_id} already has a receipt form.")
            else:
                sample_ids = [sample_obj.id]
        form = SampleReceiptFormForm(user=request.user, sample_ids=sample_ids)
        
        # Pre-select the sample if provided
        if sample_ids and form.fields['samples'].queryset.filter(id__in=sample_ids).exists():
            form.fields['samples'].initial = sample_ids
    
    # Get available samples for selection
    available_samples = Sample.objects.filter(
        status='received'
    ).exclude(
        receipt_forms__isnull=False
    ).select_related('client', 'received_by')
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Create Sample Receipt Form',
        'form': form,
        'available_samples': available_samples,
        'initial_sample_id': sample_id,
    })
    return render(request, 'operations/create_receipt_form.html', context)


@login_required
def receipt_form_detail(request, receipt_number):
    """View Sample Receipt Form details"""
    if not check_operations_access(request.user):
        raise PermissionDenied("Operations access required")
    
    srf = get_object_or_404(SampleReceiptForm, receipt_number=receipt_number)
    samples = srf.samples.select_related('client', 'received_by').prefetch_related('requested_tests').all()
    
    # Get test details for each sample
    sample_tests = {}
    for sample in samples:
        sample_tests[sample.id] = SampleTest.objects.filter(sample=sample).select_related('test_item')
    
    context = get_base_context(request.user)
    context.update({
        'page_title': f'Sample Receipt Form {srf.receipt_number}',
        'srf': srf,
        'samples': samples,
        'sample_tests': sample_tests,
    })
    return render(request, 'operations/receipt_form_detail.html', context)


@login_required
def receipt_form_pdf(request, receipt_number):
    """Generate PDF for Sample Receipt Form"""
    if not check_operations_access(request.user):
        raise PermissionDenied("Operations access required")
    
    srf = get_object_or_404(SampleReceiptForm, receipt_number=receipt_number)
    samples = srf.samples.select_related('client', 'received_by').prefetch_related('requested_tests').all()
    
    # Get test details for each sample
    sample_tests = {}
    for sample in samples:
        sample_tests[sample.id] = SampleTest.objects.filter(sample=sample).select_related('test_item')
    
    context = {
        'srf': srf,
        'samples': samples,
        'sample_tests': sample_tests,
    }
    
    # Render HTML template
    html_content = render_to_string('operations/receipt_form_pdf.html', context, request)
    
    # Generate PDF using weasyprint (if available) or return HTML
    try:
        import weasyprint
        pdf_file = weasyprint.HTML(string=html_content).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="SRF-{receipt_number}.pdf"'
        
        # Mark as PDF generated
        srf.pdf_generated = True
        srf.save(update_fields=['pdf_generated'])
        
        return response
    except ImportError:
        # If weasyprint is not installed, return HTML version
        messages.warning(request, "PDF generation requires weasyprint. Showing HTML version.")
        return render(request, 'operations/receipt_form_pdf.html', context)


@login_required
def receipt_form_list(request):
    """List all Sample Receipt Forms"""
    if not check_operations_access(request.user):
        raise PermissionDenied("Operations access required")
    
    from django.db.models import Count
    
    receipts = SampleReceiptForm.objects.select_related('received_by').annotate(
        sample_count=Count('samples')
    ).order_by('-receipt_date')
    
    # Apply filters
    search_query = request.GET.get('search', '')
    if search_query:
        receipts = receipts.filter(
            Q(receipt_number__icontains=search_query) |
            Q(delivered_by__icontains=search_query) |
            Q(project_reference__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(receipts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Sample Receipt Forms',
        'page_obj': page_obj,
        'receipts': page_obj,
        'search_query': search_query,
    })
    return render(request, 'operations/receipt_form_list.html', context)


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
