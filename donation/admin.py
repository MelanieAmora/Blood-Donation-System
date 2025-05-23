from django.contrib import admin
from django.db.models import Count, Sum
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import BloodInventory, Donor, DonationDrive, DriveRegistration

admin.site.site_header = 'Barangay Blood Donation System'
admin.site.site_title = 'Blood Donation Admin'
admin.site.index_title = 'Blood Donation Management'

@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'blood_type', 'contact_info', 'location', 'eligibility_status', 'donation_count')
    list_filter = ('blood_type', 'eligibility_status', 'is_deferred', 'city', 'barangay')
    search_fields = ('first_name', 'last_name', 'email', 'contact_number', 'barangay', 'city')
    fieldsets = (
        ('Personal Information', {
            'fields': (('first_name', 'last_name'), ('birth_date', 'blood_type'), 
                      ('contact_number', 'email'), 'address', ('barangay', 'city'))
        }),
        ('Emergency Contact', {
            'fields': (('emergency_contact_name', 'emergency_contact_relation'), 'emergency_contact_phone')
        }),
        ('Medical Information', {
            'fields': ('health_info', 'allergies', 'chronic_conditions', 'medications',
                      ('last_hemoglobin_level', 'last_screening_date', 'weight'))
        }),
        ('Donation Status', {
            'fields': ('eligibility_status', 'is_deferred', 'deferral_reason')
        })
    )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'
    
    def contact_info(self, obj):
        return format_html('📞 {} <br>✉️ {}', obj.contact_number, obj.email)
    contact_info.short_description = 'Contact Info'
    
    def location(self, obj):
        return f"{obj.barangay}, {obj.city}"
    location.short_description = 'Location'
    
    def donation_count(self, obj):
        count = DriveRegistration.objects.filter(donor=obj, donation_successful=True).count()
        return format_html('<span style="color: green;">{} donations</span>', count)
    donation_count.short_description = 'Total Donations'

@admin.register(DonationDrive)
class DonationDriveAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_date', 'location', 'registered_donors', 'successful_donations', 'capacity_status')
    list_filter = ('start_date', 'location')
    search_fields = ('name', 'location')
    ordering = ('-start_date', 'start_time')
    
    def event_date(self, obj):
        return format_html('{} to {}<br>{} - {}', 
                         obj.start_date.strftime('%B %d, %Y'),
                         obj.end_date.strftime('%B %d, %Y'),
                         obj.start_time.strftime('%I:%M %p'),
                         obj.end_time.strftime('%I:%M %p'))
    event_date.short_description = 'Event Date & Time'
    
    def registered_donors(self, obj):
        count = DriveRegistration.objects.filter(drive=obj).count()
        return f"{count}/{obj.max_donors}"
    registered_donors.short_description = 'Registration'
    
    def successful_donations(self, obj):
        count = DriveRegistration.objects.filter(drive=obj, donation_successful=True).count()
        return format_html('<span style="color: green;">{}</span>', count)
    successful_donations.short_description = 'Successful Donations'
    
    def capacity_status(self, obj):
        registered = DriveRegistration.objects.filter(drive=obj).count()
        if registered >= obj.max_donors:
            return format_html('<span style="color: red;">Full</span>')
        elif registered >= obj.max_donors * 0.8:
            return format_html('<span style="color: orange;">Almost Full</span>')
        return format_html('<span style="color: green;">Open</span>')
    capacity_status.short_description = 'Status'

@admin.register(DriveRegistration)
class DriveRegistrationAdmin(admin.ModelAdmin):
    list_display = ('donor_name', 'drive_info', 'attendance_status', 'donation_status')
    list_filter = ('is_present', 'donation_successful', 'drive__start_date')
    search_fields = ('donor__first_name', 'donor__last_name', 'drive__name')
    raw_id_fields = ('donor', 'drive')
    
    def donor_name(self, obj):
        return f"{obj.donor.first_name} {obj.donor.last_name} ({obj.donor.blood_type})"
    donor_name.short_description = 'Donor'
    
    def drive_info(self, obj):
        return format_html('{}<br>{} to {}', 
                         obj.drive.name, 
                         obj.drive.start_date.strftime('%B %d, %Y'),
                         obj.drive.end_date.strftime('%B %d, %Y'))
    drive_info.short_description = 'Drive Information'
    
    def attendance_status(self, obj):
        return format_html('<span style="color: {};">●</span> {}',
                         'green' if obj.is_present else 'red',
                         'Present' if obj.is_present else 'Absent')
    attendance_status.short_description = 'Attendance'
    
    def donation_status(self, obj):
        if not obj.is_present:
            return '-'
        return format_html('<span style="color: {};">●</span> {}',
                         'green' if obj.donation_successful else 'red',
                         'Successful' if obj.donation_successful else 'Unsuccessful')
    donation_status.short_description = 'Donation Status'

@admin.register(BloodInventory)
class BloodInventoryAdmin(admin.ModelAdmin):
    list_display = ('blood_type', 'component', 'inventory_status', 'expiry_info', 'last_update_info')
    list_filter = ('blood_type', 'component', 'expiry_date')
    search_fields = ('blood_type', 'component')
    readonly_fields = ('last_updated',)
    ordering = ('expiry_date',)
    
    def inventory_status(self, obj):
        color = 'red' if obj.is_critical else 'green'
        return format_html('<span style="color: {};">{} units</span>', color, obj.units)
    inventory_status.short_description = 'Current Stock'
    
    def expiry_info(self, obj):
        if not obj.expiry_date:
            return '-'
        days_left = (obj.expiry_date - timezone.now().date()).days
        color = 'red' if days_left <= 7 else 'orange' if days_left <= 30 else 'green'
        return format_html('<span style="color: {};">{}<br>{} days left</span>',
                         color,
                         obj.expiry_date.strftime('%B %d, %Y'),
                         days_left)
    expiry_info.short_description = 'Expiry Status'
    
    def last_update_info(self, obj):
        return format_html('{}',
                         obj.last_updated.strftime('%B %d, %Y %I:%M %p'))
    last_update_info.short_description = 'Last Updated'

    actions = ['mark_as_critical', 'reset_critical_level']
    
    def mark_as_critical(self, request, queryset):
        queryset.update(critical_level=5)
    mark_as_critical.short_description = "Mark selected items as critical (5 units)"
    
    def reset_critical_level(self, request, queryset):
        queryset.update(critical_level=10)
    reset_critical_level.short_description = "Reset critical level to default (10 units)"
