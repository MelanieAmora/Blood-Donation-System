Preparation of Papers for Barangay Blood Donation Drive System
===========================================

Melanie D. Amora
Department of Computer Engineering, Philippines
Email: melanieamora84@gmail.com

ABSTRACT
--------
The Barangay Blood Donation Drive System is a comprehensive web-based platform designed to manage and streamline blood donation activities at the barangay level. This system facilitates the organization of blood donation drives, donor registration, health screening, and inventory management. It provides an efficient interface for both administrators and donors, ensuring smooth operation of blood donation campaigns while maintaining proper health and safety protocols.

1. INTRODUCTION
--------------
The system addresses the critical need for organized blood donation management at the community level. It incorporates features for donor management, drive scheduling, health screening, and inventory tracking. The platform ensures proper documentation of donation activities while maintaining donor privacy and medical information security.

1.1 Key Features
- Donor profile management and health tracking
- Blood donation drive organization and scheduling
- Time slot management and capacity control
- Health screening and eligibility verification
- Blood inventory management
- Emergency contact information handling
- Medical staff coordination
- Safety protocol implementation

2. SYSTEM ARCHITECTURE
---------------------
The system is built using Django framework with the following key components:

2.1 Models
The system implements four main models to manage different aspects of the blood donation system:

### 2.1.1 Donor Model
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

### 2.1.2 DonationDrive Model
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
    max_donors_per_slot = models.PositiveIntegerField(default=2)
    blood_type_targets = models.JSONField(default=dict, blank=True, null=True)
    
    eligibility_requirements = models.TextField(default="")
    pre_donation_instructions = models.TextField(default="")
    required_documents = models.TextField(default="")
    
    medical_staff_count = models.PositiveIntegerField(default=2)
    equipment_available = models.TextField(default="")
    safety_protocols = models.TextField(default="")
    
    contact_person = models.CharField(max_length=100, default="")
    contact_number = models.CharField(max_length=20, default="")
    emergency_number = models.CharField(max_length=20, default="")
    
    is_active = models.BooleanField(default=True)
    cancellation_reason = models.TextField(blank=True)
    weather_dependent = models.BooleanField(default=True)

    def clean(self):
        if self.max_donors <= 0:
            raise ValidationError('Maximum donors must be greater than zero.')
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time.')
        if self.start_date > self.end_date:
            raise ValidationError('End date must be after or equal to start date.')
        if self.max_donors_per_slot > self.max_donors:
            raise ValidationError('Donors per slot cannot exceed maximum donors.')
```

### 2.1.3 DriveRegistration Model
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
    recovery_time = models.PositiveIntegerField(null=True, blank=True)
    follow_up_required = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ('donor', 'drive')
```

### 2.1.4 BloodInventory Model
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

    @property
    def is_critical(self):
        return self.units <= self.critical_level

    def clean(self):
        if self.expiry_date is not None and self.expiry_date < date.today():
            raise ValidationError("Expiry date cannot be in the past")
```

2.2 Forms
- DonorProfileForm: Captures donor personal information
- DonationDriveForm: Manages drive creation and updates
- DriveRegistrationForm: Handles donation scheduling
- DonorHealthInfoForm: Records donor health information

3. IMPLEMENTATION DETAILS
------------------------
3.1 Data Models
The system implements comprehensive data models as shown above in section 2.1. These models handle all aspects of the blood donation system, from donor management to inventory tracking.

3.2 User Interface
- Modern, responsive design
- Intuitive navigation
- Form validation and error handling
- Real-time availability updates
- Mobile-friendly layout

4. SECURITY MEASURES
-------------------
- User authentication and authorization
- Secure storage of medical information
- Data encryption for sensitive fields
- Access control based on user roles
- Session management and timeout

5. CONCLUSION
------------
The Barangay Blood Donation Drive System provides a robust platform for managing blood donation activities at the community level. It streamlines the donation process while ensuring proper health protocols and donor safety.

REFERENCES
----------
1. Django Documentation, "Models and Databases", Django Software Foundation
2. Bootstrap Documentation, "Forms and Validation", Bootstrap Team
3. World Health Organization, "Blood Donor Selection Guidelines"
4. Python Software Foundation, "Python 3.13.3 Documentation"

ACKNOWLEDGMENT
-------------
We would like to thank the barangay officials and medical staff for their support in implementing and testing this system. Special thanks to the development team for their dedication to creating a user-friendly and efficient blood donation management platform.

6. APPLICATION INTERFACE
----------------------

### 6.1 Login Interface
![Login Screen](screenshots/login.png)
The login interface provides secure access to the system with username and password authentication.

### 6.2 Admin Dashboard
![Admin Dashboard](screenshots/admin_dashboard.png)
The administrative dashboard displays key metrics including:
- Blood Inventory (11 total units available)
- Registered Donors (4 donors)
- Upcoming Donation Drives (3 drives)
- Monthly Overview (May 2025)
- Blood Type Distribution
- Recent Donation Drives

### 6.3 Create Donation Drive
![Create Drive](screenshots/create_drive.png)
The Create Drive feature includes enhanced date management:
- **Start Date**: Required field for drive commencement (e.g., 05/24/2025)
- **End Date**: Required field for drive conclusion (e.g., 05/31/2025)
- **Time Management**:
  - Start Time: 09:00 AM
  - End Time: 12:30 PM
- **Location Details**:
  - Venue: Daywan gymnasium
  - Barangay: Surigao
  - City: Surigao

### 6.4 Donor Profile Update
![Donor Profile](screenshots/donor_profile.png)
The enhanced donor profile includes:

1. **Emergency Contact Information**
   - Contact Name
   - Relationship
   - Emergency Phone Number

2. **Current Health Conditions Section**
   - Chronic Conditions field
   - Allows donors to input current health status
   - Important for donor eligibility assessment
   - Helps medical staff prepare appropriately

3. **Implementation Details**
```python
# Enhanced Donor Model Health Fields
class Donor(models.Model):
    # ... existing fields ...
    
    # Enhanced Health Information
    chronic_conditions = models.TextField(
        blank=True,
        help_text="List any chronic health conditions"
    )
    current_health_status = models.TextField(
        blank=True,
        help_text="Describe your current health status"
    )
    last_health_update = models.DateField(
        auto_now=True,
        help_text="Date of last health information update"
    )
```

### 6.5 System Features Summary

1. **Enhanced Date Management**
   - Start and end date selection for drives
   - Date validation to ensure logical sequence
   - Calendar interface for easy date selection

2. **Health Monitoring**
   - Comprehensive health condition tracking
   - Medical history documentation
   - Real-time eligibility updates

3. **User Interface Improvements**
   - Intuitive form layouts
   - Clear error messaging
   - Responsive design for all devices

4. **Data Validation**
   - Date range verification
   - Required field enforcement
   - Health information validation

These enhancements improve the system's ability to:
- Track donation drive schedules effectively
- Monitor donor health status
- Ensure safe blood donation practices
- Maintain accurate medical records