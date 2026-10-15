import complaints.models
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Complaint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("complaint_id", models.CharField(default=complaints.models.make_complaint_id, editable=False, max_length=22, unique=True)),
                ("ward_number", models.PositiveSmallIntegerField()),
                ("category", models.CharField(choices=[("ROADS", "Roads"), ("WATER", "Water supply"), ("DRAINAGE", "Drainage and sanitation"), ("STREETLIGHTS", "Street lights"), ("WELFARE", "Welfare services"), ("OTHER", "Other")], max_length=16)),
                ("title", models.CharField(max_length=120)),
                ("description", models.TextField(max_length=3000)),
                ("status", models.CharField(choices=[("SUBMITTED", "Submitted"), ("UNDER_REVIEW", "Under review"), ("IN_PROGRESS", "In progress"), ("RESOLVED", "Resolved")], default="SUBMITTED", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
