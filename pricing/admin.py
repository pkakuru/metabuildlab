from django.contrib import admin
from .models import TestCategory, TestSubCategory, TestItem, PricingRule, DiscountScheme


@admin.register(TestCategory)
class TestCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(TestSubCategory)
class TestSubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'category__name']
    ordering = ['category', 'name']


@admin.register(TestItem)
class TestItemAdmin(admin.ModelAdmin):
    list_display = ['display_code', 'test_name', 'category', 'subcategory', 'price', 'currency', 'tat_days', 'is_active']
    list_filter = ['category', 'subcategory', 'currency', 'sample_type', 'is_active', 'created_at']
    search_fields = ['system_code', 'display_code', 'test_name', 'method_standard']
    ordering = ['category', 'subcategory', 'test_name']
    list_per_page = 50
    
    fieldsets = (
        ('Identifiers', {
            'fields': ('system_code', 'display_code')
        }),
        ('Categorization', {
            'fields': ('category', 'subcategory')
        }),
        ('Test Details', {
            'fields': ('test_name', 'method_standard', 'sample_type')
        }),
        ('Pricing', {
            'fields': ('price', 'currency', 'unit', 'tat_days')
        }),
        ('Additional Info', {
            'fields': ('notes', 'is_active')
        }),
    )


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_percentage', 'discount_amount', 'minimum_quantity', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(DiscountScheme)
class DiscountSchemeAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_percentage', 'minimum_order_value', 'valid_from', 'valid_to', 'is_active']
    list_filter = ['is_active', 'valid_from', 'valid_to', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
