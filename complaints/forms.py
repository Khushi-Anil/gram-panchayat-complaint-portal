from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re

from .models import Complaint
from .uploads import sanitize_image


class ComplaintForm(forms.ModelForm):
    submission_mode = forms.ChoiceField(
        choices=(("anonymous", "Anonymous"), ("identified", "Share my contact details")),
        initial="anonymous",
        label="Privacy choice",
        widget=forms.RadioSelect,
    )
    citizen_name = forms.CharField(max_length=100, required=False, label="Name (optional)")
    citizen_phone = forms.CharField(max_length=10, required=False, label="Mobile number (optional)")
    citizen_email = forms.EmailField(required=False, label="Email (optional)")
    photo = forms.FileField(required=False, label="Issue photo (optional)")
    description = forms.CharField(
        max_length=1000,
        label="Detailed complaint description",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 5, "minlength": 15, "maxlength": 1000}),
    )

    class Meta:
        model = Complaint
        fields = ["ward_number", "village_name", "location_landmark", "noticed_on", "category", "title", "description", "photo"]
        widgets = {
            "ward_number": forms.NumberInput(
                attrs={"min": 1, "max": 99, "class": "form-control"}
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Briefly describe the issue"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Where is the issue and what needs attention?",
                }
            ),
        }
        labels = {
            "ward_number": "Ward number",
            "village_name": "Village name",
            "location_landmark": "Specific location and landmarks",
            "noticed_on": "Date the problem was noticed (optional)",
            "category": "Issue category",
            "title": "Complaint title",
            "description": "Details",
        }

    def clean_ward_number(self):
        ward = self.cleaned_data["ward_number"]
        if ward < 1 or ward > 99:
            raise forms.ValidationError("Enter a ward number from 1 to 99.")
        return ward

    def clean_village_name(self):
        value = self.cleaned_data["village_name"].strip()
        if not value:
            raise forms.ValidationError("Enter your village name.")
        return value

    def clean_location_landmark(self):
        value = self.cleaned_data["location_landmark"].strip()
        if not value:
            raise forms.ValidationError("Describe a nearby street, building, or landmark.")
        return value

    def clean_description(self):
        value = self.cleaned_data["description"].strip()
        if len(value) < 15:
            raise forms.ValidationError("Please provide at least 15 characters of detail.")
        return value

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        return sanitize_image(photo) if photo else None

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("submission_mode") == "identified":
            name = (cleaned.get("citizen_name") or "").strip()
            phone = (cleaned.get("citizen_phone") or "").strip()
            if len(name) < 2:
                self.add_error("citizen_name", "Enter your name (at least 2 characters) or choose anonymous submission.")
            if not re.fullmatch(r"[6-9]\d{9}", phone):
                self.add_error("citizen_phone", "Enter a valid 10-digit Indian mobile number or choose anonymous submission.")
            cleaned["citizen_name"] = name
            cleaned["citizen_phone"] = phone
        else:
            cleaned["citizen_name"] = ""
            cleaned["citizen_phone"] = ""
            cleaned["citizen_email"] = ""
        return cleaned


class ComplaintTrackingForm(forms.Form):
    complaint_id = forms.CharField(
        max_length=24,
        label="Complaint reference",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Example: GP-20261015-AB12CD34",
                "autocapitalize": "characters",
                "autocomplete": "off",
            }
        ),
    )
    tracking_secret = forms.CharField(
        max_length=100, required=False, label="Private tracking secret (for full details or reopening)",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )

    def clean_complaint_id(self):
        reference = self.cleaned_data["complaint_id"].strip().upper()
        if not re.fullmatch(r"GP-\d{8}-[A-F0-9]{8,12}", reference):
            raise forms.ValidationError("Enter the complaint reference exactly as shown.")
        return reference


class OfficialAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError("This sign-in is for authorized Panchayat staff only.")


class CitizenAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.is_staff:
            raise ValidationError("Use the official staff sign-in page for this account.")


class CitizenRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False, label="Email (optional)")

    class Meta:
        model = User
        fields = ("username", "email")


class ComplaintStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=Complaint.Status.choices,
        label="New status",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    note = forms.CharField(
        max_length=500,
        label="Action note",
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 4, "placeholder": "Record the action taken or reason for this status."}
        ),
    )
    priority = forms.ChoiceField(
        choices=Complaint.Priority.choices,
        label="Urgency priority",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    assigned_to = forms.CharField(
        max_length=120,
        required=False,
        label="Assigned team or official",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Ward officer or water team"}),
    )
    verified_resolved = forms.BooleanField(
        required=False,
        label="Resolution independently verified",
    )
    resolution_photo = forms.FileField(required=False, label="Resolution evidence photo (optional)")

    def clean_resolution_photo(self):
        photo = self.cleaned_data.get("resolution_photo")
        return sanitize_image(photo) if photo else None

    def __init__(self, *args, complaint=None, **kwargs):
        self.complaint = complaint
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        if (
            self.complaint
            and cleaned.get("status") == Complaint.Status.RESOLVED
            and self.complaint.status != Complaint.Status.RESOLVED
        ):
            if not cleaned.get("resolution_photo"):
                self.add_error("resolution_photo", "Upload a resolution evidence photo before marking this complaint resolved.")
            if len((cleaned.get("note") or "").strip()) < 15:
                self.add_error("note", "For a resolution, write a work summary of at least 15 characters.")
        if (
            self.complaint
            and cleaned.get("status") == Complaint.Status.CLOSED
            and self.complaint.status != Complaint.Status.CLOSED
        ):
            has_proof = self.complaint.actions.filter(
                new_status=Complaint.Status.RESOLVED
            ).exclude(resolution_photo="").exists()
            if self.complaint.status != Complaint.Status.RESOLVED or not has_proof:
                self.add_error("status", "Close only after the complaint has been resolved with photo evidence.")
        return cleaned


class CitizenComplaintEditForm(forms.ModelForm):
    description = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 5, "maxlength": 1000}),
        label="Complaint details",
    )

    class Meta:
        model = Complaint
        fields = [
            "ward_number", "village_name", "location_landmark", "noticed_on",
            "category", "title", "description", "photo",
        ]
        widgets = {
            "ward_number": forms.NumberInput(attrs={"min": 1, "max": 99}),
            "noticed_on": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_ward_number(self):
        ward = self.cleaned_data["ward_number"]
        if ward < 1 or ward > 99:
            raise forms.ValidationError("Enter a ward number from 1 to 99.")
        return ward

    def clean_description(self):
        value = self.cleaned_data["description"].strip()
        if len(value) < 15:
            raise forms.ValidationError("Please provide at least 15 characters of detail.")
        return value

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo and getattr(photo, "_committed", False):
            return photo
        return sanitize_image(photo) if photo else self.instance.photo


class PortalFeedbackForm(forms.Form):
    name = forms.CharField(max_length=100, required=False)
    village_or_ward = forms.CharField(max_length=120, required=False)
    message = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={"rows": 4}))


class CitizenFeedbackForm(forms.Form):
    complaint_id = forms.CharField(max_length=24)
    tracking_secret = forms.CharField(max_length=100, widget=forms.PasswordInput)
    message = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={"rows": 4}))
    requests_reinspection = forms.BooleanField(required=False, label="Reopen this complaint for reinspection")
