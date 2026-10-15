import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("complaints", "0006_complaint_photo_complaintaction_resolution_photo_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="complaint",
            name="village_name",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="complaint",
            name="location_landmark",
            field=models.CharField(blank=True, max_length=240),
        ),
        migrations.AddField(
            model_name="complaint",
            name="noticed_on",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="complaint",
            name="tracking_secret_hash",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AlterField(
            model_name="complaint",
            name="category",
            field=models.CharField(
                choices=[
                    ("ROADS", "Roads"),
                    ("WATER", "Water supply"),
                    ("DRAINAGE", "Drainage and sanitation"),
                    ("STREETLIGHTS", "Street lights"),
                    ("WELFARE", "Welfare services"),
                    ("OTHER", "Other"),
                    ("WASTE", "Waste management"),
                    ("SANITATION", "Public sanitation"),
                ],
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name="CitizenFeedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.CharField(max_length=1000)),
                ("requests_reinspection", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("complaint", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="citizen_feedback", to="complaints.complaint")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PortalFeedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, max_length=100)),
                ("village_or_ward", models.CharField(blank=True, max_length=120)),
                ("message", models.CharField(max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
