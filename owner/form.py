
# owner/forms.py

from django import forms

from customerlog.models import BulkOrder
from .models import CustomerProfile, WaterCan, DeliveryBoyProfile, OwnerProfile

from django import forms
from django.contrib.auth import get_user_model
from .models import CustomerProfile  # adjust import based on your project

User = get_user_model()

class CustomerRegistrationForm(forms.ModelForm):
    username = forms.CharField()
    email = forms.EmailField()
    full_name = forms.CharField()
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = CustomerProfile
        fields = ['phone_number', 'address', 'adhar', 'adharupload']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2

    def save(self, commit=True):
        # Create the user object
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            role='customer'  # explicitly set the role
        )

        # Create the customer profile
        profile = super().save(commit=False)
        profile.user = user
        profile.full_name = self.cleaned_data['full_name']
        if commit:
            profile.save()
        return profile


class CustomerUpdateForm(forms.ModelForm):
    """Form for updating customer profile information without changing the password."""
    class Meta:
        model = CustomerProfile
        fields = ['phone_number', 'address', 'adhar', 'adharupload']



class WaterCanForm(forms.ModelForm):
    class Meta:
        model = WaterCan
        fields = ['name', 'price', 'total_cans_added']




from django import forms
from .models import DailyDeliveryLog

from django import forms
from .models import DailyDeliveryLog

class DailyDeliveryLogForm(forms.ModelForm):
    class Meta:
        model = DailyDeliveryLog
        fields = [
            'schedule',
            'delivery_boy',        # Added delivery_boy field
            'delivery_date',
            'status',
            'confirmed_by_customer',
            'confirmed_by_system',
            'modified_quantity'
        ]
        widgets = {
            'schedule': forms.Select(attrs={'class': 'form-control'}),
            'delivery_boy': forms.Select(attrs={'class': 'form-control'}),
            'delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'confirmed_by_customer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'confirmed_by_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'modified_quantity': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
        }
        labels = {
            'schedule': 'Customer Schedule',
            'delivery_boy': 'Delivery Boy',
            'delivery_date': 'Delivery Date',
            'status': 'Delivery Status',
            'confirmed_by_customer': 'Customer Confirmed',
            'confirmed_by_system': 'System Confirmed',
            'modified_quantity': 'Modified Quantity (if any)'
        }


# forms.py
class AssignBulkOrderForm(forms.ModelForm):
    delivery_boy = forms.ModelChoiceField(queryset=DeliveryBoyProfile.objects.all(), required=True)

    class Meta:
        model = BulkOrder
        fields = ['delivery_boy']


class OwnerProfileForm(forms.ModelForm):
    class Meta:
        model = OwnerProfile
        fields = ['profile_photo', 'owner_name', 'company_name', 'email', 'contact_number', 'address']