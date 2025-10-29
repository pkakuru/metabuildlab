from django.urls import path
from . import views

app_name = 'config'

urlpatterns = [
    path('', views.config_dashboard, name='dashboard'),
    path('administration/', views.administration, name='administration'),
    path('users-roles/', views.users_roles, name='users_roles'),
    path('labs-instruments/', views.labs_instruments, name='labs_instruments'),
    path('test-catalog/', views.test_catalog_config, name='test_catalog_config'),
    path('pricing-rules/', views.pricing_rules_config, name='pricing_rules_config'),
    path('audit-log/', views.audit_log, name='audit_log'),
]
