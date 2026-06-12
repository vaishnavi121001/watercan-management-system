from django import forms

from .models import DailySchedule, BulkOrder

from django import forms

from django.contrib.auth.forms import ReadOnlyPasswordHashField


class CustomerLoginForm(forms.Form):
    username = forms.CharField(label="Username")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")



class DailyScheduleForm(forms.ModelForm):
    class Meta:
        model = DailySchedule
        fields = ['water_can', 'quantity_per_day', 'start_date', 'delivery_time','is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'delivery_time': forms.TimeInput(attrs={'type': 'time'}),
        }




class BulkOrderForm(forms.ModelForm):
    class Meta:
        model = BulkOrder
        fields = ['event_name', 'water_can', 'quantity', 'delivery_date', 'delivery_time', 'delivery_address']
        widgets = {
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'delivery_time': forms.TimeInput(attrs={'type': 'time'}),
            'delivery_address': forms.Textarea(attrs={'rows': 3}),
        }
