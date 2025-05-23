from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import BloodInventory, DonationDrive, DriveRegistration, Donor, BLOOD_TYPES
from .forms import DonationDriveForm, DonorRegistrationForm, DonorProfileForm, DriveRegistrationForm, BloodInventoryForm
from django.contrib.auth.models import User
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db.models import Count, F, Q, Sum
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.http import HttpResponse
import csv
import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def is_staff_user(user):
    return user.is_staff

def home(request):
    # Redirect admin users to admin dashboard
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin-dashboard')
    return render(request, 'donation/home.html')

@login_required
@user_passes_test(is_staff_user)
def inventory_list(request):
    inventory_items = BloodInventory.objects.all().order_by('expiry_date', 'blood_type', 'component')
    context = {
        'inventory_items': inventory_items,
    }
    return render(request, 'donation/inventory_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def inventory_detail(request, pk):
    inventory_item = get_object_or_404(BloodInventory, pk=pk)
    context = {
        'inventory_item': inventory_item,
    }
    return render(request, 'donation/inventory_detail.html', context)

from django.db.models import Count

def drive_list(request):
    today = timezone.now().date()
    drives = DonationDrive.objects.filter(
        start_date__gte=today,
        is_active=True
    ).annotate(
        registered_count=Count('driveregistration'),
        successful_donations=Count('driveregistration', filter=Q(driveregistration__donation_successful=True))
    ).order_by('start_date', 'start_time')

    # Get blood type statistics for each drive
    for drive in drives:
        drive.blood_type_stats = drive.get_blood_type_availability()
        
        # Calculate capacity percentage
        drive.capacity_percentage = (drive.registered_count / drive.max_donors * 100) if drive.max_donors > 0 else 0
        
        # Determine status
        if not drive.is_active:
            drive.status = 'Cancelled'
            drive.status_class = 'danger'
        elif drive.registered_count >= drive.max_donors:
            drive.status = 'Full'
            drive.status_class = 'warning'
        else:
            drive.status = 'Open'
            drive.status_class = 'success'

    context = {
        'drives': drives,
        'blood_types': BLOOD_TYPES,
    }
    return render(request, 'donation/drive_list.html', context)

from django.utils import timezone

def drive_detail(request, pk):
    drive = get_object_or_404(DonationDrive, pk=pk)
    today = timezone.now().date()
    registered_donors = DriveRegistration.objects.filter(drive=drive).select_related('donor')
    is_registered = False
    if request.user.is_authenticated:
        try:
            donor = Donor.objects.get(user=request.user)
            is_registered = DriveRegistration.objects.filter(drive=drive, donor=donor).exists()
        except Donor.DoesNotExist:
            is_registered = False

    registered_count = registered_donors.count()
    remaining_slots = max(drive.max_donors - registered_count, 0)

    # Debug prints for slot issue
    print(f"Drive ID: {drive.id}, max_donors: {drive.max_donors}")
    print(f"Registered donors count: {registered_count}")
    print(f"Remaining slots: {remaining_slots}")
    print(f"Current date: {today}")

    context = {
        'drive': drive,
        'registered_donors': registered_donors,
        'now': today,
        'is_registered': is_registered,
        'remaining_slots': remaining_slots,
        'registered_count': registered_count,
    }
    return render(request, 'donation/drive_detail.html', context)

@login_required
def register_for_drive(request, pk):
    drive = get_object_or_404(DonationDrive, pk=pk)
    
    # Check if drive is still active
    if not drive.is_active:
        messages.error(request, "This drive has been cancelled or is no longer active.")
        return redirect('drive-list')
    
    try:
        donor = Donor.objects.get(user=request.user)
    except Donor.DoesNotExist:
        messages.error(request, "You must complete your donor profile before registering for a drive.")
        return redirect('update-profile')

    # Check if already registered
    if DriveRegistration.objects.filter(drive=drive, donor=donor).exists():
        messages.info(request, "You are already registered for this drive.")
        return redirect('drive-detail', pk=pk)

    # Check slot availability
    registered_count = DriveRegistration.objects.filter(drive=drive).count()
    if registered_count >= drive.max_donors:
        messages.error(request, "Registration is full for this drive.")
        return redirect('drive-detail', pk=pk)

    # Check blood type targets if specified
    if drive.blood_type_targets:
        blood_type_stats = drive.get_blood_type_availability()
        donor_blood_type = donor.blood_type
        if donor_blood_type in blood_type_stats:
            if blood_type_stats[donor_blood_type]['current'] >= blood_type_stats[donor_blood_type]['target']:
                messages.warning(request, f"The target for blood type {donor_blood_type} has been reached. You may still register but priority will be given to needed blood types.")

    # Get available time slots
    available_slots = drive.get_available_slots()
    if not available_slots:
        messages.error(request, "No time slots available for this drive.")
        return redirect('drive-detail', pk=pk)

    if request.method == 'POST':
        selected_time = request.POST.get('time_slot')
        if selected_time:
            try:
                time_obj = datetime.strptime(selected_time, '%H:%M').time()
                registration = DriveRegistration.objects.create(
                    drive=drive,
                    donor=donor,
                    scheduled_time=time_obj
                )
                messages.success(request, f"Successfully registered for {drive.name} at {selected_time}")
                return redirect('drive-detail', pk=pk)
            except ValueError:
                messages.error(request, "Invalid time slot selected.")
        else:
            messages.error(request, "Please select a time slot.")

    context = {
        'drive': drive,
        'available_slots': available_slots,
    }
    return render(request, 'donation/register_for_drive.html', context)

@login_required
@user_passes_test(is_staff_user)
def create_drive(request):
    if request.method == 'POST':
        form = DonationDriveForm(request.POST)
        if form.is_valid():
            drive = form.save()
            messages.success(request, 'Donation drive created successfully')
            return redirect('drive-list')
    else:
        # Pre-fill some fields with default values
        initial_data = {
            'eligibility_requirements': """
- Age between 18-65 years
- Weight at least 50kg
- No major surgery in the past 6 months
- No blood donation in the past 3 months
- No current medications
- Good general health
            """.strip(),
            'pre_donation_instructions': """
1. Get adequate sleep (6-8 hours)
2. Eat a healthy meal before donation
3. Drink plenty of water
4. Bring valid ID and donor card
5. Wear comfortable clothing
            """.strip(),
            'required_documents': """
- Valid government ID
- Donor card (if previously donated)
- Medical certificate (if applicable)
            """.strip(),
            'safety_protocols': """
- Temperature screening at entry
- Mandatory face masks
- Physical distancing measures
- Regular sanitization
- Limited companions allowed
            """.strip(),
            'equipment_available': """
- Blood collection kits
- Blood pressure monitors
- Hemoglobin testing equipment
- First aid supplies
- Recovery beds
            """.strip(),
        }
        form = DonationDriveForm(initial=initial_data)
    
    return render(request, 'donation/create_drive.html', {'form': form})

@login_required
@user_passes_test(is_staff_user)
def drive_registrations(request, pk):
    drive = get_object_or_404(DonationDrive, pk=pk)
    registrations = DriveRegistration.objects.filter(drive=drive).select_related('donor')
    blood_types = BLOOD_TYPES

    if request.method == 'POST':
        registration_id = request.POST.get('registration_id')
        registration = get_object_or_404(DriveRegistration, pk=registration_id)
        form = DriveRegistrationForm(request.POST, instance=registration)
        
        if form.is_valid():
            registration = form.save(commit=False)
            
            # Update inventory if donation was successful
            if registration.donation_successful and registration.units_collected:
                try:
                    inventory, created = BloodInventory.objects.get_or_create(
                        blood_type=registration.donor.blood_type,
                        component='WB',  # Whole Blood
                        defaults={
                            'units': 0,
                            'expiry_date': timezone.now().date() + timedelta(days=42),  # Standard shelf life
                            'created_by': request.user
                        }
                    )
                    inventory.units = F('units') + registration.units_collected
                    inventory.save()
                    
                    messages.success(request, f'Successfully recorded donation of {registration.units_collected} units')
                except Exception as e:
                    messages.error(request, f'Error updating inventory: {str(e)}')
            
            registration.save()
            messages.success(request, 'Registration updated successfully')
            return redirect('drive-registrations', pk=pk)
        else:
            messages.error(request, 'Please correct the errors below')
    else:
        form = DriveRegistrationForm()

    context = {
        'drive': drive,
        'registrations': registrations,
        'form': form,
        'blood_types': blood_types,
    }
    return render(request, 'donation/drive_registrations.html', context)

from .forms import LoginForm

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Logged in successfully.')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'donation/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')

def register_donor(request):
    if request.method == 'POST':
        form = DonorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create Donor profile linked to user
            Donor.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                birth_date=form.cleaned_data['birth_date'],
                blood_type=form.cleaned_data['blood_type'],
                contact_number=form.cleaned_data['contact_number'],
                email=form.cleaned_data['email'],
                address=form.cleaned_data['address'],
                barangay=form.cleaned_data['barangay'],
                city=form.cleaned_data['city'],
            )
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('login')
    else:
        form = DonorRegistrationForm()
    return render(request, 'donation/register_donor.html', {'form': form})

