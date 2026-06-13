from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0019_booking_status"),   # ← your latest migration
    ]

    operations = [
        migrations.CreateModel(
            name="SystemSecret",
            fields=[
                ("id",              models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key",             models.CharField(max_length=100, unique=True)),
                ("encrypted_value", models.TextField(blank=True, default="")),
                ("label",           models.CharField(blank=True, max_length=200)),
                ("updated_at",      models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["key"]},
        ),
    ]
