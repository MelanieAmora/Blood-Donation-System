# Barangay Blood Donation System

## Overview
The Barangay Blood Donation System is a comprehensive web-based application designed to streamline blood donation management at the barangay level. This system facilitates efficient donor management, blood inventory tracking, and donation drive organization.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [System Requirements](#system-requirements)
- [User Roles](#user-roles)
- [Usage Guide](#usage-guide)
- [Technical Details](#technical-details)
- [Database Structure](#database-structure)

## Features

### For Donors
- **Profile Management**
  - Personal information management
  - Health history tracking
  - Emergency contact information
  - Donation history viewing

- **Donation Management**
  - View upcoming donation drives
  - Register for blood drives
  - Track donation eligibility
  - Monitor personal impact

- **Health Tracking**
  - Monitor eligibility status
  - Track donation intervals
  - View health metrics
  - Access medical history

### For Administrators
- **Blood Inventory Management**
  - Track blood types and components
  - Monitor stock levels
  - Manage expiry dates
  - Set critical level alerts

- **Donation Drive Management**
  - Create and schedule drives
  - Manage registrations
  - Track attendance
  - Record successful donations

- **Donor Management**
  - View donor profiles
  - Track donation history
  - Manage eligibility status
  - Handle deferrals

## Installation

### Prerequisites
- Python 3.13.3
- Django 5.2.1
- Other dependencies listed in requirements.txt

### Setup Steps
1. Clone the repository
```bash
git clone [repository-url]
```

2. Create a virtual environment
```bash
python -m venv venv
```

3. Activate the virtual environment
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies
```bash
pip install -r requirements.txt
```

5. Run migrations
```bash
python manage.py migrate
```

6. Create superuser
```bash
python manage.py createsuperuser
```

7. Run the development server
```bash
python manage.py runserver
```

## System Requirements

### Software Requirements
- Operating System: Windows/Linux/Mac
- Web Browser: Chrome, Firefox, Safari (latest versions)
- Python 3.13.3 or higher
- Django 5.2.1

### Hardware Requirements
- Processor: 1.5 GHz or higher
- RAM: 4GB minimum
- Storage: 500MB free space
- Internet connection

## User Roles

### Regular Users (Donors)
- Register and manage profile
- View donation history
- Register for drives
- Track personal impact
- Monitor health status

### Administrative Users
- Manage blood inventory
- Organize donation drives
- Monitor donor records
- Generate reports
- Manage system settings

## Usage Guide

### For Donors

#### Registration Process
1. Create new account
2. Complete personal profile
3. Add health information
4. Add emergency contacts

#### Making Donations
1. Check eligibility status
2. Find available drives
3. Register for drive
4. Complete donation
5. View updated history

### For Administrators

#### Managing Inventory
1. Monitor blood levels
2. Update stock quantities
3. Track expiry dates
4. Manage components

#### Organizing Drives
1. Create new drives
2. Set capacity and location
3. Monitor registrations
4. Record donations

## Technical Details

### Technology Stack
- **Backend**: Django 5.2.1
- **Frontend**: Bootstrap 5.3
- **Database**: SQLite
- **Additional Libraries**:
  - Crispy Forms
  - Chart.js
  - Font Awesome 6

### Key Components
- User Authentication System
- Role-based Access Control
- Real-time Inventory Tracking
- Automated Eligibility Checking
- Report Generation System

## Database Structure

### Core Models

#### Donor Model
```python
class Donor(models.Model):
    user = OneToOneField(User)
    first_name = CharField()
    last_name = CharField()
    birth_date = DateField()
    blood_type = CharField(choices=BLOOD_TYPES)
    contact_number = CharField()
    email = EmailField()
    # Additional fields...
```

#### Blood Inventory Model
```python
class BloodInventory(models.Model):
    blood_type = CharField(choices=BLOOD_TYPES)
    component = CharField(choices=COMPONENT_CHOICES)
    units = PositiveIntegerField()
    expiry_date = DateField()
    # Additional fields...
```

#### Donation Drive Model
```python
class DonationDrive(models.Model):
    name = CharField()
    date = DateField()
    location = CharField()
    max_donors = PositiveIntegerField()
    # Additional fields...
```

## Security Features

### Authentication
- User login required
- Role-based access control
- Session management
- Password security

### Data Protection
- Form validation
- CSRF protection
- Secure data storage
- Privacy controls

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE.md file for details.

## Support
For support, please email [support-email] or create an issue in the repository.

## Acknowledgments
- Django Framework
- Bootstrap Team
- Chart.js Contributors
- Font Awesome Team

## Offline Setup Instructions

To ensure the system works offline, follow these steps to set up the required static files:

1. Download the following resources and place them in the appropriate directories:

### Bootstrap 5.3
Download Bootstrap 5.3 from https://getbootstrap.com/docs/5.3/getting-started/download/
- Extract `bootstrap.min.css` to `donation/static/donation/vendor/bootstrap/css/`
- Extract `bootstrap.bundle.min.js` to `donation/static/donation/vendor/bootstrap/js/`

### Font Awesome 6
Download Font Awesome 6 Free from https://fontawesome.com/download
- Extract `all.min.css` to `donation/static/donation/vendor/fontawesome/css/`
- Extract the webfonts folder to `donation/static/donation/vendor/fontawesome/webfonts/`

### Inter Font
Download Inter font files from https://fonts.google.com/specimen/Inter
- Place the following files in `donation/static/donation/fonts/`:
  - Inter-Regular.woff2
  - Inter-Medium.woff2
  - Inter-SemiBold.woff2
  - Inter-Bold.woff2

2. Run Django's collectstatic command:
```bash
python manage.py collectstatic
```

3. Make sure DEBUG is set to True in settings.py when running offline to serve static files.

## Directory Structure
The static files should be organized as follows:
```
donation/static/donation/
├── vendor/
│   ├── bootstrap/
│   │   ├── css/
│   │   │   └── bootstrap.min.css
│   │   └── js/
│   │       └── bootstrap.bundle.min.js
│   └── fontawesome/
│       ├── css/
│       │   └── all.min.css
│       └── webfonts/
│           └── [font files]
├── fonts/
│   ├── inter.css
│   ├── Inter-Regular.woff2
│   ├── Inter-Medium.woff2
│   ├── Inter-SemiBold.woff2
│   └── Inter-Bold.woff2
└── js/
    └── main.js
```

## Development Setup
1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- Unix/MacOS: `source venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Features
- Modern UI with offline-compatible resources
- Blood donation drive management
- Donor registration and management
- Blood inventory tracking
- User authentication and authorization
- Responsive design for all devices

## Notes
- The system uses local static files instead of CDN resources for offline functionality
- All necessary JavaScript functionality is included in main.js
- Custom styling is included in the base template
- The Inter font is served locally for consistent typography 