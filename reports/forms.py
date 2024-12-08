from django import forms
from .models import AnonymousReport
from .models import Report

class AnonymousReportForm(forms.ModelForm):
    class Meta:
        model = AnonymousReport
        fields = ['category', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'placeholder': 'Describe the issue...', 'rows': 5}),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['title', 'description']
