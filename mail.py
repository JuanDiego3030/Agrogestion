import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Agrogestion.settings')
import django
django.setup()

from django.core.mail import send_mail
from django.conf import settings


send_mail(
    'Prueba',
    'Esto es un correo de prueba',
    settings.EMAIL_HOST_USER,
    ['juandiegoaranaperez@gmail.com'],
    fail_silently=False,
)