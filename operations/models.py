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
        if not self.client_reference:
            self.client_reference = self.generate_client_reference()
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

    def generate_client_reference(self):
        """Generate a client reference identifier"""
        from django.utils import timezone
        year = timezone.now().year
        month = timezone.now().month

        last_reference = Sample.objects.filter(
            client_reference__startswith=f"CR{year:04d}{month:02d}"
        ).order_by('-client_reference').first()

        if last_reference:
            try:
                last_number = int(last_reference.client_reference[-4:])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1

        return f"CR{year:04d}{month:02d}{next_number:04d}"


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


class Job(models.Model):
    """Job assignment linking samples to technicians for testing"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Job identification
    job_id = models.CharField(max_length=50, unique=True, help_text="Unique job identifier")
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='jobs')
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='assigned_jobs', 
                                     limit_choices_to={'role': 'technician'},
                                     help_text="Technician assigned to this job")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_jobs',
                                   help_text="User who created this job")
    
    # Job details
    assigned_tests = models.ManyToManyField(SampleTest, related_name='jobs', 
                                           help_text="Specific tests assigned in this job")
    priority = models.CharField(max_length=20, choices=Sample.PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Dates
    assigned_date = models.DateTimeField(null=True, blank=True, help_text="When job was assigned to technician")
    due_date = models.DateField(null=True, blank=True, help_text="Expected completion date")
    started_date = models.DateTimeField(null=True, blank=True, help_text="When technician started work")
    completed_date = models.DateTimeField(null=True, blank=True, help_text="When job was completed")
    
    # Instructions and notes
    instructions = models.TextField(blank=True, help_text="Special instructions for the technician")
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Job"
        verbose_name_plural = "Jobs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['job_id']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.job_id} - {self.sample.sample_id}"
    
    def save(self, *args, **kwargs):
        if not self.job_id:
            self.job_id = self.generate_job_id()
        super().save(*args, **kwargs)
    
    def generate_job_id(self):
        """Generate unique job ID"""
        from django.utils import timezone
        year = timezone.now().year
        month = timezone.now().month
        
        last_job = Job.objects.filter(
            job_id__startswith=f"JOB{year:04d}{month:02d}"
        ).order_by('-job_id').first()
        
        if last_job:
            try:
                last_number = int(last_job.job_id[-4:])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        return f"JOB{year:04d}{month:02d}{next_number:04d}"
    
    @property
    def total_tests(self):
        """Return total number of tests assigned"""
        return self.assigned_tests.count()
    
    def assign_to_technician(self, technician, due_date=None):
        """Assign job to a technician"""
        from django.utils import timezone
        self.assigned_to = technician
        self.assigned_date = timezone.now()
        self.status = 'assigned'
        if due_date:
            self.due_date = due_date
        self.save()
    
    def start_work(self, user):
        """Start working on the job - called by technician"""
        from django.utils import timezone
        from .models import SampleStatusHistory
        
        if self.status in ['assigned', 'pending']:
            self.status = 'in_progress'
            self.started_date = timezone.now()
            self.save()
            
            # Update sample status if needed
            if self.sample.status in ['received', 'assigned']:
                old_status = self.sample.status
                self.sample.status = 'in_progress'
                self.sample.save()
                
                # Create status history entry
                SampleStatusHistory.objects.create(
                    sample=self.sample,
                    old_status=old_status,
                    new_status='in_progress',
                    changed_by=user,
                    notes=f'Work started on job {self.job_id}'
                )
            return True
        return False
    
    def complete_job(self, user):
        """Mark job as completed - called by technician"""
        from django.utils import timezone
        from .models import SampleStatusHistory
        
        if self.status == 'in_progress':
            self.status = 'completed'
            self.completed_date = timezone.now()
            self.save()
            
            # Check if all jobs for this sample are completed
            all_jobs_completed = not Job.objects.filter(
                sample=self.sample,
                status__in=['assigned', 'in_progress', 'pending']
            ).exclude(id=self.id).exists()
            
            # Update sample status if all jobs are done
            if all_jobs_completed and self.sample.status == 'in_progress':
                old_status = self.sample.status
                self.sample.status = 'testing'
                self.sample.save()
                
                # Create status history entry
                SampleStatusHistory.objects.create(
                    sample=self.sample,
                    old_status=old_status,
                    new_status='testing',
                    changed_by=user,
                    notes=f'All jobs completed. Job {self.job_id} finished.'
                )
            return True
        return False
    
    def put_on_hold(self, user, notes=''):
        """Put job on hold"""
        from django.utils import timezone
        
        if self.status in ['assigned', 'in_progress']:
            old_status = self.status
            self.status = 'on_hold'
            if notes:
                self.notes += f"\n[On Hold - {timezone.now().strftime('%Y-%m-%d %H:%M')}] {notes}"
            self.save()
            return True
        return False
    
    def resume_work(self, user):
        """Resume work on a job that was on hold"""
        from django.utils import timezone
        
        if self.status == 'on_hold':
            self.status = 'in_progress'
            if not self.started_date:
                self.started_date = timezone.now()
            self.save()
            return True
        return False


class SampleReceiptForm(models.Model):
    """Sample Receipt Form (SRF) - Formal acknowledgment of sample receipt"""
    
    # Receipt identification
    receipt_number = models.CharField(max_length=50, unique=True, help_text="Auto-generated receipt number (e.g., SRF-2025-0012)")
    
    # Related sample(s) - SRF can cover one or multiple samples
    samples = models.ManyToManyField(Sample, related_name='receipt_forms', help_text="Samples included in this receipt")
    
    # Receipt date and time
    receipt_date = models.DateTimeField(default=timezone.now, help_text="Date and time samples were received")
    
    # Lab information
    received_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_receipts',
                                    help_text="Lab staff member who received the samples")
    received_by_signature = models.TextField(blank=True, help_text="Signature of lab representative")
    received_by_name = models.CharField(max_length=200, blank=True, help_text="Name of lab representative")
    
    # Client information
    delivered_by = models.CharField(max_length=200, blank=True, help_text="Client representative who delivered samples")
    delivered_by_signature = models.TextField(blank=True, help_text="Signature of client representative")
    delivered_by_name = models.CharField(max_length=200, blank=True, help_text="Name of client representative")
    
    # Project/Site reference (optional)
    project_reference = models.CharField(max_length=200, blank=True, help_text="Project or site reference")
    
    # Condition notes
    condition_notes = models.TextField(blank=True, help_text="Notes about sample condition upon receipt")
    
    # Additional information
    special_instructions = models.TextField(blank=True, help_text="Any special instructions or notes")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_signed = models.BooleanField(default=False, help_text="Whether both parties have signed")
    pdf_generated = models.BooleanField(default=False, help_text="Whether PDF has been generated")
    
    class Meta:
        verbose_name = "Sample Receipt Form"
        verbose_name_plural = "Sample Receipt Forms"
        ordering = ['-receipt_date']
        indexes = [
            models.Index(fields=['receipt_number']),
            models.Index(fields=['receipt_date']),
            models.Index(fields=['received_by']),
        ]
    
    def __str__(self):
        return f"{self.receipt_number} - {self.receipt_date.date()}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self.generate_receipt_number()
        super().save(*args, **kwargs)
    
    def generate_receipt_number(self):
        """Generate unique receipt number in format SRF-YYYY-NNNN"""
        from django.utils import timezone
        year = timezone.now().year
        
        last_receipt = SampleReceiptForm.objects.filter(
            receipt_number__startswith=f"SRF-{year}-"
        ).order_by('-receipt_number').first()
        
        if last_receipt:
            try:
                last_number = int(last_receipt.receipt_number.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        return f"SRF-{year}-{next_number:04d}"
    
    @property
    def sample_count(self):
        """Return number of samples in this receipt"""
        return self.samples.count()
    
    @property
    def total_tests(self):
        """Return total number of tests requested across all samples"""
        total = 0
        for sample in self.samples.all():
            total += sample.total_tests
        return total
