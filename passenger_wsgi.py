"""
passenger_wsgi.py — Entry point untuk cPanel Python App (Phusion Passenger).

INSTRUKSI SETUP cPanel:
1. Di cPanel → Setup Python App → Create Application
2. Python version: 3.9+ (pilih yang terbaru)
3. Application root: /home/USERNAME/lms.koreanskill.com  (sesuaikan)
4. Application URL: / 
5. Application startup file: passenger_wsgi.py
6. Application entry point: application
7. Klik "Create" → lalu "Run pip install" dari requirements.txt
8. Jangan lupa: python manage.py migrate && python manage.py collectstatic --noinput
"""
import os
import sys

# Sesuaikan path di bawah ini dengan path project Anda di cPanel
# Contoh: /home/koreanskill/lms.koreanskill.com
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_config.settings')

# Production settings via env
os.environ.setdefault('DJANGO_DEBUG', 'False')
os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'lms.koreanskill.com,www.lms.koreanskill.com')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
