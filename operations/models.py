from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from core.models import User
from pricing.models import TestItem


class Client(models.Model):
    """Client information for sample intake"""
    name = models.CharField(max_length=200, help_text="Client or company name")
    contact_person = models.CharField(max_length=200, blank=True, help_text="Primary contact person")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    company_registration = models.CharField(max_length=100, blank=True, help_text="Company registration number")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.contact_person})" if self.contact_person else self.name


class Sample(models.Model):
    """Individual sample received for testing"""
    
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('in_progress', 'In Progress'),
        ('testing', 'Testing'),
        ('completed', 'Completed'),
        ('reported', 'Reported'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('rush', 'Rush'),
    ]
    
    SAMPLE_CONDITION_CHOICES = [
        ('good', 'Good'),
        ('damaged', 'Damaged'),
        ('insufficient', 'Insufficient'),
        ('contaminated', 'Contaminated'),
    ]

    # Sample identification
    sample_id = models.CharField(max_length=50, unique=True, help_text="Unique sample identifier")
    client_reference = models.CharField(max_length=100, blank=True, help_text="Client's reference number")
    
    # Client information
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='samples')
    
    # Sample details
    sample_type = models.CharField(max_length=100, help_text="Type of sample (e.g., Soil, Concrete, Steel)")
    sample_description = models.TextField(help_text="Detailed description of the sample")
    sample_condition = models.CharField(max_length=20, choices=SAMPLE_CONDITION_CHOICES, default='good')
    quantity = models.CharField(max_length=100, help_text="Quantity or amount of sample")
    location_collected = models.CharField(max_length=200, blank=True, help_text="Location where sample was collected")
    collection_date = models.DateField(blank=True, null=True, help_text="Date sample was collected")
    
    # Intake information
    received_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_samples')
    received_date = models.DateTimeField(default=timezone.now)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    
    # Testing requirements
    requested_tests = models.ManyToManyField(TestItem, through='SampleTest', related_name='samples')
    special_instructions = models.TextField(blank=True, help_text="Special instructions for testing")
    
    # Delivery information
    delivery_method = models.CharField(max_length=100, blank=True, help_text="How sample was delivered")
    courier_details = models.CharField(max_length=200, blank=True, help_text="Courier or delivery details")
    
    # Metadata
    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sample"
        verbose_name_plural = "Samples"
        ordering = ['-received_date']
        indexes = [
            models.Index(fields=['sample_id']),
            models.Index(fields=['status']),
            models.Index(fields=['received_date']),
            models.Index(fields=['client']),
        ]

    def __str__(self):
        return f"{self.sample_id} - {self.client.name}"

    @property
    def total_tests(self):
        """Return total number of tests requested"""
        return self.requested_tests.count()

    @property
    def estimated_completion_date(self):
        """Calculate estimated completion date based on test turnaround times"""
        if not self.requested_tests.exists():
            return None
        
        max_tat = max(test.tat_days for test in self.requested_tests.all())
        return self.received_date.date() + timezone.timedelta(days=max_tat)

    def save(self, *args, **kwargs):
        if not self.sample_id:
            # Generate sample ID if not provided
            self.sample_id = self.generate_sample_id()
        super().save(*args, **kwargs)

    def generate_sample_id(self):
        """Generate unique sample ID"""
        from django.utils import timezone
        year = timezone.now().year
        month = timezone.now().month
        
        # Get the last sample for this year/month
        last_sample = Sample.objects.filter(
            sample_id__startswith=f"MBL{year:04d}{month:02d}"
        ).order_by('-sample_id').first()
        
        if last_sample:
            try:
                last_number = int(last_sample.sample_id[-4:])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        return f"MBL{year:04d}{month:02d}{next_number:04d}"


class SampleTest(models.Model):
    """Through model for Sample-TestItem relationship with additional fields"""
    
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    test_item = models.ForeignKey(TestItem, on_delete=models.CASCADE)
    
    # Test-specific information
    quantity_requested = models.PositiveIntegerField(default=1, help_text="Number of tests requested")
    special_requirements = models.TextField(blank=True, help_text="Special requirements for this test")
    
    # Status tracking
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(blank=True, null=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='completed_tests')
    
    # Results
    test_results = models.TextField(blank=True, help_text="Test results")
    test_report = models.FileField(upload_to='test_reports/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sample Test"
        verbose_name_plural = "Sample Tests"
        unique_together = ['sample', 'test_item']
        ordering = ['test_item__category', 'test_item__test_name']

    def __str__(self):
        return f"{self.sample.sample_id} - {self.test_item.test_name}"


class SampleAttachment(models.Model):
    """Attachments for samples (photos, documents, etc.)"""
    
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='sample_attachments/')
    description = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sample Attachment"
        verbose_name_plural = "Sample Attachments"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.sample.sample_id} - {self.description or self.file.name}"


class SampleStatusHistory(models.Model):
    """Track status changes for samples"""
    
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Sample Status History"
        verbose_name_plural = "Sample Status Histories"
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.sample.sample_id} - {self.old_status} → {self.new_status}"
