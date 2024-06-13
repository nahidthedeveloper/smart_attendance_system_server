import random
from django.utils import timezone
from .models import OTP


def generate_otp(user):
    otp_code = f"{random.randint(100000, 999999):06d}"  # Generates a 6-digit random code
    otp_instance, created = OTP.objects.update_or_create(
        user=user,
        defaults={'otp': otp_code, 'created_at': timezone.now()}
    )
    return otp_code
