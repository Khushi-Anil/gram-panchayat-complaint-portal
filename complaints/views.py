from datetime import timedelta
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from .forms import (
    ComplaintForm,
    CitizenComplaintEditForm,
    CitizenFeedbackForm,
    ComplaintStatusUpdateForm,
    ComplaintTrackingForm,
    CitizenAuthenticationForm,
    CitizenRegistrationForm,
    OfficialAuthenticationForm,
    PortalFeedbackForm,
)
from .models import Complaint, ComplaintAction, ComplaintContact, CitizenFeedback, PortalFeedback, create_tracking_secret


class OfficialLoginView(LoginView):
    template_name = "registration/official_login.html"
    authentication_form = OfficialAuthenticationForm
    # Staff login redirects are also used when a signed-in citizen is blocked
    # from the official area. Do not redirect that citizen back into a loop.
    redirect_authenticated_user = False
    next_page = reverse_lazy("complaints:official_dashboard")


class OfficialLogoutView(LogoutView):
    next_page = reverse_lazy("complaints:official_login")


class CitizenLoginView(LoginView):
    template_name = "registration/citizen_login.html"
    authentication_form = CitizenAuthenticationForm
    redirect_authenticated_user = False
    next_page = reverse_lazy("complaints:citizen_dashboard")

    def dispatch(self, request, *args, **kwargs):
        if _is_citizen(request.user):
            return redirect("complaints:citizen_dashboard")
        return super().dispatch(request, *args, **kwargs)


class CitizenLogoutView(LogoutView):
    next_page = reverse_lazy("complaints:public_dashboard")


def citizen_register(request):
    if request.user.is_authenticated:
        destination = (
            "complaints:official_dashboard"
            if request.user.is_staff
            else "complaints:citizen_dashboard"
        )
        return redirect(destination)
    if request.method == "POST":
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Your citizen account is ready. Complaints submitted while signed in will appear in My complaints.")
            return redirect("complaints:citizen_dashboard")
    else:
        form = CitizenRegistrationForm()
    return render(request, "registration/citizen_register.html", {"form": form})


def _is_official(user):
    return user.is_authenticated and user.is_active and user.is_staff


def _is_citizen(user):
    return user.is_authenticated and user.is_active and not user.is_staff


