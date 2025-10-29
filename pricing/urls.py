from django.urls import path
from . import views

app_name = 'pricing'

urlpatterns = [
    path('', views.pricing_dashboard, name='dashboard'),
    path('catalog/', views.catalog, name='catalog'),
    path('price-list/', views.master_price_list, name='master_price_list'),
    path('categories/', views.categories, name='categories'),
    path('tests-parameters/', views.tests_parameters, name='tests_parameters'),
    path('search-filter/', views.search_filter, name='search_filter'),
    path('pricing-rules/', views.pricing_rules, name='pricing_rules'),
    path('discount-schemes/', views.discount_schemes, name='discount_schemes'),
]
