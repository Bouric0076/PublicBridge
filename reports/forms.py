from django import forms

from .models import AnonymousReport
from .models import Report
from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class AnonymousReportForm(forms.ModelForm):
    class Meta:
        model = AnonymousReport
        fields = ['category', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'placeholder': 'Describe the issue...', 'rows': 5}),
        }


class ReportForm(forms.ModelForm):
    user_contact = forms.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Enter a valid contact number. It must be between 9 and 15 digits and may include a leading '+' sign."
            )
        ],
        required=True
    )

    urgency = forms.IntegerField(
        required=True,
        error_messages={'required': 'Urgency is required.'}
    )

    class Meta:
        model = Report
        fields = ['title', 'description', 'urgency', 'user_contact']

    def clean_urgency(self):
        urgency = self.cleaned_data.get('urgency')
        if urgency < 1 or urgency > 5:
            raise ValidationError('Urgency must be between 1 and 5.')
        return urgency

    def save(self, commit=True):
        # Overriding the save method to include custom logic if needed
        report = super().save(commit=False)  # Do not commit yet
        if commit:
            report.save()  # Save the report if commit is True
        return report