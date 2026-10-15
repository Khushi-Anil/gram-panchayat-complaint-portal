from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("complaints", "0003_complaintaction")]

    operations = [
        migrations.AddField(
            model_name="complaint",
            name="escalated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="complaintaction",
            name="is_escalation",
            field=models.BooleanField(default=False),
        ),
    ]
