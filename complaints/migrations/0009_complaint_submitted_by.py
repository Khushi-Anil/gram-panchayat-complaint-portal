from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("complaints", "0008_crud_audited_archive"),
    ]

    operations = [
        migrations.AddField(
            model_name="complaint",
            name="submitted_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="citizen_complaints",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
