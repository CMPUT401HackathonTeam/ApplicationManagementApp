# forms.py
from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ["profileID", "is_deleted"]  # don’t let users edit internal fields
