from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('inventory/', views.inventory_list, name='inventory-list'),
    path('inventory/<int:pk>/', views.inventory_detail, name='inventory-detail'),
    path('drives/', views.drive_list, name='drive-list'),
    path('drives/<int:pk>/', views.drive_detail, name='drive-detail'),
    path('drives/<int:pk>/register/', views.register_for_drive, name='register-for-drive'),
    path('create-drive/', views.create_drive, name='create-drive'),
    path('drives/<int:pk>/registrations/', views.drive_registrations, name='drive-registrations'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_donor, name='register'),
    path('profile/update/', views.update_profile, name='update-profile'),
    path('dashboard/', views.donor_dashboard, name='donor-dashboard'),
    path('manage-inventory/', views.manage_inventory, name='manage-inventory'),
    path('inventory/<int:pk>/edit/', views.edit_inventory, name='edit-inventory'),
    path('inventory/<int:pk>/delete/', views.delete_inventory, name='delete-inventory'),
    path('emergency-contact-health-info/', views.emergency_contact_health_info, name='emergency-contact-health-info'),
    path('download-medical-card/', views.download_medical_card, name='download-medical-card'),
    path('update-health-info/', views.update_health_info, name='update-health-info'),
    path('update-health-info-htmx/', views.update_health_info_htmx, name='update-health-info-htmx'),
    
    # New donor management URLs
    path('manage-donors/', views.manage_donors, name='manage-donors'),
    path('donor/add/', views.add_donor, name='add-donor'),
    path('donor/<int:donor_id>/', views.get_donor_details, name='get-donor-details'),
    path('donor/<int:donor_id>/update/', views.update_donor, name='update-donor'),
    path('donor/<int:donor_id>/delete/', views.delete_donor, name='delete-donor'),
    path('export/donors/excel/', views.export_donors_excel, name='export-donors-excel'),
    path('export/donors/csv/', views.export_donors_csv, name='export-donors-csv'),
    path('export/donors/pdf/', views.export_donors_pdf, name='export-donors-pdf'),
]
