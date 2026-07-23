import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aamyproject.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
email = 'attorneyalexbodiford@gmail.com'
password = 'AlEx44@'
first_name = 'alex44'

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password=password, first_name=first_name)
    print("Superuser created.")
else:
    # Optional: Update password if it already exists
    u = User.objects.get(email=email)
    u.set_password(password)
    u.is_superuser = True
    u.is_staff = True
    u.save()
    print("Superuser already exists, updated password and permissions.")
