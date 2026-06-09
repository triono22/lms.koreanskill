import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(username='admin_lokal').exists():
    User.objects.create_superuser('admin_lokal', 'admin@example.com', 'admin1234')
    print("User created!")
else:
    u = User.objects.get(username='admin_lokal')
    u.set_password('admin1234')
    u.save()
    print("User password reset!")
