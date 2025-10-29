from django.contrib import admin
from .models import Client, Sample, SampleTest, SampleAttachment, SampleStatusHistory


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'email', 'phone']
    ordering = ['name']


class SampleTestInline(admin.TabularInline):
    model = SampleTest
    extra = 1
    fields = ['test_item', 'quantity_requested', 'special_requirements', 'is_completed']


class SampleAttachmentInline(admin.TabularInline):
    model = SampleAttachment
    extra = 1
    fields = ['file', 'description', 'uploaded_by']


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ['sample_id', 'client', 'sample_type', 'status', 'priority', 'received_date', 'received_by']
    list_filter = ['status', 'priority', 'sample_type', 'sample_condition', 'received_date', 'client']
    search_fields = ['sample_id', 'client__name', 'client_reference', 'sample_description']
    ordering = ['-received_date']
    inlines = [SampleTestInline, SampleAttachmentInline]
    
    fieldsets = (
        ('Sample Information', {
            'fields': ('sample_id', 'client_reference', 'client')
        }),
        ('Sample Details', {
            'fields': ('sample_type', 'sample_description', 'sample_condition', 'quantity', 'location_collected', 'collection_date')
        }),
        ('Intake Information', {
            'fields': ('received_by', 'received_date', 'priority', 'status')
        }),
        ('Testing Requirements', {
            'fields': ('special_instructions',)
        }),
        ('Delivery Information', {
            'fields': ('delivery_method', 'courier_details')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
    )


@admin.register(SampleTest)
class SampleTestAdmin(admin.ModelAdmin):
    list_display = ['sample', 'test_item', 'quantity_requested', 'is_completed', 'completed_date', 'completed_by']
    list_filter = ['is_completed', 'test_item__category', 'completed_date']
    search_fields = ['sample__sample_id', 'test_item__test_name']
    ordering = ['sample', 'test_item']


@admin.register(SampleAttachment)
class SampleAttachmentAdmin(admin.ModelAdmin):
    list_display = ['sample', 'description', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at', 'uploaded_by']
    search_fields = ['sample__sample_id', 'description']


@admin.register(SampleStatusHistory)
class SampleStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['sample', 'old_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['new_status', 'changed_at', 'changed_by']
    search_fields = ['sample__sample_id', 'notes']
    readonly_fields = ['changed_at']