@login_required
def update_profile(request):
    # If user is staff/admin, redirect to admin dashboard
    if request.user.is_staff:
        return redirect('admin-dashboard')
        
    try:
        donor = Donor.objects.get(user=request.user)
    except ObjectDoesNotExist:
        # Automatically create Donor profile if missing for regular users
        donor = Donor.objects.create(
            user=request.user,
            first_name=request.user.first_name,
            last_name=request.user.last_name,
            email=request.user.email,
            # Set default or empty values for other required fields
            birth_date=datetime.date(1900, 1, 1),
            blood_type='A+',  # default blood type
            contact_number='',
            address='',
            barangay='',
            city='',
        )
        messages.info(request, "Donor profile was missing and has been created. Please complete your profile.")

    if request.method == 'POST':
        form = DonorProfileForm(request.POST, instance=donor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('donor-dashboard')
    else:
        form = DonorProfileForm(instance=donor)
    return render(request, 'donation/update_profile.html', {'form': form})

from django.core.exceptions import ObjectDoesNotExist

from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist
from .models import Donor, DriveRegistration
from .forms import DonorHealthInfoForm

@login_required
def donor_dashboard(request):
    # Redirect admin users to admin dashboard
    if request.user.is_staff:
        return redirect('admin-dashboard')
        
    try:
        donor = Donor.objects.get(user=request.user)
        
        # Check critical profile fields
        critical_fields_complete = all([
            donor.first_name,
            donor.last_name,
            donor.birth_date,
            donor.blood_type,
            donor.contact_number,
            donor.email
        ])

        # Check additional profile fields
        address_complete = all([
            donor.address,
            donor.barangay,
            donor.city
        ])

        emergency_complete = all([
            donor.emergency_contact_name,
            donor.emergency_contact_phone
        ])

        if not critical_fields_complete:
            messages.error(request, "Please complete your basic profile information to access the dashboard.")
            return redirect('update-profile')

        if not address_complete:
            messages.warning(request, "Your address information is incomplete. Please update your profile.")
        
        if not emergency_complete:
            messages.warning(request, "Please add emergency contact information to your profile.")

        today = timezone.now().date()
        
        # Get upcoming drives the donor is registered for
        upcoming_registrations = DriveRegistration.objects.filter(
            donor=donor,
            drive__start_date__gte=today
        ).select_related('drive').order_by('drive__start_date')

        # Get past donations with more details
        past_donations = DriveRegistration.objects.filter(
            donor=donor,
            drive__start_date__lt=today,
            donation_successful=True
        ).select_related('drive').order_by('-drive__start_date')

        # Calculate next eligible donation date
        last_successful_donation = past_donations.first()
        next_eligible_date = None
        days_until_eligible = None
        if last_successful_donation:
            next_eligible_date = last_successful_donation.drive.start_date + timedelta(days=56)
            if next_eligible_date > today:
                days_until_eligible = (next_eligible_date - today).days

        # Get blood inventory status for donor's blood type
        blood_inventory = BloodInventory.objects.filter(blood_type=donor.blood_type)
        
        # Calculate donation statistics
        total_donations = past_donations.count()
        recent_donations = past_donations.filter(
            drive__start_date__gte=today - timedelta(days=365)
        ).count()

        # Calculate donation streak
        donation_dates = list(past_donations.values_list('drive__start_date', flat=True))
        current_streak = 0
        if donation_dates:
            last_date = donation_dates[0]
            for date in donation_dates[1:]:
                if (last_date - date).days <= 90:  # Consider donations within 90 days as continuous
                    current_streak += 1
                else:
                    break
                last_date = date

        # Get nearby upcoming drives
        nearby_drives = DonationDrive.objects.filter(
            start_date__gte=today,
            location__icontains=donor.city  # Basic location matching
        ).exclude(
            driveregistration__donor=donor  # Exclude drives donor is already registered for
        ).order_by('start_date')[:5]

        # Calculate impact statistics
        lives_impacted = total_donations * 3  # Each donation can help up to 3 people
        total_volume_donated = total_donations * 450  # Average 450ml per donation

        # Get monthly donation history for the chart
        last_12_months = []
        for i in range(11, -1, -1):
            month_start = today - timedelta(days=today.day - 1) - timedelta(days=30 * i)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            donation_count = past_donations.filter(
                drive__start_date__gte=month_start,
                drive__start_date__lte=month_end
            ).count()
            last_12_months.append({
                'month': month_start.strftime('%b %Y'),
                'count': donation_count
            })

        # Get health metrics
        health_status = {
            'hemoglobin': donor.last_hemoglobin_level,
            'weight': donor.weight,
            'last_screening': donor.last_screening_date,
            'eligibility': donor.eligibility_status if not donor.is_deferred else 'Deferred',
            'deferral_reason': donor.deferral_reason if donor.is_deferred else None
        }

        context = {
            'donor': donor,
            'upcoming_registrations': upcoming_registrations,
            'past_donations': past_donations[:5],  # Show only last 5 donations
            'next_eligible_date': next_eligible_date,
            'days_until_eligible': days_until_eligible,
            'blood_inventory': blood_inventory,
            'total_donations': total_donations,
            'recent_donations': recent_donations,
            'donation_streak': current_streak,
            'nearby_drives': nearby_drives,
            'today': today,
            'lives_impacted': lives_impacted,
            'total_volume_donated': total_volume_donated,
            'monthly_history': last_12_months,
            'health_status': health_status,
            'profile_completion': {
                'basic_info': critical_fields_complete,
                'contact_info': bool(donor.contact_number and donor.email),
                'address_info': address_complete,
                'health_info': bool(donor.health_info),
                'emergency_contact': emergency_complete
            }
        }
        return render(request, 'donation/donor_dashboard.html', context)

    except Donor.DoesNotExist:
        messages.error(request, "Donor profile not found. Please complete your profile.")
        return redirect('update-profile')

@login_required
@user_passes_test(is_staff_user)
# In views.py
def manage_inventory(request):
    if request.method == 'POST':
        form = BloodInventoryForm(request.POST)
        if form.is_valid():
            # Handle null expiry_date case
            inventory = form.save(commit=False)
            if not inventory.expiry_date:
                inventory.expiry_date = date.today() + timedelta(days=42)  # Default RBC expiry
            inventory.save()
            messages.success(request, 'Inventory updated!')
            return redirect('manage-inventory')
    else:
        form = BloodInventoryForm()
    
    inventory = BloodInventory.objects.all().order_by('expiry_date', 'blood_type', 'component')
    print(f"DEBUG: Inventory records count: {inventory.count()}")
    for item in inventory:
        print(f"DEBUG: Inventory item - Blood Type: {item.blood_type}, Component: {item.component}, Units: {item.units}, Expiry: {item.expiry_date}")
    return render(request, 'donation/manage_inventory.html', {'form': form, 'inventory': inventory})

@login_required
@user_passes_test(is_staff_user)
def edit_inventory(request, pk):
    inventory_item = get_object_or_404(BloodInventory, pk=pk)
    if request.method == 'POST':
        form = BloodInventoryForm(request.POST, instance=inventory_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventory item updated successfully.')
            return redirect('manage-inventory')
    else:
        form = BloodInventoryForm(instance=inventory_item)
    return render(request, 'donation/edit_inventory.html', {'form': form, 'inventory_item': inventory_item})

@login_required
@user_passes_test(is_staff_user)
def delete_inventory(request, pk):
    inventory_item = get_object_or_404(BloodInventory, pk=pk)
    if request.method == 'POST':
        inventory_item.delete()
        messages.success(request, 'Inventory item deleted successfully.')
        return redirect('manage-inventory')
    return render(request, 'donation/delete_inventory_confirm.html', {'inventory_item': inventory_item})
@login_required
def emergency_contact_health_info(request):
    try:
        donor = Donor.objects.get(user=request.user)
    except Donor.DoesNotExist:
        if request.user.is_staff:
            messages.info(request, "Admin users do not have donor health information to view.")
            return render(request, 'donation/emergency_contact_health_info.html', {'donor': None, 'admin_user': True})
        else:
            # Automatically create Donor profile if missing
            donor = Donor.objects.create(
                user=request.user,
                first_name=request.user.first_name,
                last_name=request.user.last_name,
                email=request.user.email,
                # Set default or empty values for other required fields
                birth_date=None,
                blood_type='A+',  # default blood type or choose appropriate default
                contact_number='',
                address='',
                barangay='',
                city='',
                emergency_contact_name='',
                emergency_contact_phone='',
                health_info='',
            )
            messages.info(request, "Donor profile was missing and has been created. Please complete your emergency contact and health information.")

    return render(request, 'donation/emergency_contact_health_info.html', {'donor': donor, 'admin_user': request.user.is_staff})

from django.http import HttpResponse
import io
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def download_medical_card(request):
    try:
        donor = Donor.objects.get(user=request.user)
    except Donor.DoesNotExist:
        messages.error(request, "Donor profile not found. Please complete your profile first.")
        return redirect('update-profile')

    # Create a simple text-based medical card content
    medical_card_content = f"""
Medical Card for {donor.first_name} {donor.last_name}

Blood Type: {donor.blood_type}
Allergies: {donor.allergies or 'None'}
Chronic Conditions: {donor.chronic_conditions or 'None'}
Medications: {donor.medications or 'None'}
Last Hemoglobin Level: {donor.last_hemoglobin_level if donor.last_hemoglobin_level is not None else 'N/A'}
Deferred: {"Yes" if donor.is_deferred else "No"}
Deferral Reason: {donor.deferral_reason or 'N/A'}
"""

    # Create HTTP response with text file attachment
    response = HttpResponse(medical_card_content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="medical_card.txt"'
    return response
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.middleware.csrf import get_token

@login_required
@require_http_methods(["GET", "POST"])
def update_health_info_htmx(request):
    try:
        donor = Donor.objects.get(user=request.user)
    except Donor.DoesNotExist:
        messages.error(request, "Donor profile not found. Please complete your profile first.")
        return redirect('update-profile')

    if request.method == "POST":
        form = DonorHealthInfoForm(request.POST, instance=donor)
        if form.is_valid():
            form.save()
            messages.success(request, "Health information updated successfully.")
            return redirect('donor-dashboard')
    else:
        form = DonorHealthInfoForm(instance=donor)

    return render(request, 'donation/update_health_info.html', {'form': form})

@login_required
def update_health_info(request):
    try:
        donor = Donor.objects.get(user=request.user)
    except Donor.DoesNotExist:
        messages.error(request, "Donor profile not found. Please complete your profile first.")
        return redirect('update-profile')

    if request.method == "POST":
        form = DonorHealthInfoForm(request.POST, instance=donor)
        if form.is_valid():
            form.save()
            messages.success(request, "Health information updated successfully.")
            return redirect('donor-dashboard')
    else:
        form = DonorHealthInfoForm(instance=donor)

    return render(request, 'donation/update_health_info.html', {'form': form})

@login_required
@user_passes_test(is_staff_user)
def admin_dashboard(request):
    today = timezone.now().date()
    
    # Blood Inventory Summary
    blood_inventory = BloodInventory.objects.all()
    critical_inventory = blood_inventory.filter(units__lte=models.F('critical_level')).count()
    total_blood_units = blood_inventory.aggregate(total_units=Sum('units'))['total_units'] or 0
    expiring_soon = blood_inventory.filter(expiry_date__lte=today + timedelta(days=7)).count()
    
    # Blood Type Distribution
    blood_type_stats = BloodInventory.objects.values('blood_type').annotate(
        total_units=Sum('units')
    ).order_by('blood_type')
    
    # Donation Drives Statistics
    upcoming_drives = DonationDrive.objects.filter(start_date__gte=today).order_by('start_date')
    past_drives = DonationDrive.objects.filter(start_date__lt=today).order_by('-start_date')
    
    # Today's Drives
    todays_drives = DonationDrive.objects.filter(start_date=today)
    
    # Registration Statistics
    total_donors = Donor.objects.count()
    recent_registrations = Donor.objects.filter(
        user__date_joined__gte=today - timedelta(days=30)
    ).count()
    
    # Donation Success Rate
    total_registrations = DriveRegistration.objects.filter(drive__start_date__lt=today).count()
    successful_donations = DriveRegistration.objects.filter(
        drive__start_date__lt=today,
        donation_successful=True
    ).count()
    success_rate = (successful_donations / total_registrations * 100) if total_registrations > 0 else 0
    
    # Recent Activity
    recent_drives = DonationDrive.objects.filter(
        start_date__gte=today - timedelta(days=7)
    ).annotate(
        registered_count=Count('driveregistration')
    ).order_by('-start_date')[:5]
    
    # Monthly Statistics
    this_month_start = today.replace(day=1)
    this_month_donations = DriveRegistration.objects.filter(
        drive__start_date__gte=this_month_start,
        drive__start_date__lte=today,
        donation_successful=True
    ).count()
    
    # Upcoming Events
    next_drives = DonationDrive.objects.filter(
        start_date__gt=today
    ).annotate(
        registered_count=Count('driveregistration')
    ).order_by('start_date')[:5]
    
    context = {
        'blood_inventory_summary': {
            'total_units': total_blood_units,
            'critical_inventory': critical_inventory,
            'expiring_soon': expiring_soon,
        },
        'blood_type_stats': blood_type_stats,
        'drive_statistics': {
            'upcoming_count': upcoming_drives.count(),
            'past_count': past_drives.count(),
            'today_count': todays_drives.count(),
        },
        'donor_statistics': {
            'total_donors': total_donors,
            'recent_registrations': recent_registrations,
            'success_rate': round(success_rate, 1),
        },
        'monthly_statistics': {
            'this_month_donations': this_month_donations,
        },
        'recent_drives': recent_drives,
        'next_drives': next_drives,
        'today': today,
    }
    
    return render(request, 'donation/admin_dashboard.html', context)

@login_required
@user_passes_test(is_staff_user)
def manage_donors(request):
    # Get all unique cities for the filter
    cities = Donor.objects.values_list('city', flat=True).distinct()
    
    # Get query parameters for filtering
    search_query = request.GET.get('search', '')
    blood_type = request.GET.get('blood_type', '')
    eligibility = request.GET.get('eligibility', '')
    location = request.GET.get('location', '')
    
    # Start with all donors
    donors = Donor.objects.all()
    
    # Apply filters
    if search_query:
        donors = donors.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(contact_number__icontains=search_query)
        )
    
    if blood_type:
        donors = donors.filter(blood_type=blood_type)
    
    if eligibility:
        if eligibility == 'eligible':
            donors = donors.filter(eligibility_status='Good')
        elif eligibility == 'ineligible':
            donors = donors.filter(is_deferred=True)
    
    if location:
        donors = donors.filter(city=location)
    
    # Order donors by name
    donors = donors.order_by('last_name', 'first_name')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(donors, 10)  # Show 10 donors per page
    
    try:
        donors = paginator.page(page)
    except PageNotAnInteger:
        donors = paginator.page(1)
    except EmptyPage:
        donors = paginator.page(paginator.num_pages)
    
    context = {
        'donors': donors,
        'cities': cities,
    }
    
    return render(request, 'donation/manage_donors.html', context)

@login_required
@user_passes_test(is_staff_user)
def add_donor(request):
    if request.method == 'POST':
        try:
            # Generate a unique username from email
            email = request.POST['email']
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            
            # Keep trying until we find a unique username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create user account with a random password
            import random
            import string
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=temp_password,
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name']
            )
            
            # Create donor profile
            donor = Donor.objects.create(
                user=user,
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                email=request.POST['email'],
                contact_number=request.POST['contact_number'],
                blood_type=request.POST['blood_type'],
                birth_date=request.POST['birth_date'],
                gender=request.POST.get('gender', 'O'),  # Default to 'O' if not provided
                address=request.POST['address'],
                city=request.POST['city'],
                barangay=request.POST['barangay']
            )
            
            response_data = {
                'status': 'success',
                'message': 'Donor added successfully.',
                'username': username,
                'temp_password': temp_password
            }
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
@user_passes_test(is_staff_user)
def get_donor_details(request, donor_id):
    try:
        donor = Donor.objects.get(id=donor_id)
        donations = DriveRegistration.objects.filter(donor=donor).select_related('drive')
        
        donation_list = [{
            'date': donation.drive.start_date.strftime('%Y-%m-%d'),
            'location': donation.drive.location,
            'status': 'Completed' if donation.donation_successful else 'Pending'
        } for donation in donations]
        
        data = {
            'id': donor.id,
            'first_name': donor.first_name,
            'last_name': donor.last_name,
            'email': donor.email,
            'contact_number': donor.contact_number,
            'blood_type': donor.blood_type,
            'birth_date': donor.birth_date.strftime('%Y-%m-%d') if donor.birth_date else '',
            'gender': getattr(donor, 'gender', ''),  # Handle missing gender field
            'address': donor.address,
            'city': donor.city,
            'barangay': donor.barangay,
            'emergency_contact': {
                'name': donor.emergency_contact_name,
                'relation': donor.emergency_contact_relation,
                'phone': donor.emergency_contact_phone
            },
            'health_info': {
                'allergies': donor.allergies,
                'chronic_conditions': donor.chronic_conditions,
                'medications': donor.medications,
                'hemoglobin_level': donor.last_hemoglobin_level,
                'last_screening_date': donor.last_screening_date.strftime('%Y-%m-%d') if donor.last_screening_date else '',
                'weight': donor.weight
            },
            'eligibility_status': donor.eligibility_status or 'Pending',
            'is_deferred': donor.is_deferred,
            'deferral_reason': donor.deferral_reason,
            'donations': donation_list
        }
        
        return JsonResponse(data)
        
    except Donor.DoesNotExist:
        return JsonResponse({'error': 'Donor not found'}, status=404)
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # Print full traceback to console
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_staff_user)
def update_donor(request, donor_id):
    if request.method == 'POST':
        try:
            donor = Donor.objects.get(id=donor_id)
            
            # Update donor information
            donor.first_name = request.POST.get('first_name', donor.first_name)
            donor.last_name = request.POST.get('last_name', donor.last_name)
            donor.email = request.POST.get('email', donor.email)
            donor.contact_number = request.POST.get('contact_number', donor.contact_number)
            donor.blood_type = request.POST.get('blood_type', donor.blood_type)
            donor.birth_date = request.POST.get('birth_date', donor.birth_date)
            donor.gender = request.POST.get('gender', donor.gender)
            donor.address = request.POST.get('address', donor.address)
            donor.city = request.POST.get('city', donor.city)
            donor.barangay = request.POST.get('barangay', donor.barangay)
            
            # Update eligibility status if provided
            if 'eligibility_status' in request.POST:
                donor.eligibility_status = request.POST['eligibility_status']
            
            # Handle deferral
            is_deferred = request.POST.get('is_deferred', '').lower() == 'true'
            if is_deferred:
                donor.is_deferred = True
                donor.deferral_reason = request.POST.get('deferral_reason', '')
            else:
                donor.is_deferred = False
                donor.deferral_reason = ''
            
            donor.save()
            
            # Update associated user account
            user = donor.user
            user.first_name = donor.first_name
            user.last_name = donor.last_name
            user.email = donor.email
            user.save()
            
            messages.success(request, 'Donor information updated successfully.')
            return JsonResponse({'status': 'success'})
            
        except Donor.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Donor not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_staff_user)
