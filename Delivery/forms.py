from django import forms
from .models import DeliveryProof



class DeliveryProofForm(forms.ModelForm):
    class Meta:
        model = DeliveryProof
        fields = [ 'cans_delivered', 'cans_received_empty']


class DeliveryLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
