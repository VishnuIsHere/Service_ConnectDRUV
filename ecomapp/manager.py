import random
from .models import OTP

def generate_otp():
    return str(random.randint(100000, 999999))

def create_otp_for_user(user):
    otp_code = generate_otp()
    OTP.objects.create(user=user, otp_code=otp_code)
    return otp_code
