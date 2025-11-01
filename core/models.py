from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    with role-based access for Meta Build Lab staff
    """
    
    ROLE_CHOICES = [
        ('director', 'Director'),
        ('lab_manager', 'Lab Manager'),
        ('office_staff', 'Office Staff'),
        ('technician', 'Technician'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='office_staff',
        help_text='User role determines access permissions within the system'
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Contact phone number'
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text='Department or specialization area'
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user should be treated as active. '
                  'Unselect this instead of deleting accounts.'
    )
    
    # Note: date_joined is already inherited from AbstractUser
    # We'll add profile tracking later after resolving migration issues
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    def get_role_display(self):
        """Return the display name for the user's role"""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
    
    @property
    def is_director(self):
        """Check if user is a Director (full access)"""
        return self.role == 'director'
    
    @property
    def is_lab_manager(self):
        """Check if user is a Lab Manager"""
        return self.role == 'lab_manager'
    
    @property
    def is_office_staff(self):
        """Check if user is Office Staff"""
        return self.role == 'office_staff'
    
    @property
    def is_technician(self):
        """Check if user is a Technician"""
        return self.role == 'technician'
    
    def can_access_module(self, module_name):
        """
        Check if user can access a specific module based on their role
        
        Args:
            module_name (str): Name of the module ('sales', 'operations', etc.)
            
        Returns:
            bool: True if user can access the module
        """
        access_matrix = {
            'director': ['sales', 'operations', 'pricing', 'finance', 'config'],
            'lab_manager': ['sales', 'operations', 'pricing', 'finance'],  # Added sales for client management
            'office_staff': ['sales', 'operations', 'finance'],  # Added operations for sample intake
            'technician': ['operations'],
        }
        
        return module_name in access_matrix.get(self.role, [])
    
    def get_accessible_modules(self):
        """
        Get list of modules this user can access
        
        Returns:
            list: List of accessible module names
        """
        access_matrix = {
            'director': ['sales', 'operations', 'pricing', 'finance', 'config'],
            'lab_manager': ['sales', 'operations', 'pricing', 'finance'],  # Added sales for client management
            'office_staff': ['sales', 'operations', 'finance'],  # Added operations for sample intake
            'technician': ['operations'],
        }
        
        return access_matrix.get(self.role, [])
