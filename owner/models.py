# owner/models.py (or accounts/models.py)
from email.policy import default

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, role='customer', **extra_fields):
        if not username:
            raise ValueError("The Username must be set")
        user = self.model(username=username, email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, role='admin', **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('delivery_boy', 'Delivery Boy'),
        ('admin', 'Admin'),
    )

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return f"{self.username} ({self.role})"

class CustomerProfile(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, limit_choices_to={'role': 'customer'})
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    adhar = models.TextField()
    adharupload = models.ImageField(upload_to='adhar_uploads/')
    registration_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class DeliveryBoyProfile(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, limit_choices_to={'role': 'delivery_boy'})
    full_name = models.CharField(max_length=150,default='***')  # Add this line
    phone = models.CharField(max_length=15)
    address = models.TextField()
    adhar = models.TextField()
    adharupload = models.ImageField(upload_to='adhar_uploads/')
    profile_picture = models.ImageField(upload_to='delivery_profiles/', blank=True, null=True)
    joining_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class WaterCan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    total_cans_added = models.PositiveIntegerField(default=0)
    current_stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class DailyDeliveryLog(models.Model):
    schedule = models.ForeignKey('customerlog.DailySchedule', on_delete=models.CASCADE)
    delivery_boy = models.ForeignKey('DeliveryBoyProfile', on_delete=models.CASCADE)
    delivery_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('Scheduled', 'Scheduled'),
            ('Cancelled', 'Cancelled'),
            ('Delivered', 'Delivered'),
            ('Confirmed', 'Confirmed'),
            ('Auto-Confirmed', 'Auto-Confirmed'),
        ],
        default='Scheduled'
    )
    confirmed_by_customer = models.BooleanField(default=False)
    confirmed_by_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_quantity = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.schedule.customer.user.username} - {self.delivery_date} - {self.status}"


class MonthlyBill(models.Model):
    customer = models.ForeignKey('owner.CustomerProfile', on_delete=models.CASCADE)
    month = models.DateField()
    total_cans = models.IntegerField()
    amount_due = models.DecimalField(max_digits=7, decimal_places=2)
    payment_status = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('Paid', 'Paid')]
    )
    generated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username} - {self.month.strftime('%B %Y')}"



class OwnerProfile(models.Model):
    profile_photo = models.ImageField(upload_to='owner_photos/', default='default_profile.png')
    owner_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    email = models.EmailField()
    contact_number = models.CharField(max_length=15)
    address = models.TextField()

    def _str_(self):
        return f"{self.owner_name} ({self.company_name})"

import uuid

class Bill(models.Model):
    customer = models.ForeignKey('CustomerProfile', on_delete=models.CASCADE)
    month = models.DateField()
    total_cans = models.PositiveIntegerField(default=0)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_status = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('Paid', 'Paid')],
        default='Pending'
    )
    is_paid = models.BooleanField(default=False)
    payment_time = models.DateTimeField(blank=True, null=True)

    qr_code = models.ImageField(upload_to='qrcodes/', null=True, blank=True)
    pdf_bill = models.FileField(upload_to='pdfbills/', null=True, blank=True)

    payment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def _str_(self):
        return f"Bill for {self.customer.user.username} - {self.month}"
