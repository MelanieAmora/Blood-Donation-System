from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import timedelta, date, datetime

BLOOD_TYPES = [
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
]

COMPONENT_CHOICES = [
    ('WB', 'Whole Blood'),
    ('PLS', 'Plasma'),
    ('PLT', 'Platelets'),
    ('RBC', 'Red Blood Cells'),
]

GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

TIME_SLOT_DURATION = 30  # minutes

class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='O')
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    barangay = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    health_info = models.TextField(blank=True)

    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    medications = models.TextField(blank=True)

    last_hemoglobin_level = models.FloatField(null=True, blank=True)  # g/dL
    last_screening_date = models.DateField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)  # kg
    eligibility_status = models.CharField(max_length=50, blank=True)

    is_deferred = models.BooleanField(default=False)
    deferral_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.blood_type})"

from django.core.exceptions import ValidationError

class DonationDrive(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateField(help_text="Start date of the donation drive", null=True)
    end_date = models.DateField(help_text="End date of the donation drive", null=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=300)
    venue_details = models.TextField(blank=True, help_text="Specific details about the venue, parking, etc.")
    
    # Capacity Management
    max_donors = models.PositiveIntegerField(default=10)
    max_donors_per_slot = models.PositiveIntegerField(default=2, help_text="Maximum donors that can be processed simultaneously")
    blood_type_targets = models.JSONField(default=dict, blank=True, null=True, help_text="Target number of donors for each blood type")
    
    # Requirements and Instructions
    eligibility_requirements = models.TextField(help_text="Basic eligibility criteria for donors", default="")
    pre_donation_instructions = models.TextField(help_text="Instructions for donors to follow before donation", default="")
    required_documents = models.TextField(help_text="List of required documents donors should bring", default="")
    
    # Health and Safety
    medical_staff_count = models.PositiveIntegerField(default=2, help_text="Number of medical staff available")
    equipment_available = models.TextField(help_text="Available medical equipment and supplies", default="")
    safety_protocols = models.TextField(help_text="COVID-19 and other safety protocols", default="")
    
    # Contact Information
    contact_person = models.CharField(max_length=100, default="")
    contact_number = models.CharField(max_length=20, default="")
    emergency_number = models.CharField(max_length=20, default="")
    
    # Status
    is_active = models.BooleanField(default=True)
    cancellation_reason = models.TextField(blank=True)
    weather_dependent = models.BooleanField(default=True, help_text="Whether the drive may be affected by weather")

    def clean(self):
        if self.max_donors <= 0:
            raise ValidationError('Maximum donors must be greater than zero.')
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time.')
        if self.start_date > self.end_date:
            raise ValidationError('End date must be after or equal to start date.')
        if self.max_donors_per_slot > self.max_donors:
            raise ValidationError('Donors per slot cannot exceed maximum donors.')

    def get_available_slots(self):
        """Calculate available time slots based on duration and capacity"""
        slots = []
        current_time = self.start_time
        while current_time < self.end_time:
            next_time = (datetime.combine(date.min, current_time) + 
                        timedelta(minutes=TIME_SLOT_DURATION)).time()
            if next_time <= self.end_time:
                slots.append({
                    'start': current_time,
                    'end': next_time,
                    'capacity': self.max_donors_per_slot
                })
            current_time = next_time
        return slots

    def get_blood_type_availability(self):
        """Get current registration count by blood type"""
        registrations = self.driveregistration_set.all()
        blood_type_counts = {}
        for blood_type, _ in BLOOD_TYPES:
            count = registrations.filter(donor__blood_type=blood_type).count()
            target = self.blood_type_targets.get(blood_type, 0)
            blood_type_counts[blood_type] = {
                'current': count,
                'target': target,
                'available': max(0, target - count) if target > 0 else None
            }
        return blood_type_counts

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"

class DriveRegistration(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    drive = models.ForeignKey(DonationDrive, on_delete=models.CASCADE)
    registration_time = models.DateTimeField(default=timezone.now)
    scheduled_time = models.TimeField(null=True, blank=True)
    
    # Pre-donation
    confirmed_attendance = models.BooleanField(default=False)
    pre_screening_complete = models.BooleanField(default=False)
    pre_screening_notes = models.TextField(blank=True)
    
    # Attendance
    is_present = models.BooleanField(default=False)
    arrival_time = models.TimeField(null=True, blank=True)
    
    # Donation
    donation_started = models.TimeField(null=True, blank=True)
    donation_completed = models.TimeField(null=True, blank=True)
    donation_successful = models.BooleanField(default=False)
    units_collected = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    
    # Health Metrics
    blood_pressure = models.CharField(max_length=20, blank=True, default="")
    hemoglobin_level = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    pulse_rate = models.PositiveIntegerField(null=True, blank=True)
    
    # Post-donation
    post_donation_condition = models.TextField(blank=True, default="")
    recovery_time = models.PositiveIntegerField(null=True, blank=True, help_text="Recovery time in minutes")
    follow_up_required = models.BooleanField(default=False)
    
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ('donor', 'drive')

    def __str__(self):
        return f"{self.donor} registration for {self.drive}"

class BloodInventory(models.Model):
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    component = models.CharField(max_length=3, choices=COMPONENT_CHOICES)
    units = models.PositiveIntegerField(default=0)
    expiry_date =  models.DateField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    critical_level = models.PositiveIntegerField(default=5)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('blood_type', 'component', 'expiry_date')
        ordering = ['expiry_date', 'blood_type', 'component']

    def __str__(self):
        return f"{self.blood_type} - {self.component} ({self.units} units)"

    @property
    def is_critical(self):
        return self.units <= self.critical_level

    def clean(self):
        if self.expiry_date is not None and self.expiry_date < date.today():
            raise ValidationError("Expiry date cannot be in the past")
        
    def save(self, *args, **kwargs):
        
        self.full_clean()
        super().save(*args, **kwargs)
