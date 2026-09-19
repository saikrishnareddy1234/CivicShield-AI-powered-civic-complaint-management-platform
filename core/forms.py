from django import forms
from .models import Complaint


class ComplaintForm(forms.ModelForm):

    class Meta:
        model = Complaint

        fields = [
            "name",
            "email",
            "phone",
            "category",
            "description",
            "image",
            "location",
            "latitude",
            "longitude",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Enter your full name"
            }),

            "email": forms.EmailInput(attrs={
                "placeholder": "Enter your email"
            }),

            "phone": forms.TextInput(attrs={
                "placeholder": "Enter your phone number"
            }),

            "category": forms.Select(),

            "description": forms.Textarea(attrs={
                "placeholder": "Describe the civic problem...",
                "rows": 5
            }),

            "image": forms.ClearableFileInput(attrs={
                "accept": "image/*"
            }),

            "location": forms.TextInput(attrs={
                "placeholder": "Enter the problem location"
            }),

            "latitude": forms.HiddenInput(),

            "longitude": forms.HiddenInput(),
        }