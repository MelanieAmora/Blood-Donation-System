# Blood Donation System Documentation

## Table of Contents
1. [Overview](#overview)
2. [Models](#models)
3. [Views](#views)
4. [Features](#features)

## Overview

The Blood Donation System is a web-based application designed to manage blood donation drives, donor information, and blood inventory. It provides separate interfaces for donors and administrators, facilitating efficient management of the blood donation process.

## Models

### 1. Donor Model
Represents individual blood donors in the system.

#### Implementation:
```python
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
    last_hemoglobin_level = models.FloatField(null=True, blank=True)
    last_screening_date = models.DateField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    eligibility_status = models.CharField(max_length=50, blank=True)

    is_deferred = models.BooleanField(default=False)
    deferral_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.blood_type})"
```

#### Fields:
- **User Information**
  - `user`: OneToOneField - Link to Django User model
  - `first_name`: CharField(100) - Donor's first name
  - `last_name`: CharField(100) - Donor's last name
  - `birth_date`: DateField - Date of birth
  - `gender`: CharField(1) - Gender (M/F/O)
  - `blood_type`: CharField(3) - Blood type (A+, A-, B+, B-, AB+, AB-, O+, O-)

- **Contact Information**
  - `contact_number`: CharField(20) - Phone number
  - `email`: EmailField - Email address
  - `address`: TextField - Full address
  - `barangay`: CharField(100) - Barangay name
  - `city`: CharField(100) - City name

- **Emergency Contact**
  - `emergency_contact_name`: CharField(100)
  - `emergency_contact_relation`: CharField(50)
  - `emergency_contact_phone`: CharField(20)

- **Health Information**
  - `health_info`: TextField - General health information
  - `allergies`: TextField - Known allergies
  - `chronic_conditions`: TextField - Chronic medical conditions
  - `medications`: TextField - Current medications
  - `last_hemoglobin_level`: FloatField - Latest hemoglobin reading (g/dL)
  - `last_screening_date`: DateField - Date of last health screening
  - `weight`: FloatField - Weight in kg
  - `eligibility_status`: CharField(50) - Current eligibility status

- **Deferral Information**
  - `is_deferred`: BooleanField - Whether donor is currently deferred
  - `deferral_reason`: TextField - Reason for deferral if applicable

### 2. DonationDrive Model
Manages blood donation events and drives.

#### Implementation:
```python
class DonationDrive(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateField(help_text="Start date of the donation drive", null=True)
    end_date = models.DateField(help_text="End date of the donation drive", null=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=300)
    venue_details = models.TextField(blank=True, help_text="Specific details about the venue, parking, etc.")
    
    max_donors = models.PositiveIntegerField(default=10)
    max_donors_per_slot = models.PositiveIntegerField(default=2, help_text="Maximum donors that can be processed simultaneously")
    blood_type_targets = models.JSONField(default=dict, blank=True, null=True, help_text="Target number of donors for each blood type")
    
    eligibility_requirements = models.TextField(help_text="Basic eligibility criteria for donors", default="")
    pre_donation_instructions = models.TextField(help_text="Instructions for donors to follow before donation", default="")
    required_documents = models.TextField(help_text="List of required documents donors should bring", default="")
    
    medical_staff_count = models.PositiveIntegerField(default=2, help_text="Number of medical staff available")
    equipment_available = models.TextField(help_text="Available medical equipment and supplies", default="")
    safety_protocols = models.TextField(help_text="COVID-19 and other safety protocols", default="")
    
    contact_person = models.CharField(max_length=100, default="")
    contact_number = models.CharField(max_length=20, default="")
    emergency_number = models.CharField(max_length=20, default="")
    
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
```

#### Fields:
- **Basic Information**
  - `name`: CharField(200) - Name of the drive
  - `start_date`: DateField - Start date
  - `end_date`: DateField - End date
  - `start_time`: TimeField - Daily start time
  - `end_time`: TimeField - Daily end time
  - `location`: CharField(300) - Location of the drive
  - `venue_details`: TextField - Additional venue information

- **Capacity Management**
  - `max_donors`: PositiveIntegerField - Maximum number of donors
  - `max_donors_per_slot`: PositiveIntegerField - Donors per time slot
  - `blood_type_targets`: JSONField - Target numbers by blood type

- **Requirements**
  - `eligibility_requirements`: TextField - Eligibility criteria
  - `pre_donation_instructions`: TextField - Pre-donation guidelines
  - `required_documents`: TextField - Required documentation

- **Health and Safety**
  - `medical_staff_count`: PositiveIntegerField - Number of medical staff
  - `equipment_available`: TextField - Available equipment
  - `safety_protocols`: TextField - Safety measures

- **Contact Information**
  - `contact_person`: CharField(100)
  - `contact_number`: CharField(20)
  - `emergency_number`: CharField(20)

#### Methods:
- `get_available_slots()`: Calculates available time slots based on duration and capacity
- `get_blood_type_availability()`: Returns current registration count by blood type
- `clean()`: Validates drive data

### 3. DriveRegistration Model
Tracks donor registrations for specific donation drives.

#### Implementation:
```python
class DriveRegistration(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    drive = models.ForeignKey(DonationDrive, on_delete=models.CASCADE)
    registration_time = models.DateTimeField(default=timezone.now)
    scheduled_time = models.TimeField(null=True, blank=True)
    
    confirmed_attendance = models.BooleanField(default=False)
    pre_screening_complete = models.BooleanField(default=False)
    pre_screening_notes = models.TextField(blank=True)
    
    is_present = models.BooleanField(default=False)
    arrival_time = models.TimeField(null=True, blank=True)
    
    donation_started = models.TimeField(null=True, blank=True)
    donation_completed = models.TimeField(null=True, blank=True)
    donation_successful = models.BooleanField(default=False)
    units_collected = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    
    blood_pressure = models.CharField(max_length=20, blank=True, default="")
    hemoglobin_level = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    pulse_rate = models.PositiveIntegerField(null=True, blank=True)
    
    post_donation_condition = models.TextField(blank=True, default="")
    recovery_time = models.PositiveIntegerField(null=True, blank=True, help_text="Recovery time in minutes")
    follow_up_required = models.BooleanField(default=False)
    
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ('donor', 'drive')

    def __str__(self):
        return f"{self.donor} registration for {self.drive}"
```

#### Fields:
- **Registration Details**
  - `donor`: ForeignKey(Donor)
  - `drive`: ForeignKey(DonationDrive)
  - `registration_time`: DateTimeField
  - `scheduled_time`: TimeField

- **Pre-donation**
  - `confirmed_attendance`: BooleanField
  - `pre_screening_complete`: BooleanField
  - `pre_screening_notes`: TextField

- **Donation Process**
  - `is_present`: BooleanField
  - `arrival_time`: TimeField
  - `donation_started`: TimeField
  - `donation_completed`: TimeField
  - `donation_successful`: BooleanField
  - `units_collected`: DecimalField(4,2)

- **Health Metrics**
  - `blood_pressure`: CharField(20)
  - `hemoglobin_level`: DecimalField(4,2)
  - `pulse_rate`: PositiveIntegerField

### 4. BloodInventory Model
Manages blood inventory levels and tracking.

#### Implementation:
```python
class BloodInventory(models.Model):
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    component = models.CharField(max_length=3, choices=COMPONENT_CHOICES)
    units = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(null=True, blank=True)
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
```

#### Fields:
- `blood_type`: CharField(3) - Blood type
- `component`: CharField(3) - Blood component type (WB, PLS, PLT, RBC)
- `units`: PositiveIntegerField - Number of units
- `expiry_date`: DateField - Expiration date
- `last_updated`: DateTimeField - Last update timestamp
- `critical_level`: PositiveIntegerField - Critical threshold
- `created_by`: ForeignKey(User)
- `updated_at`: DateTimeField

## Views

### Authentication Views

#### 1. Login View (`login_view`)
- **URL**: `/login/`
- **Purpose**: Handles user authentication
- **Features**:
  - Processes login form
  - Authenticates users
  - Redirects to appropriate dashboard

#### 2. Registration View (`register_donor`)
- **URL**: `/register/`
- **Purpose**: New donor registration
- **Features**:
  - Creates user account
  - Creates donor profile
  - Validates registration data

### Donor Views

#### 1. Donor Dashboard (`donor_dashboard`)
- **URL**: `/donor/dashboard/`
- **Purpose**: Main donor interface
- **Features**:
  - Donation history
  - Upcoming appointments
  - Eligibility status
  - Health metrics
  - Nearby donation drives
  - Profile completion status

#### 2. Profile Management
- **Update Profile** (`update_profile`)
  - Updates personal information
  - Manages contact details
  - Updates address information

- **Health Information** (`update_health_info`)
  - Updates medical history
  - Manages current health status
  - Updates emergency contacts

### Administrative Views

#### 1. Admin Dashboard (`admin_dashboard`)
- **URL**: `/admin/dashboard/`
- **Purpose**: Administrative overview
- **Features**:
  - Blood inventory summary
  - Donation drive statistics
  - Donor registration stats
  - Success rate metrics
  - Recent activities
  - Upcoming events

#### 2. Donor Management (`manage_donors`)
- **URL**: `/admin/donors/`
- **Features**:
  - List all donors
  - Filter and search
  - View donor details
  - Update donor information
  - Track donation history

#### 3. Donation Drive Management
- **Drive List** (`drive_list`)
  - View all drives
  - Track registrations
  - Monitor capacity

- **Create Drive** (`create_drive`)
  - Set up new drives
  - Configure requirements
  - Set capacity limits

#### 4. Inventory Management (`inventory_detail`)
- **URL**: `/admin/inventory/<pk>/`
- **Features**:
  - Track blood units
  - Monitor expiry dates
  - Manage critical levels
  - Update inventory

## Features

### 1. Donor Features
- Profile management
- Donation history tracking
- Appointment scheduling
- Health status monitoring
- Eligibility tracking

### 2. Administrative Features
- Comprehensive dashboard
- Donor management
- Drive organization
- Inventory tracking
- Statistical reporting

### 3. Security Features
- User authentication
- Role-based access control
- Data validation
- Secure profile management

### 4. Reporting Features
- Blood inventory reports
- Donation statistics
- Success rate tracking
- Donor participation metrics 