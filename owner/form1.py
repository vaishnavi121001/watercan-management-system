# owner/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from owner.models import DeliveryBoyProfile

User = get_user_model()

class DeliveryBoyRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=150)  # Add full_name field here
    phone = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    adhar = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}))
    adharupload = forms.ImageField()
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']  # no full_name here because it's in profile

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'delivery_boy'  # Ensure correct role
        if commit:
            user.save()
            DeliveryBoyProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],  # Save full_name here
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                adhar=self.cleaned_data['adhar'],
                adharupload=self.cleaned_data['adharupload'],
                profile_picture=self.cleaned_data.get('profile_picture')
            )
        return user


class DeliveryBoyUpdateForm(forms.ModelForm):
    class Meta:
        model = DeliveryBoyProfile
        fields = ['phone', 'address', 'adhar', 'adharupload', 'profile_picture']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'adhar': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['adharupload'].required = False
        self.fields['profile_picture'].required = False
