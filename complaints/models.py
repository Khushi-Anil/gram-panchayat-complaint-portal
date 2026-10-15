import uuid
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


def make_complaint_id():
    return f"GP-{timezone.localdate():%Y%m%d}-{uuid.uuid4().hex[:12].upper()}"


class Complaint(models.Model):
    class Category(models.TextChoices):
        ROADS = "ROADS", "Roads"
        WATER = "WATER", "Water supply"
        DRAINAGE = "DRAINAGE", "Drainage and sanitation"
        STREETLIGHTS = "STREETLIGHTS", "Street lights"
        WELFARE = "WELFARE", "Welfare services"
        OTHER = "OTHER", "Other"
        WASTE = "WASTE", "Waste management"
        SANITATION = "SANITATION", "Public sanitation"

    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under review"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"
        REOPENED = "REOPENED", "Reopened"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    complaint_id = models.CharField(
        max_length=24, unique=True, default=make_complaint_id, editable=False
    )
    ward_number = models.PositiveSmallIntegerField()
    village_name = models.CharField(max_length=100, blank=True)
    location_landmark = models.CharField(max_length=240, blank=True)
    noticed_on = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=16, choices=Category.choices)
    title = models.CharField(max_length=120)
    description = models.TextField(max_length=3000)
    photo = models.FileField(upload_to="complaint_photos/%Y/%m/", blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.SUBMITTED
    )
    priority = models.CharField(
        max_length=8, choices=Priority.choices, default=Priority.MEDIUM
    )
    assigned_to = models.CharField(max_length=120, blank=True)
    target_resolution_at = models.DateTimeField(null=True, blank=True)
    verified_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    tracking_secret_hash = models.CharField(max_length=128, blank=True, default="")
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="archived_complaints",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="citizen_complaints",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.complaint_id

    @property
    def is_overdue(self):
        return bool(
            self.target_resolution_at
            and self.target_resolution_at < timezone.now()
            and self.status not in (self.Status.RESOLVED, self.Status.CLOSED)
        )


class ComplaintAction(models.Model):
    complaint = models.ForeignKey(
        Complaint, on_delete=models.CASCADE, related_name="actions"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaint_actions",
    )
    previous_status = models.CharField(
        max_length=16, choices=Complaint.Status.choices, blank=True
    )
    new_status = models.CharField(max_length=16, choices=Complaint.Status.choices)
    note = models.CharField(max_length=500)
    resolution_photo = models.FileField(upload_to="resolution_photos/%Y/%m/", blank=True)
    is_escalation = models.BooleanField(default=False)
    is_archive_event = models.BooleanField(default=False)
    archive_operation = models.CharField(max_length=8, blank=True, choices=(
        ("ARCHIVED", "Archived"), ("RESTORED", "Restored")
    ))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.complaint.complaint_id}: {self.get_new_status_display()}"


class ComplaintContact(models.Model):
    """Private contact details for citizens who explicitly identify themselves."""
    complaint = models.OneToOneField(
        Complaint, on_delete=models.CASCADE, related_name="private_contact"
    )
    citizen_name = models.CharField(max_length=100)
    citizen_phone = models.CharField(max_length=10)
    citizen_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Private contact for {self.complaint.complaint_id}"


class CitizenFeedback(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="citizen_feedback")
    message = models.CharField(max_length=1000)
    requests_reinspection = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PortalFeedback(models.Model):
    name = models.CharField(max_length=100, blank=True)
    village_or_ward = models.CharField(max_length=120, blank=True)
    message = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


def create_tracking_secret():
    return secrets.token_urlsafe(24)
