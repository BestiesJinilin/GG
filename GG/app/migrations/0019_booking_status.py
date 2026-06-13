from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0018_activity_log'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('Active',    'Active'),
                    ('Completed', 'Completed'),
                    ('Cancelled', 'Cancelled'),
                    ('No Show',   'No Show'),
                ],
                default='Active',
            ),
        ),
    ]
