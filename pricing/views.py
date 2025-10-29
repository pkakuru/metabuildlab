from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import TestCategory, TestSubCategory, TestItem

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
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    subcategory_filter = request.GET.get('subcategory', '')
    sample_type_filter = request.GET.get('sample_type', '')
    active_filter = request.GET.get('active', '')
    
    # Build queryset
    test_items = TestItem.objects.select_related('category', 'subcategory').all()
    
    # Apply filters
    if search_query:
        test_items = test_items.filter(
            Q(test_name__icontains=search_query) |
            Q(display_code__icontains=search_query) |
            Q(system_code__icontains=search_query) |
            Q(method_standard__icontains=search_query)
        )
    
    if category_filter:
        test_items = test_items.filter(category_id=category_filter)
    
    if subcategory_filter:
        test_items = test_items.filter(subcategory_id=subcategory_filter)
    
    if sample_type_filter:
        test_items = test_items.filter(sample_type=sample_type_filter)
    
    if active_filter == 'true':
        test_items = test_items.filter(is_active=True)
    elif active_filter == 'false':
        test_items = test_items.filter(is_active=False)
    
    # Order by category and subcategory
    test_items = test_items.order_by('category__name', 'subcategory__name', 'test_name')
    
    # Pagination
    paginator = Paginator(test_items, 25)  # Show 25 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = TestCategory.objects.filter(is_active=True).order_by('name')
    subcategories = TestSubCategory.objects.filter(is_active=True).order_by('name')
    sample_types = TestItem.objects.values_list('sample_type', flat=True).distinct().order_by('sample_type')
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Master Price List',
        'can_edit': can_edit,
        'page_obj': page_obj,
        'test_items': page_obj,
        'categories': categories,
        'subcategories': subcategories,
        'sample_types': sample_types,
        'search_query': search_query,
        'category_filter': category_filter,
        'subcategory_filter': subcategory_filter,
        'sample_type_filter': sample_type_filter,
        'active_filter': active_filter,
        'total_items': paginator.count,
    })
    return render(request, 'pricing/master_price_list.html', context)

@login_required
def categories(request):
    # Director (full access), Lab Manager (full access)
    if not check_pricing_access(request.user):
        raise PermissionDenied("You don't have permission to access Categories.")
    
    if not (request.user.is_director or request.user.is_lab_manager):
        raise PermissionDenied("You don't have permission to access Categories.")
    
    # Get categories with their subcategories and test counts
    categories = TestCategory.objects.prefetch_related('subcategories').all().order_by('name')
    
    # Add test counts for each category and subcategory
    for category in categories:
        category.test_count = TestItem.objects.filter(category=category).count()
        for subcategory in category.subcategories.all():
            subcategory.test_count = TestItem.objects.filter(subcategory=subcategory).count()
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Test Categories',
        'categories': categories,
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
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    sample_type_filter = request.GET.get('sample_type', '')
    
    # Build queryset
    test_items = TestItem.objects.select_related('category', 'subcategory').all()
    
    # Apply filters
    if search_query:
        test_items = test_items.filter(
            Q(test_name__icontains=search_query) |
            Q(display_code__icontains=search_query) |
            Q(method_standard__icontains=search_query)
        )
    
    if category_filter:
        test_items = test_items.filter(category_id=category_filter)
    
    if sample_type_filter:
        test_items = test_items.filter(sample_type=sample_type_filter)
    
    # Order by category and subcategory
    test_items = test_items.order_by('category__name', 'subcategory__name', 'test_name')
    
    # Pagination
    paginator = Paginator(test_items, 30)  # Show 30 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = TestCategory.objects.filter(is_active=True).order_by('name')
    sample_types = TestItem.objects.values_list('sample_type', flat=True).distinct().order_by('sample_type')
    
    context = get_base_context(request.user)
    context.update({
        'page_title': 'Tests & Parameters',
        'can_edit': can_edit,
        'page_obj': page_obj,
        'test_items': page_obj,
        'categories': categories,
        'sample_types': sample_types,
        'search_query': search_query,
        'category_filter': category_filter,
        'sample_type_filter': sample_type_filter,
        'total_items': paginator.count,
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