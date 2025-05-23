from django.db import migrations

def set_default_max_donors(apps, schema_editor):
    DonationDrive = apps.get_model('donation', 'DonationDrive')
    for drive in DonationDrive.objects.all():
        if not drive.max_donors or drive.max_donors == 0:
            drive.max_donors = 10
            drive.save()

class Migration(migrations.Migration):

    dependencies = [
        ('donation', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_default_max_donors),
    ]
