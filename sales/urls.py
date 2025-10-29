from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sales_dashboard, name='dashboard'),
    path('quotations/', views.quotations, name='quotations'),
    path('quotations/new/', views.new_quotation, name='new_quotation'),
    path('quotations/kanban/', views.quotation_kanban, name='quotation_kanban'),
    path('activity/', views.activity_log, name='activity_log'),
    path('clients/', views.clients, name='clients'),
    path('leads/', views.leads, name='leads'),
    path('contracts/', views.contracts, name='contracts'),
    path('reports/summary/', views.sales_summary, name='sales_summary'),
    path('reports/conversion/', views.conversion_rates, name='conversion_rates'),
]
