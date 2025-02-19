from django.core.mail import send_mail
from django.conf import settings
from .models import OTP

def send_otp_via_email(email, otp_code):
    subject = "Your OTP Verification Code"
    message = f"Your OTP code is: {otp_code}. It will expire in 5 minutes."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    send_mail(subject, message, from_email, recipient_list)