def delete_donor(request, donor_id):
    if request.method == 'POST':
        try:
            donor = Donor.objects.get(id=donor_id)
            user = donor.user
            
            # Delete donor profile and user account
            donor.delete()
            user.delete()
            
            messages.success(request, 'Donor deleted successfully.')
            return JsonResponse({'status': 'success'})
            
        except Donor.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Donor not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_staff_user)
def export_donors_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="donors_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'

    # Get all donors
    donors = Donor.objects.all().order_by('last_name', 'first_name')
    
    # Create DataFrame
    data = []
    for donor in donors:
        data.append({
            'ID': donor.id,
            'First Name': donor.first_name,
            'Last Name': donor.last_name,
            'Blood Type': donor.blood_type,
            'Gender': donor.get_gender_display(),
            'Contact Number': donor.contact_number,
            'Email': donor.email,
            'Address': donor.address,
            'City': donor.city,
            'Barangay': donor.barangay,
            'Eligibility Status': 'Deferred' if donor.is_deferred else donor.eligibility_status or 'Pending'
        })
    
    df = pd.DataFrame(data)
    
    # Write to Excel
    with BytesIO() as b:
        with pd.ExcelWriter(b, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Donors', index=False)
            
            # Get the xlsxwriter workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Donors']
            
            # Add header formatting
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#CCCCCC',
                'border': 1
            })
            
            # Apply header formatting
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            # Adjust column widths
            for i, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(str(col))
                ) + 2
                worksheet.set_column(i, i, max_length)
        
        # Get the value of the BytesIO buffer and write it to the response
        excel_data = b.getvalue()
        
    response.write(excel_data)
    return response

