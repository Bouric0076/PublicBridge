from django import forms

from .models import Ministry


class MinistryRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password"}),
        label="Password",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm password"}),
        label="Confirm Password",
    )

    class Meta:
        model = Ministry
        fields = ["name", "email", "phone_number", "website", "description", "password"]

    def clean_email(self):
        """Ensure email is unique."""
        email = self.cleaned_data.get("email")
        if Ministry.objects.filter(email=email).exists():
            raise forms.ValidationError("A ministry with this email already exists.")
        return email

    def clean_phone_number(self):
        """Ensure phone number is unique."""
        phone_number = self.cleaned_data.get("phone_number")
        if Ministry.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("A ministry with this phone number already exists.")
        return phone_number

    def clean(self):
        """Validate passwords match."""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")

        return cleaned_data


