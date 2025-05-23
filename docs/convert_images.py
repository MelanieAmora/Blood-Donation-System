import base64
import os

def image_to_base64(image_path):
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# List of screenshots
screenshots = [
    'login.png',
    'admin_dashboard.png',
    'create_drive.png',
    'donor_profile.png'
]

# Convert each screenshot
for screenshot in screenshots:
    try:
        base64_string = image_to_base64(f'screenshots/{screenshot}')
        print(f'Base64 for {screenshot}:')
        print(base64_string)
        print('\n---\n')
    except FileNotFoundError:
        print(f'Warning: {screenshot} not found') 