from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Donor, DonationDrive, DriveRegistration, BloodInventory, BLOOD_TYPES, TIME_SLOT_DURATION
import json
from datetime import datetime, date


class DonorProfileForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = [
            'first_name',
            'last_name',
            'birth_date',
            'blood_type',
            'contact_number',
            'email',
            'address',
            'barangay',
            'city',
            'emergency_contact_name',
            'emergency_contact_relation',
            'emergency_contact_phone',
            'chronic_conditions'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'emergency_contact_name': forms.TextInput(attrs={
                'placeholder': 'Full Name'
            }),
            'emergency_contact_relation': forms.TextInput(attrs={
                'placeholder': 'Relationship (e.g., Spouse, Parent)'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'placeholder': '+63 912 345 6789'
            }),
            'chronic_conditions': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'List any current health conditions (e.g., Hypertension, Diabetes)',
                'class': 'form-control'
            })
        }

class DonorRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    blood_type = forms.ChoiceField(choices=BLOOD_TYPES)
    contact_number = forms.CharField(max_length=20)
    email = forms.EmailField()
    address = forms.CharField(widget=forms.Textarea)
    barangay = forms.CharField(max_length=100)
    city = forms.CharField(max_length=100)
    
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name', 
                  'birth_date', 'blood_type', 'contact_number', 'email', 
                  'address', 'barangay', 'city']

class DonationDriveForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    blood_type_targets = forms.JSONField(required=False, widget=forms.Textarea(attrs={
        'rows': 4,
        'placeholder': '{"A+": 5, "B+": 3, "O+": 8}'
    }))
    
    class Meta:
        model = DonationDrive
        fields = [
            'name', 'start_date', 'end_date', 'start_time', 'end_time', 'location', 'venue_details',
            'max_donors', 'max_donors_per_slot', 'blood_type_targets',
            'eligibility_requirements', 'pre_donation_instructions', 'required_documents',
            'medical_staff_count', 'equipment_available', 'safety_protocols',
            'contact_person', 'contact_number', 'emergency_number',
            'is_active', 'weather_dependent'
        ]
        widgets = {
            'venue_details': forms.Textarea(attrs={'rows': 3}),
            'eligibility_requirements': forms.Textarea(attrs={'rows': 4}),
            'pre_donation_instructions': forms.Textarea(attrs={'rows': 4}),
            'required_documents': forms.Textarea(attrs={'rows': 3}),
            'equipment_available': forms.Textarea(attrs={'rows': 3}),
            'safety_protocols': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_blood_type_targets(self):
        blood_type_targets = self.cleaned_data.get('blood_type_targets')
        if not blood_type_targets:
            return {}  # Return empty dict if no targets specified
        return blood_type_targets

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        max_donors = cleaned_data.get('max_donors')
        max_donors_per_slot = cleaned_data.get('max_donors_per_slot')
        medical_staff_count = cleaned_data.get('medical_staff_count')
        blood_type_targets = cleaned_data.get('blood_type_targets', {})

        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("End date must be after or equal to start date")

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time")
            
            # Calculate minimum drive duration based on capacity
            if max_donors and max_donors_per_slot:
                required_slots = -(-max_donors // max_donors_per_slot)  # Ceiling division
                min_duration = required_slots * TIME_SLOT_DURATION
                drive_duration = (datetime.combine(date.min, end_time) - 
                                datetime.combine(date.min, start_time)).seconds / 60
                if drive_duration < min_duration:
                    raise forms.ValidationError(
                        f"Drive duration must be at least {min_duration} minutes to accommodate {max_donors} donors"
                    )

        if max_donors_per_slot and medical_staff_count:
            if max_donors_per_slot > medical_staff_count * 2:
                raise forms.ValidationError(
                    "Too many donors per slot for available medical staff. Maximum 2 donors per staff member."
                )

        if blood_type_targets:
            try:
                targets = blood_type_targets if isinstance(blood_type_targets, dict) else json.loads(blood_type_targets)
                total_target = sum(targets.values())
                if total_target > max_donors:
                    raise forms.ValidationError("Sum of blood type targets exceeds maximum donors")
                for blood_type in targets.keys():
                    if blood_type not in dict(BLOOD_TYPES):
                        raise forms.ValidationError(f"Invalid blood type: {blood_type}")
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format for blood type targets")

        return cleaned_data

class DonorHealthInfoForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = [
            'emergency_contact_name',
            'emergency_contact_relation',
            'emergency_contact_phone',
            'allergies',
            'chronic_conditions',
            'medications',
            'last_hemoglobin_level',
            'last_screening_date',
            'weight',
            'eligibility_status',
            'is_deferred',
            'deferral_reason',
        ]
        widgets = {
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name'
            }),
            'emergency_contact_relation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Relationship (e.g., Spouse, Parent)'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+63 912 345 6789'
            }),
            'allergies': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'List any allergies (e.g., Latex, Iodine)'
            }),
            'chronic_conditions': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'List any chronic conditions (e.g., Hypertension, Diabetes)'
            }),
            'medications': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Current medications'
            }),
            'last_hemoglobin_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'g/dL (e.g., 12.5)'
            }),
            'last_screening_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'Weight in kg (e.g., 70.5)'
            }),
            'eligibility_status': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Eligibility status (e.g., Eligible, Deferred)'
            }),
            'is_deferred': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'deferral_reason': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'If deferred, specify reason'
            }),
        }
        labels = {
            'last_hemoglobin_level': 'Last Hemoglobin Level (g/dL)',
            'last_screening_date': 'Last Screening Date',
            'weight': 'Weight (kg)',
            'eligibility_status': 'Eligibility Status',
            'is_deferred': 'Temporarily Deferred from Donation'
        }

class DriveRegistrationForm(forms.ModelForm):
    class Meta:
        model = DriveRegistration
        fields = [
            'scheduled_time',
            'confirmed_attendance',
            'pre_screening_complete',
            'pre_screening_notes',
            'is_present',
            'arrival_time',
            'donation_started',
            'donation_completed',
            'donation_successful',
            'units_collected',
            'blood_pressure',
            'hemoglobin_level',
            'pulse_rate',
            'post_donation_condition',
            'recovery_time',
            'follow_up_required',
            'notes'
        ]
        widgets = {
            'scheduled_time': forms.TimeInput(attrs={'type': 'time'}),
            'arrival_time': forms.TimeInput(attrs={'type': 'time'}),
            'donation_started': forms.TimeInput(attrs={'type': 'time'}),
            'donation_completed': forms.TimeInput(attrs={'type': 'time'}),
            'pre_screening_notes': forms.Textarea(attrs={'rows': 3}),
            'post_donation_condition': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        arrival_time = cleaned_data.get('arrival_time')
        donation_started = cleaned_data.get('donation_started')
        donation_completed = cleaned_data.get('donation_completed')
        units_collected = cleaned_data.get('units_collected')
        donation_successful = cleaned_data.get('donation_successful')
        
        if donation_successful and not units_collected:
            raise forms.ValidationError("Units collected must be specified for successful donations")
            
        if donation_started and donation_completed:
            if donation_started >= donation_completed:
                raise forms.ValidationError("Donation completion time must be after start time")
                
        if arrival_time and donation_started:
            if donation_started < arrival_time:
                raise forms.ValidationError("Donation cannot start before arrival")
                
        return cleaned_data

# In forms.py
class BloodInventoryForm(forms.ModelForm):
    class Meta:
        model = BloodInventory
        fields = ['blood_type', 'component', 'units', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expiry_date'].required = False
class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
