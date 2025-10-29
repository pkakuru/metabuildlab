from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class TestCategory(models.Model):
    """Main test categories (e.g., Soil - Laboratory tests, Rocks & Aggregates)"""
    code = models.CharField(max_length=50, unique=True, help_text="Category code (e.g., SOLATE-GEN)")
    name = models.CharField(max_length=200, help_text="Category name (e.g., Soil - Laboratory tests)")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Test Category"
        verbose_name_plural = "Test Categories"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class TestSubCategory(models.Model):
    """Subcategories within main categories (e.g., Physical Properties, Engineering Properties)"""
    category = models.ForeignKey(TestCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=200, help_text="Subcategory name (e.g., Physical Properties:)")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Test Subcategory"
        verbose_name_plural = "Test Subcategories"
        ordering = ['category', 'name']
        unique_together = ['category', 'name']

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class TestItem(models.Model):
    """Individual test items with pricing and specifications"""
    CURRENCY_CHOICES = [
        ('UGX', 'Ugandan Shilling'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    ]

    SAMPLE_TYPE_CHOICES = [
        ('Soil', 'Soil'),
        ('Rocks', 'Rocks'),
        ('Concrete', 'Concrete'),
        ('Steel', 'Steel'),
        ('Water', 'Water'),
        ('Other', 'Other'),
    ]

    # Identifiers
    system_code = models.CharField(max_length=50, unique=True, help_text="Unique system code (e.g., SOIL-PHPR-001)")
    display_code = models.CharField(max_length=20, help_text="Display code (e.g., SL-GSD)")
    
    # Categorization
    category = models.ForeignKey(TestCategory, on_delete=models.CASCADE, related_name='test_items')
    subcategory = models.ForeignKey(TestSubCategory, on_delete=models.CASCADE, related_name='test_items')
    
    # Test details
    test_name = models.CharField(max_length=300, help_text="Full test name")
    method_standard = models.CharField(max_length=200, help_text="Testing method or standard")
    
    # Pricing
    unit = models.CharField(max_length=50, help_text="Pricing unit (e.g., per sample, per meter)")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UGX')
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Test price"
    )
    
    # Operational details
    tat_days = models.PositiveIntegerField(help_text="Turnaround time in days")
    sample_type = models.CharField(max_length=50, choices=SAMPLE_TYPE_CHOICES, default='Soil')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True, help_text="Additional requirements or notes")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Test Item"
        verbose_name_plural = "Test Items"
        ordering = ['category', 'subcategory', 'test_name']
        indexes = [
            models.Index(fields=['system_code']),
            models.Index(fields=['display_code']),
            models.Index(fields=['category', 'subcategory']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.display_code} - {self.test_name}"

    @property
    def formatted_price(self):
        """Return formatted price with currency"""
        return f"{self.currency} {self.price:,.2f}"

    @property
    def full_category_path(self):
        """Return full category path"""
        return f"{self.category.name} > {self.subcategory.name}"


class PricingRule(models.Model):
    """Pricing rules and discounts"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    minimum_quantity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pricing Rule"
        verbose_name_plural = "Pricing Rules"
        ordering = ['name']

    def __str__(self):
        return self.name


class DiscountScheme(models.Model):
    """Discount schemes for clients or bulk orders"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    minimum_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valid_from = models.DateField()
    valid_to = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Discount Scheme"
        verbose_name_plural = "Discount Schemes"
        ordering = ['name']

    def __str__(self):
        return self.name
