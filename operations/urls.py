from django.urls import path
from . import views

app_name = 'operations'

urlpatterns = [
    path('', views.operations_dashboard, name='dashboard'),
    
    # General Operations (Director, Lab Manager, Office Staff)
    path('job-board/', views.job_board, name='job_board'),
    path('samples/', views.samples_intake, name='samples_intake'),
    path('results/review/', views.results_review, name='results_review'),
    path('turnaround/', views.turnaround_tracker, name='turnaround_tracker'),
    
    # Sample Intake (All Roles)
    path('sample-intake/', views.sample_intake_dashboard, name='sample_intake_dashboard'),
    path('samples/new/', views.new_sample_intake, name='new_sample_intake'),
    path('samples/quick/', views.quick_sample_intake, name='quick_sample_intake'),
    path('samples/<str:sample_id>/', views.sample_detail, name='sample_detail'),
    path('samples/<str:sample_id>/add-tests/', views.add_tests_to_sample, name='add_tests_to_sample'),
    
    # Client Management (All Roles)
    path('clients/', views.client_management, name='client_management'),
    
    # Director Only
    path('worklist/', views.technician_worklist, name='technician_worklist'),
    path('attachments/', views.attachments, name='attachments'),
    path('reports/', views.job_reports, name='job_reports'),
    
    # Technician Only
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('results/entry/', views.results_entry, name='results_entry'),
    path('my-attachments/', views.my_attachments, name='my_attachments'),
    path('activity/', views.activity_log, name='activity_log'),
]