@login_required
@user_passes_test(is_staff_user)
def export_donors_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="donors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'First Name', 'Last Name', 'Blood Type', 'Gender', 'Contact Number', 
                    'Email', 'Address', 'City', 'Barangay', 'Eligibility Status'])

    donors = Donor.objects.all().order_by('last_name', 'first_name')
    for donor in donors:
        writer.writerow([
            donor.id,
            donor.first_name,
            donor.last_name,
            donor.blood_type,
            donor.get_gender_display(),
            donor.contact_number,
            donor.email,
            donor.address,
            donor.city,
            donor.barangay,
            'Deferred' if donor.is_deferred else donor.eligibility_status or 'Pending'
        ])

    return response

@login_required
@user_passes_test(is_staff_user)
def export_donors_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="donors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []

    # Add title
    styles = getSampleStyleSheet()
    elements.append(Paragraph('Donor List', styles['Heading1']))
    elements.append(Paragraph(f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', styles['Normal']))

    # Prepare data
    donors = Donor.objects.all().order_by('last_name', 'first_name')
    data = [['ID', 'Name', 'Blood Type', 'Contact Number', 'Email', 'Address', 'Status']]
    
    for donor in donors:
        data.append([
            str(donor.id),
            f"{donor.first_name} {donor.last_name}",
            donor.blood_type,
            donor.contact_number,
            donor.email,
            f"{donor.address}, {donor.barangay}, {donor.city}",
            'Deferred' if donor.is_deferred else donor.eligibility_status or 'Pending'
        ])

    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    
    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response
