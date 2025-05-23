from PIL import Image
import os

# Create screenshots directory if it doesn't exist
os.makedirs('screenshots', exist_ok=True)

# Save login screenshot
login_img = Image.open('temp_login.png')
login_img.save('screenshots/login.png')

# Save admin dashboard screenshot
dashboard_img = Image.open('temp_dashboard.png')
dashboard_img.save('screenshots/admin_dashboard.png')

# Save create drive screenshot
create_drive_img = Image.open('temp_create_drive.png')
create_drive_img.save('screenshots/create_drive.png')

# Save donor profile screenshot
donor_profile_img = Image.open('temp_donor_profile.png')
donor_profile_img.save('screenshots/donor_profile.png')

print("Screenshots saved successfully!") 