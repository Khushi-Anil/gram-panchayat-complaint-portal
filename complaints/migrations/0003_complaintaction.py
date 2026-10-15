import django.conf
import django.db.models.deletion
from django.db import migrations, models


def seed_submission_actions(apps, schema_editor):
    Complaint = apps.get_model("complaints", "Complaint")
    ComplaintAction = apps.get_model("complaints", "ComplaintAction")
    database = schema_editor.connection.alias
    records = []
    submission_dates = []
    for complaint in Complaint.objects.using(database).all().iterator():
        if not ComplaintAction.objects.using(database).filter(complaint_id=complaint.pk).exists():
            records.append(
                ComplaintAction(
                    complaint_id=complaint.pk,
                    previous_status="",
                    new_status=complaint.status,
                    note="Complaint submitted.",
                    created_at=complaint.created_at,
                )
            )
            submission_dates.append(complaint.created_at)
    if records:
        created = ComplaintAction.objects.using(database).bulk_create(records)
        for action, submitted_at in zip(created, submission_dates):
            ComplaintAction.objects.using(database).filter(pk=action.pk).update(
                created_at=submitted_at
            )


class Migration(migrations.Migration):
    dependencies = [
        ("complaints", "0002_complaint_id_length"),
        migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ComplaintAction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("previous_status", models.CharField(blank=True, choices=[("SUBMITTED", "Submitted"), ("UNDER_REVIEW", "Under review"), ("IN_PROGRESS", "In progress"), ("RESOLVED", "Resolved")], max_length=16)),
                ("new_status", models.CharField(choices=[("SUBMITTED", "Submitted"), ("UNDER_REVIEW", "Under review"), ("IN_PROGRESS", "In progress"), ("RESOLVED", "Resolved")], max_length=16)),
                ("note", models.CharField(max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="complaint_actions", to=django.conf.settings.AUTH_USER_MODEL)),
                ("complaint", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="actions", to="complaints.complaint")),
            ],
            options={"ordering": ["-created_at", "-pk"]},
        ),
        migrations.RunPython(seed_submission_actions, migrations.RunPython.noop),
    ]
