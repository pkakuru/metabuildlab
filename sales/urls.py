from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sales_dashboard, name='dashboard'),
    path('quotations/', views.quotations, name='quotations'),
    path('quotations/new/', views.new_quotation, name='new_quotation'),
    path('quotations/kanban/', views.quotation_kanban, name='quotation_kanban'),
    path('activity/', views.activity_log, name='activity_log'),
    # Client Management CRUD (Office Staff, Lab Manager, Directors)
    path('clients/', views.clients, name='clients'),
    path('clients/new/', views.client_create, name='client_create'),
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('clients/<int:client_id>/edit/', views.client_update, name='client_update'),
    path('clients/<int:client_id>/delete/', views.client_delete, name='client_delete'),
    path('leads/', views.leads, name='leads'),
    path('contracts/', views.contracts, name='contracts'),
    path('reports/summary/', views.sales_summary, name='sales_summary'),
    path('reports/conversion/', views.conversion_rates, name='conversion_rates'),
]