def _resolution_target(category, priority, started_at):
    base_days = {
        Complaint.Category.WATER: 3,
        Complaint.Category.STREETLIGHTS: 3,
        Complaint.Category.DRAINAGE: 5,
        Complaint.Category.ROADS: 10,
        Complaint.Category.WELFARE: 4,
        Complaint.Category.OTHER: 7,
    }.get(category, 7)
    if priority == Complaint.Priority.URGENT:
        days = max(1, base_days // 2)
    elif priority == Complaint.Priority.HIGH:
        days = max(2, base_days - 1)
    elif priority == Complaint.Priority.LOW:
        days = base_days + 3
    else:
        days = base_days
    return started_at + timedelta(days=days)


def escalate_overdue_complaints():
    """Record one internal escalation for each overdue unresolved complaint."""
    escalation_days = settings.COMPLAINT_ESCALATION_DAYS
    cutoff = timezone.now() - timedelta(days=escalation_days)
    unresolved_statuses = [
        Complaint.Status.SUBMITTED,
        Complaint.Status.UNDER_REVIEW,
        Complaint.Status.ASSIGNED,
        Complaint.Status.IN_PROGRESS,
        Complaint.Status.REOPENED,
    ]
    candidates = Complaint.objects.filter(
        status__in=unresolved_statuses,
        created_at__lte=cutoff,
        escalated_at__isnull=True,
        is_archived=False,
    ).values_list("pk", flat=True)

    for complaint_pk in candidates:
        with transaction.atomic():
            complaint = (
                Complaint.objects.select_for_update()
                .filter(
                    pk=complaint_pk,
                    status__in=unresolved_statuses,
                    escalated_at__isnull=True,
                    is_archived=False,
                )
                .first()
            )
            if complaint is None:
                continue
            complaint.escalated_at = timezone.now()
            complaint.save(update_fields=["escalated_at"])
            ComplaintAction.objects.create(
                complaint=complaint,
                previous_status=complaint.status,
                new_status=complaint.status,
                note=(
                    f"Automatically marked for escalation after {escalation_days} "
                    "days unresolved. This demo records the escalation internally; "
                    "it does not send a notification."
                ),
                is_escalation=True,
            )


def submit_complaint(request):
    if request.method == "POST":
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            if _is_citizen(request.user):
                complaint.submitted_by = request.user
            complaint.priority = (
                Complaint.Priority.HIGH
                if complaint.category in (Complaint.Category.WATER, Complaint.Category.STREETLIGHTS)
                else Complaint.Priority.MEDIUM
            )
            complaint.target_resolution_at = _resolution_target(
                complaint.category, complaint.priority, timezone.now()
            )
            tracking_secret = create_tracking_secret()
            complaint.tracking_secret_hash = make_password(tracking_secret)
            complaint.save()
            if form.cleaned_data["submission_mode"] == "identified":
                ComplaintContact.objects.create(
                    complaint=complaint,
                    citizen_name=form.cleaned_data["citizen_name"],
                    citizen_phone=form.cleaned_data["citizen_phone"],
                    citizen_email=form.cleaned_data.get("citizen_email", ""),
                )
            ComplaintAction.objects.create(
                complaint=complaint,
                new_status=complaint.status,
                note="Complaint submitted.",
            )
            request.session[f"new_tracking_secret_{complaint.complaint_id}"] = tracking_secret
            return redirect("complaints:success", complaint_id=complaint.complaint_id)
    else:
        initial = {}
        category = request.GET.get("category", "")
        if category in Complaint.Category.values:
            initial["category"] = category
        form = ComplaintForm(initial=initial)
    return render(request, "complaints/submit.html", {"form": form})


@user_passes_test(_is_citizen, login_url="complaints:citizen_login")
def citizen_dashboard(request):
    complaints = Complaint.objects.filter(submitted_by=request.user).order_by("-created_at")
    return render(request, "complaints/citizen_dashboard.html", {"complaints": complaints})


@user_passes_test(_is_citizen, login_url="complaints:citizen_login")
def citizen_complaint_edit(request, complaint_id):
    complaint = get_object_or_404(Complaint, complaint_id=complaint_id, submitted_by=request.user)
    if request.method == "POST":
        form = CitizenComplaintEditForm(request.POST, request.FILES, instance=complaint)
        if form.is_valid():
            changed_fields = list(form.changed_data)
            if not changed_fields:
                messages.info(request, "No complaint details changed.")
                return redirect("complaints:citizen_dashboard")
            with transaction.atomic():
                current = Complaint.objects.select_for_update().get(
                    pk=complaint.pk, submitted_by=request.user
                )
                for field in changed_fields:
                    setattr(current, field, form.cleaned_data[field])
                if "category" in changed_fields:
                    current.target_resolution_at = _resolution_target(
                        current.category, current.priority, current.created_at
                    )
                current.save()
                changed_names = ", ".join(
                    form.fields[field].label or field for field in changed_fields
                )
                ComplaintAction.objects.create(
                    complaint=current,
                    actor=request.user,
                    previous_status=current.status,
                    new_status=current.status,
                    note=f"Citizen edited complaint details: {changed_names}.",
                )
            messages.success(request, "Your complaint was updated.")
            return redirect("complaints:citizen_dashboard")
    else:
        form = CitizenComplaintEditForm(instance=complaint)
    return render(
        request,
        "complaints/citizen_edit.html",
        {"complaint": complaint, "form": form},
    )


def submission_success(request, complaint_id):
    secret = request.session.pop(f"new_tracking_secret_{complaint_id}", "")
    return render(
        request,
        "complaints/success.html",
        {"complaint_id": complaint_id, "tracking_secret": secret},
    )


def track_complaint(request):
    complaint = None
    not_found = False
    secret_valid = False
    actions = []
    if request.method == "POST":
        form = ComplaintTrackingForm(request.POST)
        if form.is_valid():
            complaint = Complaint.objects.filter(
                complaint_id=form.cleaned_data["complaint_id"], is_archived=False
            ).only("complaint_id", "status", "created_at", "target_resolution_at", "priority").first()
            not_found = complaint is None
            if complaint:
                secret = form.cleaned_data.get("tracking_secret", "")
                full = Complaint.objects.get(pk=complaint.pk)
                if secret and full.tracking_secret_hash:
                    secret_valid = check_password(secret, full.tracking_secret_hash)
                complaint = full
                if secret_valid:
                    actions = list(complaint.actions.order_by("created_at", "pk"))
    else:
        form = ComplaintTrackingForm()
    return render(
        request,
        "complaints/track.html",
        {"form": form, "complaint": complaint, "not_found": not_found, "secret_valid": secret_valid, "actions": actions, "tracking_secret_value": request.POST.get("tracking_secret", "") if request.method == "POST" else ""},
    )


def citizen_feedback(request, complaint_id):
    complaint = get_object_or_404(Complaint, complaint_id=complaint_id)
    if request.method != "POST":
        return redirect("complaints:track")
    form = CitizenFeedbackForm(request.POST)
    if not form.is_valid() or form.cleaned_data["complaint_id"].strip().upper() != complaint.complaint_id:
        messages.error(request, "The complaint details could not be verified.")
        return redirect("complaints:track")
    if not complaint.tracking_secret_hash or not check_password(
        form.cleaned_data["tracking_secret"], complaint.tracking_secret_hash
    ):
        messages.error(request, "The complaint details could not be verified.")
        return redirect("complaints:track")
    if complaint.is_archived:
        messages.error(request, "This complaint is archived and cannot receive further feedback.")
        return redirect("complaints:track")

    reinspection = form.cleaned_data["requests_reinspection"]
    if reinspection:
        latest_resolved = complaint.actions.filter(new_status=Complaint.Status.RESOLVED).order_by("-created_at").first()
        if (
            complaint.status not in (Complaint.Status.RESOLVED, Complaint.Status.CLOSED)
            or not latest_resolved
            or latest_resolved.created_at < timezone.now() - timedelta(days=7)
        ):
            messages.error(request, "Reinspection can only be requested within 7 days after resolution.")
            return redirect("complaints:track")
        previous_status = complaint.status
        complaint.status = Complaint.Status.REOPENED
        complaint.save(update_fields=["status"])
        ComplaintAction.objects.create(
            complaint=complaint,
            previous_status=previous_status,
            new_status=Complaint.Status.REOPENED,
            note=("Citizen requested reinspection: " + form.cleaned_data["message"])[:500],
        )
    CitizenFeedback.objects.create(
        complaint=complaint,
        message=form.cleaned_data["message"],
        requests_reinspection=reinspection,
    )
    messages.success(request, "Your feedback was recorded.")
    return redirect("complaints:track")


def public_ledger(request):
    complaints = Complaint.objects.filter(is_archived=False).prefetch_related("actions").order_by("-created_at")
    ward = request.GET.get("ward", "").strip()
    category = request.GET.get("category", "").strip()
    if ward.isdigit():
        complaints = complaints.filter(ward_number=int(ward))
    if category in Complaint.Category.values:
        complaints = complaints.filter(category=category)
    complaints = list(complaints[:100])
    for item in complaints:
        item.public_resolution_action = item.actions.filter(
            new_status=Complaint.Status.RESOLVED
        ).exclude(resolution_photo="").order_by("-created_at").first()
    return render(request, "complaints/ledger.html", {
        "complaints": complaints, "ward_filter": ward,
        "category_filter": category, "categories": Complaint.Category.choices,
    })


def possible_duplicates(request):
    ward = request.GET.get("ward", "")
    category = request.GET.get("category", "")
    if not ward.isdigit() or category not in Complaint.Category.values:
        return JsonResponse({"matches": []})
    open_statuses = [Complaint.Status.SUBMITTED, Complaint.Status.UNDER_REVIEW, Complaint.Status.ASSIGNED, Complaint.Status.IN_PROGRESS, Complaint.Status.REOPENED]
    matches = Complaint.objects.filter(is_archived=False, ward_number=int(ward), category=category, status__in=open_statuses).order_by("-created_at")[:5]
    return JsonResponse({"matches": [{
        "reference": item.complaint_id,
        "title": item.title,
        "status": item.get_status_display(),
        "date": item.created_at.strftime("%d %b %Y"),
    } for item in matches]})


def portal_feedback(request):
    if request.method == "POST":
        form = PortalFeedbackForm(request.POST)
        if form.is_valid():
            PortalFeedback.objects.create(**form.cleaned_data)
            messages.success(request, "Thank you. Your portal suggestion was saved for the development team.")
            return redirect("complaints:portal_feedback")
    else:
        form = PortalFeedbackForm()
    return render(request, "complaints/feedback.html", {"form": form})


def how_it_works(request):
    return render(request, "complaints/how_it_works.html")


def categories(request):
    return render(request, "complaints/categories.html")


def helpdesk(request):
    return render(request, "complaints/helpdesk.html")


def public_dashboard(request):
    active = Complaint.objects.filter(is_archived=False)
    open_statuses = [value for value, _label in Complaint.Status.choices if value not in (Complaint.Status.RESOLVED, Complaint.Status.CLOSED)]
    totals = active.aggregate(
        total=Count("pk"),
        submitted=Count("pk", filter=Q(status=Complaint.Status.SUBMITTED)),
        under_review=Count("pk", filter=Q(status=Complaint.Status.UNDER_REVIEW)),
        assigned=Count("pk", filter=Q(status=Complaint.Status.ASSIGNED)),
        in_progress=Count("pk", filter=Q(status=Complaint.Status.IN_PROGRESS)),
        resolved=Count("pk", filter=Q(status=Complaint.Status.RESOLVED)),
        verified_resolved=Count("pk", filter=Q(verified_resolved=True, status__in=[Complaint.Status.RESOLVED, Complaint.Status.CLOSED])),
        closed=Count("pk", filter=Q(status=Complaint.Status.CLOSED)),
        reopened=Count("pk", filter=Q(status=Complaint.Status.REOPENED)),
    )
    totals["open"] = active.filter(status__in=open_statuses).count()
    totals["escalated"] = active.filter(escalated_at__isnull=False).count()
    totals["overdue"] = active.filter(
        status__in=open_statuses, target_resolution_at__lt=timezone.now()
    ).count()
    resolved_actions = ComplaintAction.objects.filter(complaint__is_archived=False,
        new_status=Complaint.Status.RESOLVED
    ).order_by("created_at").values_list("complaint_id", "created_at")
    first_resolution = {}
    for complaint_pk, resolved_at in resolved_actions:
        first_resolution.setdefault(complaint_pk, resolved_at)
    submitted_at = dict(active.filter(pk__in=first_resolution).values_list("pk", "created_at"))
    durations = [
        (resolved_at - submitted_at[complaint_pk]).total_seconds() / 86400
        for complaint_pk, resolved_at in first_resolution.items()
        if complaint_pk in submitted_at
    ]
    totals["avg_resolution_days"] = round(sum(durations) / len(durations), 1) if durations else None
    totals["has_resolution_data"] = bool(durations)
    ward_rows = list(active.values("ward_number").annotate(
        total=Count("pk"),
        submitted=Count("pk", filter=Q(status=Complaint.Status.SUBMITTED)),
        under_review=Count("pk", filter=Q(status=Complaint.Status.UNDER_REVIEW)),
        assigned=Count("pk", filter=Q(status=Complaint.Status.ASSIGNED)),
        in_progress=Count("pk", filter=Q(status=Complaint.Status.IN_PROGRESS)),
        resolved=Count("pk", filter=Q(status=Complaint.Status.RESOLVED)),
    ).order_by("ward_number"))
    wards = ward_rows
    for row in wards:
        row["ward_label"] = f"Ward {row['ward_number']}"
    category_counts = list(active.values("category").annotate(total=Count("pk")).order_by("category"))
    category_labels = dict(Complaint.Category.choices)
    for row in category_counts:
        row["label"] = category_labels.get(row["category"], row["category"])
    return render(
        request,
        "complaints/public_dashboard.html",
        {"totals": totals, "wards": wards, "category_counts": category_counts},
    )


@user_passes_test(_is_official, login_url="complaints:official_login")
def official_dashboard(request):
    escalate_overdue_complaints()
    archived = request.GET.get("archived") == "1"
    complaints = Complaint.objects.filter(is_archived=archived)
    query = request.GET.get("q", "").strip()[:80]
    ward = request.GET.get("ward", "").strip()
    status = request.GET.get("status", "").strip()
    category = request.GET.get("category", "").strip()
    priority = request.GET.get("priority", "").strip()

    if query:
        complaints = complaints.filter(complaint_id__icontains=query)
    if ward.isdigit():
        complaints = complaints.filter(ward_number=int(ward))
    else:
        ward = ""
    if status in Complaint.Status.values:
        complaints = complaints.filter(status=status)
    else:
        status = ""
    if category in Complaint.Category.values:
        complaints = complaints.filter(category=category)
    else:
        category = ""
    if priority in Complaint.Priority.values:
        complaints = complaints.filter(priority=priority)
    else:
        priority = ""
    return render(
        request,
        "complaints/official_dashboard.html",
        {
            "complaints": complaints,
            "filters": {"q": query, "ward": ward, "status": status, "category": category, "priority": priority, "archived": archived},
            "status_choices": Complaint.Status.choices,
            "category_choices": Complaint.Category.choices,
            "priority_choices": Complaint.Priority.choices,
        },
    )


@user_passes_test(_is_official, login_url="complaints:official_login")
def official_complaint_update(request, complaint_id):
    complaint = get_object_or_404(Complaint, complaint_id=complaint_id, is_archived=False)
    if complaint.status in (Complaint.Status.RESOLVED, Complaint.Status.CLOSED):
        messages.info(request, "This complaint is complete, so staff review is no longer available.")
        return redirect("complaints:official_dashboard")
    if request.method == "POST":
        form = ComplaintStatusUpdateForm(request.POST, request.FILES, complaint=complaint)
        if form.is_valid():
            with transaction.atomic():
                current = Complaint.objects.select_for_update().get(pk=complaint.pk)
                new_status = form.cleaned_data["status"]
                new_priority = form.cleaned_data["priority"]
                new_assignment = form.cleaned_data["assigned_to"].strip()
                new_verified = form.cleaned_data["verified_resolved"]
                changed = (
                    current.status != new_status
                    or current.priority != new_priority
                    or current.assigned_to != new_assignment
                    or current.verified_resolved != new_verified
                    or bool(form.cleaned_data.get("resolution_photo"))
                    or bool(form.cleaned_data.get("note", "").strip())
                )
                if not changed:
                    messages.info(request, "No complaint details changed.")
                else:
                    previous_status = current.status
                    priority_changed = current.priority != new_priority
                    current.status = new_status
                    current.priority = new_priority
                    current.assigned_to = new_assignment
                    current.verified_resolved = new_verified
                    if priority_changed:
                        current.target_resolution_at = _resolution_target(
                            current.category, new_priority, current.created_at
                        )
                    current.save(update_fields=[
                        "status", "priority", "assigned_to", "verified_resolved", "target_resolution_at"
                    ])
                    ComplaintAction.objects.create(
                        complaint=current,
                        actor=request.user,
                        previous_status=previous_status if previous_status != new_status else "",
                        new_status=new_status,
                        note=form.cleaned_data["note"],
                        resolution_photo=form.cleaned_data.get("resolution_photo") or "",
                    )
                    messages.success(request, "Complaint status and action history updated.")
            return redirect(
                "complaints:official_update", complaint_id=complaint.complaint_id
            )
    else:
        form = ComplaintStatusUpdateForm(complaint=complaint, initial={
            "status": complaint.status,
            "priority": complaint.priority,
            "assigned_to": complaint.assigned_to,
            "verified_resolved": complaint.verified_resolved,
        })

    actions = complaint.actions.select_related("actor").all()
    feedback_items = complaint.citizen_feedback.all()
    return render(
        request,
        "complaints/official_update.html",
        {"complaint": complaint, "form": form, "actions": actions, "feedback_items": feedback_items},
    )


@user_passes_test(_is_official, login_url="complaints:official_login")
def official_complaint_archive(request, complaint_id):
    if request.method != "POST":
        return redirect("complaints:official_dashboard")
    with transaction.atomic():
        complaint = get_object_or_404(
            Complaint.objects.select_for_update(), complaint_id=complaint_id
        )
        previous_status = complaint.status
        operation = "RESTORED" if complaint.is_archived else "ARCHIVED"
        complaint.is_archived = operation == "ARCHIVED"
        complaint.archived_at = timezone.now() if complaint.is_archived else None
        complaint.archived_by = request.user if complaint.is_archived else None
        complaint.save(update_fields=["is_archived", "archived_at", "archived_by"])
        action_note = (
            "Complaint archived from the official dashboard. Record retained for audit."
            if operation == "ARCHIVED"
            else "Complaint restored to the active queue by authorized staff."
        )
        ComplaintAction.objects.create(
            complaint=complaint,
            actor=request.user,
            previous_status=previous_status,
            new_status=complaint.status,
            note=action_note,
            is_archive_event=True,
            archive_operation=operation,
        )
    messages.success(request, f"Complaint {complaint.complaint_id} {operation.lower()} successfully.")
    return redirect("complaints:official_dashboard" + ("?archived=1" if complaint.is_archived else ""))
