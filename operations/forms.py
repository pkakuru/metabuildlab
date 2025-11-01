from django import forms
from django.core.exceptions import ValidationError
from .models import Client, Sample, SampleTest
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
