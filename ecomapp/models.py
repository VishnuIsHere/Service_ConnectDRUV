from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
import uuid



def validate_file_size(file):
    max_size_kb = 500 
    if file.size > max_size_kb * 1024:
        raise ValidationError(f"File size exceeds {max_size_kb} KB.")



class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class Register(AbstractBaseUser,PermissionsMixin):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['name', 'phone_number'] 
    
    def __str__(self):
        return self.email
    
    def delete(self, *args, **kwargs):
        
        OTP.objects.filter(user=self).delete()
       
        Profile.objects.filter(user=self).delete()
      
        super().delete(*args, **kwargs)
    
 

class OTP(models.Model):
    user = models.ForeignKey(Register, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)  # OTP code
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.email}"
    
    def delete(self, *args, **kwargs):
        """Override delete to make sure the OTP is deleted after verification"""
        super().delete(*args, **kwargs)

class Profile(models.Model):
    user = models.OneToOneField(Register, on_delete=models.CASCADE) 
    full_name = models.CharField(max_length=255)
    address = models.TextField()
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)
    house_name = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255)
    pin_code = models.CharField(max_length=6)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
    
    






class Services(models.Model):
    title = models.CharField(max_length=50, db_index=True)
    image = models.ImageField(
        upload_to='images/', 
        null=True, 
        blank=True, 
        validators=[validate_file_size]
    )
    description = models.TextField()
    status = models.CharField(max_length=10, choices=[('Active', 'Active'), ('Inactive', 'Inactive')])

    def __str__(self):
        return self.title


class Subservices(models.Model):
    title = models.CharField(max_length=50, db_index=True)
    services = models.ForeignKey(Services, on_delete=models.CASCADE, related_name='subservices')
    image = models.ImageField(
        upload_to='images/', 
        null=True, 
        blank=True, 
        validators=[validate_file_size]
    )
    description = models.TextField()




class EmployeeRegistration(models.Model):
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    phone_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ServiceRegistry(models.Model):
    employee = models.ForeignKey('EmployeeRegistration', on_delete=models.CASCADE)
    service = models.ForeignKey('Services', on_delete=models.CASCADE)
    min_price = models.PositiveIntegerField()
    max_price = models.PositiveIntegerField()
    description = models.TextField()

    def __str__(self):
        return f"{self.employee.name} - {self.service.title}"




class ServiceRequest(models.Model):
    service_registry = models.ForeignKey(ServiceRegistry, on_delete=models.CASCADE, related_name='service_requests')
    title = models.CharField(max_length=100)
    description = models.TextField()
    from_time = models.DateTimeField()
    to_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    register = models.ForeignKey(Register, on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return self.title
    
    
    
    
    
class BookingList(models.Model):
    register = models.ForeignKey('Register', on_delete=models.CASCADE, null=True, blank=True)
    booking_date = models.DateTimeField()
    
    service_request = models.ForeignKey('ServiceRequest', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Booking for {self.register.name if self.register else 'Unknown'} on {self.booking_date}"
    
    
@receiver(post_save, sender=ServiceRequest,)
def create_booking_list(sender, instance, **kwargs):
   
    BookingList.objects.create(
        register=instance.register,  
        booking_date=instance.created_at,  
        service_request=instance 
    )
    
 
 
    
    
class Review(models.Model):
    user = models.ForeignKey(Register, on_delete=models.CASCADE)
    service = models.ForeignKey(ServiceRegistry, on_delete=models.CASCADE)  # Ensure correct linking
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    
    
    
    
class Payment(models.Model):
    order_id = models.CharField(max_length=100, unique=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(Register, on_delete=models.CASCADE, null=True, blank=True, related_name="user_payments")
    employee = models.ForeignKey(EmployeeRegistration, on_delete=models.CASCADE, null=True, blank=True, related_name="employee_payments")
    amount = models.FloatField()
    status = models.CharField(max_length=50, choices=[('created', 'Created'), ('paid', 'Paid'), ('failed', 'Failed')])
    reference_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)  # Generate unique reference
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.reference_number} for Order {self.order_id}"