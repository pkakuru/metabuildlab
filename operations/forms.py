from django import forms
from django.core.exceptions import ValidationError
from .models import Client, Sample, SampleTest, Job, SampleReceiptForm
from pricing.models import TestItem


class ClientForm(forms.ModelForm):
    """Form for creating/editing clients"""
    
    class Meta:
        model = Client
        fields = ['name', 'contact_person', 'email', 'phone', 'address', 'company_registration']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company or client name'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Primary contact person'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+256 XXX XXX XXX'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full address'}),
            'company_registration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company registration number'}),
        }


class SampleIntakeForm(forms.ModelForm):
    """Form for sample intake - accessible to all roles"""
    
    # Client selection - allow creating new client or selecting existing
    client_choice = forms.ChoiceField(
        choices=[('existing', 'Select Existing Client'), ('new', 'Create New Client')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='existing'
    )
    
    existing_client = forms.ModelChoiceField(
        queryset=Client.objects.filter(is_active=True),
        required=False,
        empty_label="Select a client...",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Sample type selection with optional manual entry
    sample_type_choice = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label='Sample Type'
    )
    sample_type_other = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specify sample type'}),
        label='Specify Sample Type'
    )
    
    # Test selection
    requested_tests = forms.ModelMultipleChoiceField(
        queryset=TestItem.objects.filter(is_active=True),
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Select all tests to be performed on this sample"
    )
    
    class Meta:
        model = Sample
        fields = [
            'sample_type', 'sample_description', 'sample_condition',
            'quantity', 'location_collected', 'collection_date', 'priority',
            'special_instructions', 'delivery_method', 'courier_details', 'notes'
        ]
        widgets = {
            'sample_type': forms.HiddenInput(),
            'sample_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed description of the sample'}),
            'sample_condition': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 5kg, 10 pieces, 1 liter'}),
            'location_collected': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location where sample was collected'}),
            'collection_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any special instructions for testing'}),
            'delivery_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Walk-in, Courier, Hand delivery'}),
            'courier_details': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Courier company and tracking number'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Hide underlying sample_type field since we manage via choice/other inputs
        self.fields['sample_type'].required = False

        # Build sample type choices from existing samples
        existing_types = Sample.objects.values_list('sample_type', flat=True).exclude(sample_type="").distinct().order_by('sample_type')
        type_choices = [('', 'Select sample type...')]
        type_choices += [(sample_type, sample_type) for sample_type in existing_types]
        type_choices.append(('__other__', 'Other (specify below)'))
        self.fields['sample_type_choice'].choices = type_choices

        # If editing an instance, pre-populate selection
        current_type = self.instance.sample_type if self.instance and self.instance.sample_type else None
        if current_type and current_type in [choice[0] for choice in type_choices if choice[0] not in ['', '__other__']]:
            self.fields['sample_type_choice'].initial = current_type
        elif current_type:
            self.fields['sample_type_choice'].initial = '__other__'
            self.fields['sample_type_other'].initial = current_type

        # Group tests by category for better organization
        self.fields['requested_tests'].queryset = TestItem.objects.filter(is_active=True).select_related('category', 'subcategory')
        self.fields['existing_client'].label = 'Company/Client Name'
    
    def clean(self):
        cleaned_data = super().clean()
        client_choice = cleaned_data.get('client_choice')
        existing_client = cleaned_data.get('existing_client')
        sample_type_choice = cleaned_data.get('sample_type_choice')
        sample_type_other = cleaned_data.get('sample_type_other')
        
        if client_choice == 'existing' and not existing_client:
            raise ValidationError("Please select an existing client.")

        # Determine final sample type value
        if not sample_type_choice:
            self.add_error('sample_type_choice', "Please select a sample type.")
        elif sample_type_choice == '__other__':
            if not sample_type_other:
                self.add_error('sample_type_other', "Please specify the sample type.")
            else:
                cleaned_data['sample_type'] = sample_type_other.strip()
        else:
            cleaned_data['sample_type'] = sample_type_choice
        
        return cleaned_data


