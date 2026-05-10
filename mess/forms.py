from __future__ import annotations

import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import LeaveRequest, MealAbsence, StudentProfile, StudentUser

USN_ERROR_MESSAGE = (
    "USN must start with '2AB', contain exactly 10 characters, "
    "and include only letters and numbers."
)
USN_PATTERN = re.compile(r"^2AB[a-zA-Z0-9]{7}$")


def normalize_usn(value: str) -> str:
    return (value or "").strip().upper()


class USNAuthenticationForm(AuthenticationForm):
    """
    Uses Django's built-in AuthenticationForm, but labels the username field as USN.
    """

    username = forms.CharField(label="USN")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrap styling
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["password"].widget.attrs.update({"class": "form-control"})

    def clean_username(self) -> str:
        # Match signup storage: Django auth looks up StudentUser.username in uppercase.
        return normalize_usn(self.cleaned_data.get("username", ""))


class AdminAuthenticationForm(AuthenticationForm):
    """
    Staff/superuser login form using Django's native username + password flow.
    """

    username = forms.CharField(label="Username")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "current-password"}
        )


class StudentSignupForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    usn = forms.CharField(max_length=10)
    email = forms.EmailField()
    room_number = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "password":
                field.widget.attrs.update({"class": "form-control"})
            else:
                field.widget.attrs.update({"class": "form-control"})
        self.fields["usn"].widget.attrs.setdefault("maxlength", "10")

    def clean_usn(self) -> str:
        usn = normalize_usn(self.cleaned_data.get("usn", ""))

        if len(usn) != 10 or not USN_PATTERN.fullmatch(usn):
            raise ValidationError(USN_ERROR_MESSAGE)

        if StudentUser.objects.filter(username=usn).exists():
            raise ValidationError("This USN is already registered.")
        if StudentProfile.objects.filter(usn=usn).exists():
            raise ValidationError("This USN is already registered.")

        return usn


class MealAbsenceForm(forms.ModelForm):
    """
    Single-day absence form.
    """

    class Meta:
        model = MealAbsence
        fields = ["date", "meal_type", "reason"]
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 2}),
            "date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, student: StudentProfile | None = None, **kwargs):
        self.student = student
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned = super().clean()
        if not self.student:
            return cleaned

        date = cleaned.get("date")
        meal_type = cleaned.get("meal_type")

        if date and meal_type:
            if MealAbsence.objects.filter(
                student=self.student,
                date=date,
                meal_type=meal_type,
            ).exists():
                raise ValidationError(
                    "You already submitted an absence for this meal on this date."
                )
        return cleaned


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["from_date", "to_date", "reason"]
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 3}),
            "from_date": forms.DateInput(attrs={"type": "date"}),
            "to_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        from_date = cleaned.get("from_date")
        to_date = cleaned.get("to_date")

        if from_date and to_date and from_date > to_date:
            raise ValidationError("From date cannot be greater than To date.")

        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
