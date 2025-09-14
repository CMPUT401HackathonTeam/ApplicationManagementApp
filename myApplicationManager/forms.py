from django import forms
from .models import JobApplication, Profile


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = [
            'company_name', 'position', 'stage',
            'apply_date', 'response_date',
            'job_url', 'is_referred', 'notes'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter position title'
            }),
            'stage': forms.Select(attrs={'class': 'form-control'}),
            'apply_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'response_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'job_url': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/job-posting'
            }),
            'is_referred': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            })
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ["profileID", "is_deleted"]  # don’t let users edit internal fields