class QuickSampleIntakeForm(forms.ModelForm):
    """Simplified form for quick sample intake"""
    
    client_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Client name'})
    )
    
    contact_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'})
    )
    
    class Meta:
        model = Sample
        fields = ['sample_type', 'sample_description', 'quantity', 'priority']
        widgets = {
            'sample_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sample type'}),
            'sample_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Sample description'}),
            'quantity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Quantity'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }


class SampleTestForm(forms.ModelForm):
    """Form for adding tests to a sample"""
    
    class Meta:
        model = SampleTest
        fields = ['test_item', 'quantity_requested', 'special_requirements']
        widgets = {
            'test_item': forms.Select(attrs={'class': 'form-select'}),
            'quantity_requested': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'special_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Special requirements for this test'}),
        }


class SampleStatusUpdateForm(forms.ModelForm):
    """Form for updating sample status"""
    
    status_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes about this status change'})
    )
    
    class Meta:
        model = Sample
        fields = ['status', 'priority']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }


class JobCreateForm(forms.Form):
    """Form for creating a job from a sample"""
    
    sample = forms.ModelChoiceField(
        queryset=None,
        widget=forms.HiddenInput(),
        required=True
    )
    
    assigned_tests = forms.ModelMultipleChoiceField(
        queryset=None,
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Select tests to assign in this job"
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=None,
        required=True,
        empty_label="Select a technician...",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Technician to assign this job to"
    )
    
    priority = forms.ChoiceField(
        choices=Sample.PRIORITY_CHOICES,
        initial='normal',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text="Expected completion date (optional)"
    )
    
    instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Special instructions for the technician'}),
        help_text="Additional instructions for this job"
    )
    
    def __init__(self, *args, **kwargs):
        sample = kwargs.pop('sample', None)
        super().__init__(*args, **kwargs)
        
        if sample:
            self.fields['sample'].initial = sample
            self.fields['sample'].queryset = Sample.objects.filter(id=sample.id)
            
            # Only show tests that are requested for this sample
            from .models import SampleTest
            sample_tests = SampleTest.objects.filter(sample=sample)
            self.fields['assigned_tests'].queryset = sample_tests
            self.fields['assigned_tests'].initial = sample_tests.values_list('id', flat=True)
            
            # Only show technicians
            from core.models import User
            self.fields['assigned_to'].queryset = User.objects.filter(role='technician', is_active=True).order_by('username')


class SampleReceiptFormForm(forms.ModelForm):
    """Form for creating/editing Sample Receipt Form (SRF)"""
    
    samples = forms.ModelMultipleChoiceField(
        queryset=Sample.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Select samples to include in this receipt"
    )
    
    class Meta:
        model = SampleReceiptForm
        fields = [
            'samples', 'receipt_date', 'project_reference',
            'delivered_by', 'delivered_by_name',
            'received_by_name', 'condition_notes', 'special_instructions'
        ]
        widgets = {
            'receipt_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'project_reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project or site reference (optional)'}),
            'delivered_by': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Client representative name'}),
            'delivered_by_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Client representative full name for signature'}),
            'received_by_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your name as lab representative'}),
            'condition_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes about sample condition upon receipt'}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any special instructions or notes'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        sample_ids = kwargs.pop('sample_ids', None)
        super().__init__(*args, **kwargs)
        
        # Filter samples - show only received samples that don't already have a receipt
        queryset = Sample.objects.filter(status='received')
        if sample_ids:
            queryset = queryset.filter(id__in=sample_ids)
        
        # Exclude samples that already have receipts
        # Get sample IDs that already have receipts
        from .models import SampleReceiptForm
        samples_with_receipts = SampleReceiptForm.objects.values_list('samples__id', flat=True).distinct()
        queryset = queryset.exclude(id__in=samples_with_receipts)
        self.fields['samples'].queryset = queryset
        
        # Pre-fill received_by_name with user's name
        if user and not self.instance.pk:
            self.fields['received_by_name'].initial = user.get_full_name() or user.username
