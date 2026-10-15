from django.contrib import admin

from .models import Complaint, ComplaintAction, ComplaintContact, CitizenFeedback, PortalFeedback


class ComplaintActionInline(admin.TabularInline):
    model = ComplaintAction
    extra = 0
    can_delete = False
    readonly_fields = (
        "actor",
        "previous_status",
        "new_status",
        "note",
        "resolution_photo",
        "is_escalation",
        "is_archive_event",
        "archive_operation",
        "created_at",
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "complaint_id", "ward_number", "category", "status", "priority", "is_archived", "assigned_to", "target_resolution_at", "escalated_at", "created_at"
    )
    list_filter = ("ward_number", "category", "status", "priority", "is_archived", "escalated_at", "created_at")
    search_fields = ("complaint_id", "title", "description")
    readonly_fields = (
        "complaint_id", "ward_number", "village_name", "location_landmark", "noticed_on",
        "category", "title", "description", "photo", "status", "priority", "assigned_to",
        "target_resolution_at", "verified_resolved", "created_at", "escalated_at",
        "tracking_secret_hash",
        "is_archived", "archived_at", "archived_by",
    )
    inlines = (ComplaintActionInline,)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ComplaintAction)
class ComplaintActionAdmin(admin.ModelAdmin):
    list_display = (
        "complaint", "previous_status", "new_status", "is_escalation", "archive_operation", "actor", "created_at"
    )
    list_filter = ("new_status", "is_escalation", "created_at")
    search_fields = ("complaint__complaint_id", "actor__username", "note")
    readonly_fields = (
        "complaint",
        "actor",
        "previous_status",
        "new_status",
        "note",
        "resolution_photo",
        "is_escalation",
        "is_archive_event",
        "archive_operation",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ComplaintContact)
class ComplaintContactAdmin(admin.ModelAdmin):
    list_display = ("complaint", "citizen_name", "citizen_phone", "created_at")
    search_fields = ("complaint__complaint_id", "citizen_name", "citizen_phone", "citizen_email")
    readonly_fields = ("complaint", "citizen_name", "citizen_phone", "citizen_email", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CitizenFeedback)
class CitizenFeedbackAdmin(admin.ModelAdmin):
    list_display = ("complaint", "requests_reinspection", "created_at")
    search_fields = ("complaint__complaint_id", "message")
    readonly_fields = ("complaint", "message", "requests_reinspection", "created_at")
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(PortalFeedback)
class PortalFeedbackAdmin(admin.ModelAdmin):
    list_display = ("created_at", "village_or_ward", "name")
    search_fields = ("name", "village_or_ward", "message")
    readonly_fields = ("name", "village_or_ward", "message", "created_at")
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
