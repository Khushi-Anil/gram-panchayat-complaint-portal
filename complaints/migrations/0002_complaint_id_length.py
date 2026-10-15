import complaints.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("complaints", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="complaint",
            name="complaint_id",
            field=models.CharField(
                default=complaints.models.make_complaint_id,
                editable=False,
                max_length=24,
                unique=True,
            ),
        ),
    ]
