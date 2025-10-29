from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin interface with role-based access management
    """
    
    # Fields to display in the user list
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'department', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    ordering = ('username',)
    
    # Add role field to the user editing form
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Meta Build Lab Info', {
            'fields': ('role', 'phone', 'department'),
            'description': 'Role-based access and contact information'
        }),
    )
    
    # Add role field to the user creation form
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Meta Build Lab Info', {
            'fields': ('role', 'phone', 'department'),
        }),
    )
    
    def get_queryset(self, request):
        """Limit queryset based on user permissions"""
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        # Directors can see all users, others only see users in their department
        if hasattr(request.user, 'is_director') and request.user.is_director:
            return queryset
        return queryset.filter(department=request.user.department)
