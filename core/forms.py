from django import forms
from .models import DemoRequest

class DemoRequestForm(forms.ModelForm):
    class Meta:
        model = DemoRequest
        fields = [
            "full_name",
            "email",
            "whatsapp_number",
            "company",
            "job_title",
            "message",
        ]

        widgets = {
            "message": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Tell us about your safety challenges (optional)"
            }),
        }
