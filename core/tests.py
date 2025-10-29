from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError

User = get_user_model()


class UserModelTestCase(TestCase):
    """Test the custom User model and its methods"""
    
    def setUp(self):
        """Set up test data"""
        self.director = User.objects.create_user(
            username='director_test',
            email='director@metabuildlab.com',
            password='testpass123',
            role='director',
            department='Management'
        )
        
        self.lab_manager = User.objects.create_user(
            username='labmanager_test',
            email='labmanager@metabuildlab.com',
            password='testpass123',
            role='lab_manager',
            department='Laboratory'
        )
        
        self.office_staff = User.objects.create_user(
            username='officestaff_test',
            email='office@metabuildlab.com',
            password='testpass123',
            role='office_staff',
            department='Administration'
        )
        
        self.technician = User.objects.create_user(
            username='technician_test',
            email='tech@metabuildlab.com',
            password='testpass123',
            role='technician',
            department='Laboratory'
        )
    
    def test_user_creation(self):
        """Test that users are created with correct attributes"""
        self.assertEqual(self.director.role, 'director')
        self.assertEqual(self.lab_manager.role, 'lab_manager')
        self.assertEqual(self.office_staff.role, 'office_staff')
        self.assertEqual(self.technician.role, 'technician')
    
    def test_role_properties(self):
        """Test role property methods"""
        # Director
        self.assertTrue(self.director.is_director)
        self.assertFalse(self.director.is_lab_manager)
        self.assertFalse(self.director.is_office_staff)
        self.assertFalse(self.director.is_technician)
        
        # Lab Manager
        self.assertFalse(self.lab_manager.is_director)
        self.assertTrue(self.lab_manager.is_lab_manager)
        self.assertFalse(self.lab_manager.is_office_staff)
        self.assertFalse(self.lab_manager.is_technician)
        
        # Office Staff
        self.assertFalse(self.office_staff.is_director)
        self.assertFalse(self.office_staff.is_lab_manager)
        self.assertTrue(self.office_staff.is_office_staff)
        self.assertFalse(self.office_staff.is_technician)
        
        # Technician
        self.assertFalse(self.technician.is_director)
        self.assertFalse(self.technician.is_lab_manager)
        self.assertFalse(self.technician.is_office_staff)
        self.assertTrue(self.technician.is_technician)
    
    def test_module_access_permissions(self):
        """Test module access for different roles"""
        # Director - should have access to all modules
        director_modules = self.director.get_accessible_modules()
        expected_director_modules = ['sales', 'operations', 'pricing', 'finance', 'config']
        self.assertEqual(set(director_modules), set(expected_director_modules))
        
        # Lab Manager - should have access to most modules except some config
        lab_manager_modules = self.lab_manager.get_accessible_modules()
        expected_lab_manager_modules = ['sales', 'operations', 'pricing', 'finance', 'config']
        self.assertEqual(set(lab_manager_modules), set(expected_lab_manager_modules))
        
        # Office Staff - should not have access to all modules
        office_modules = self.office_staff.get_accessible_modules()
        expected_office_modules = ['sales', 'pricing', 'finance']
        self.assertEqual(set(office_modules), set(expected_office_modules))
        
        # Technician - should have limited access
        tech_modules = self.technician.get_accessible_modules()
        expected_tech_modules = ['operations', 'pricing']
        self.assertEqual(set(tech_modules), set(expected_tech_modules))
    
    def test_specific_module_access(self):
        """Test can_access_module method for specific modules"""
        # Sales module
        self.assertTrue(self.director.can_access_module('sales'))
        self.assertTrue(self.lab_manager.can_access_module('sales'))
        self.assertTrue(self.office_staff.can_access_module('sales'))
        self.assertFalse(self.technician.can_access_module('sales'))
        
        # Operations module
        self.assertTrue(self.director.can_access_module('operations'))
        self.assertTrue(self.lab_manager.can_access_module('operations'))
        self.assertFalse(self.office_staff.can_access_module('operations'))
        self.assertTrue(self.technician.can_access_module('operations'))
        
        # Finance module
        self.assertTrue(self.director.can_access_module('finance'))
        self.assertTrue(self.lab_manager.can_access_module('finance'))
        self.assertTrue(self.office_staff.can_access_module('finance'))
        self.assertFalse(self.technician.can_access_module('finance'))
        
        # Config module
        self.assertTrue(self.director.can_access_module('config'))
        self.assertTrue(self.lab_manager.can_access_module('config'))
        self.assertFalse(self.office_staff.can_access_module('config'))
        self.assertFalse(self.technician.can_access_module('config'))
    
    def test_user_string_representation(self):
        """Test __str__ method"""
        expected = f"{self.director.get_full_name() or self.director.username} ({self.director.get_role_display()})"
        self.assertEqual(str(self.director), expected)


