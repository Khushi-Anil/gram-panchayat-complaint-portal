from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("complaints", "0007_full_prototype_workflow"),
    ]

    operations = [
        migrations.AddField(
            model_name="complaint",
            name="is_archived",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="complaint",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="complaint",
            name="archived_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="archived_complaints",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="complaintaction",
            name="is_archive_event",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="complaintaction",
            name="archive_operation",
            field=models.CharField(
                blank=True,
                choices=[("ARCHIVED", "Archived"), ("RESTORED", "Restored")],
                max_length=8,
            ),
        ),
    ]
