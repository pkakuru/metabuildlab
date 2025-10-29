from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.finance_dashboard, name='dashboard'),
    
    # Invoice Management
    path('invoices/', views.invoices, name='invoices'),
    path('invoices/new/', views.new_invoice, name='new_invoice'),
    path('payments/record/', views.record_payment, name='record_payment'),
    path('receipts/', views.receipts, name='receipts'),
    
    # Director Only - Advanced Billing
    path('credit-notes/', views.credit_notes, name='credit_notes'),
    path('statements/', views.statements, name='statements'),
    path('unpaid-ageing/', views.unpaid_ageing, name='unpaid_ageing'),
    
    # Reports (Director & Lab Manager)
    path('reports/revenue/', views.revenue_reports, name='revenue_reports'),
]