class AuthenticationTestCase(TestCase):
    """Test authentication and access control"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.director = User.objects.create_user(
            username='director_auth',
            email='director@test.com',
            password='testpass123',
            role='director'
        )
        
        self.technician = User.objects.create_user(
            username='tech_auth',
            email='tech@test.com',
            password='testpass123',
            role='technician'
        )
    
    def test_login_required_views(self):
        """Test that views require authentication"""
        # Test some key URLs that should require login
        protected_urls = [
            reverse('home'),
            reverse('config:dashboard'),
            reverse('pricing:dashboard'),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            # Should redirect to login page
            self.assertEqual(response.status_code, 302)
            self.assertIn('/accounts/login/', response.url)
    
    def test_successful_login_redirect(self):
        """Test successful login redirects to home"""
        response = self.client.post(reverse('login'), {
            'username': 'director_auth',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        # Should redirect to home page after login
        self.assertEqual(response.url, '/')
    
    def test_role_based_access_control(self):
        """Test that role-based access control works"""
        # Login as technician
        self.client.login(username='tech_auth', password='testpass123')
        
        # Technician should NOT have access to config
        response = self.client.get(reverse('config:dashboard'))
        # Should get permission denied (redirect or 403)
        self.assertIn(response.status_code, [302, 403])
        
        # Technician SHOULD have access to operations
        response = self.client.get(reverse('operations:dashboard'))
        self.assertEqual(response.status_code, 200)


class HomeViewTestCase(TestCase):
    """Test the home dashboard view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.director = User.objects.create_user(
            username='director_home',
            email='director@test.com',
            password='testpass123',
            role='director'
        )
    
    def test_home_view_authenticated(self):
        """Test home view for authenticated user"""
        self.client.login(username='director_home', password='testpass123')
        response = self.client.get(reverse('home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Meta Build Lab')
        self.assertContains(response, 'Director')  # Role should be displayed
        
        # Check that accessible modules are in context
        self.assertIn('accessible_modules', response.context)
        self.assertIn('sales', response.context['accessible_modules'])
    
    def test_home_view_unauthenticated(self):
        """Test home view redirects for unauthenticated user"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class ModuleAccessTestCase(TestCase):
    """Test access to different modules based on roles"""
    
    def setUp(self):
        """Set up test users"""
        self.client = Client()
        
        # Create users for each role
        self.users = {
            'director': User.objects.create_user(
                username='director_module',
                password='testpass123',
                role='director'
            ),
            'lab_manager': User.objects.create_user(
                username='labmanager_module',
                password='testpass123',
                role='lab_manager'
            ),
            'office_staff': User.objects.create_user(
                username='office_module',
                password='testpass123',
                role='office_staff'
            ),
            'technician': User.objects.create_user(
                username='tech_module',
                password='testpass123',
                role='technician'
            )
        }
    
    def test_config_module_access(self):
        """Test config module access by role"""
        # Director and Lab Manager should have access
        for role in ['director', 'lab_manager']:
            self.client.login(username=f'{role}_module', password='testpass123')
            response = self.client.get(reverse('config:dashboard'))
            self.assertEqual(response.status_code, 200, f"{role} should access config")
            self.client.logout()
        
        # Office Staff and Technician should NOT have access
        for role in ['office_staff', 'technician']:
            self.client.login(username=f'{role}_module', password='testpass123')
            response = self.client.get(reverse('config:dashboard'))
            # Should be redirected or get permission denied
            self.assertIn(response.status_code, [302, 403], f"{role} should NOT access config")
            self.client.logout()
    
    def test_operations_module_access(self):
        """Test operations module access by role"""
        # Director, Lab Manager, and Technician should have access
        for role in ['director', 'lab_manager', 'technician']:
            self.client.login(username=f'{role}_module', password='testpass123')
            response = self.client.get(reverse('operations:dashboard'))
            self.assertEqual(response.status_code, 200, f"{role} should access operations")
            self.client.logout()
        
        # Office Staff should NOT have access
        self.client.login(username='office_module', password='testpass123')
        response = self.client.get(reverse('operations:dashboard'))
        self.assertIn(response.status_code, [302, 403], "office_staff should NOT access operations")
    
    def test_pricing_module_access(self):
        """Test pricing module access by role"""
        # All roles should have some level of access to pricing
        for role in ['director', 'lab_manager', 'office_staff', 'technician']:
            self.client.login(username=f'{role}_module', password='testpass123')
            response = self.client.get(reverse('pricing:dashboard'))
            self.assertEqual(response.status_code, 200, f"{role} should access pricing")
            self.client.logout()