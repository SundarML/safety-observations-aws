# observations/forms.py
from django import forms
from .models import Observation, Location

class ObservationCreateForm(forms.ModelForm):
    target_date = forms.DateField(
            widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}) )
    class Meta:
        model = Observation
        fields = ['title','location','description','severity','photo_before','assigned_to', 'target_date']
        

        # target_date = forms.DateField(
        #     widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}) )
        
        # widgets = {
        #     'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})},

class RectificationForm(forms.ModelForm):
    class Meta:
        model = Observation
        fields = ['description','photo_before','rectification_details','photo_after','target_date', 'location']

class VerificationForm(forms.ModelForm):
    APPROVAL_CHOICES = [
        ('approve', 'Approve and Close'),
        ('reject', 'Reject (Send Back to Action Owner)'),
    ]

    verification_action = forms.ChoiceField(
        choices=APPROVAL_CHOICES,
        widget=forms.RadioSelect,
        label="Verification Decision"
    )
    class Meta:
        model = Observation
        fields = ['verification_comment']
        widgets = {
            'verification_comment': forms.Textarea(attrs={'rows': 3}),
        }
    # approved = forms.BooleanField(required=False)
    # comment = forms.CharField(widget=forms.Textarea, required=False)

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name','area', 'facility']
