from django.db import migrations, models


def migrate_plan_names(apps, schema_editor):
    ClientStatus = apps.get_model("app", "ClientStatus")
    # Rename plan
    ClientStatus.objects.filter(plan="TCT A/R").update(plan="Columbarium")
    # Rename columbarium types
    ClientStatus.objects.filter(columbarium_type="Niche 1").update(
        columbarium_type="TCT A/R Condo Niche 1"
    )
    ClientStatus.objects.filter(columbarium_type="Niche 2").update(
        columbarium_type="TCT A/R Condo Niche 2"
    )
    ClientStatus.objects.filter(columbarium_type="Condo").update(
        columbarium_type="TCT A/R Condo Niche 1"
    )


def reverse_migrate(apps, schema_editor):
    ClientStatus = apps.get_model("app", "ClientStatus")
    ClientStatus.objects.filter(plan="Columbarium").update(plan="TCT A/R")
    ClientStatus.objects.filter(
        columbarium_type="TCT A/R Condo Niche 1"
    ).update(columbarium_type="Niche 1")
    ClientStatus.objects.filter(
        columbarium_type="TCT A/R Condo Niche 2"
    ).update(columbarium_type="Niche 2")


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0020_system_secret"),
    ]

    operations = [
        migrations.AlterField(
            model_name="clientstatus",
            name="plan",
            field=models.CharField(
                max_length=200,
                choices=[
                    ("No Plan",         "No Plan"),
                    ("Lawn lot",        "Lawn lot"),
                    ("Garden lot",      "Garden lot"),
                    ("Junior court",    "Junior court"),
                    ("Executive court", "Executive court"),
                    ("Senior court",    "Senior court"),
                    ("Family estate",   "Family estate"),
                    ("Grand estate",    "Grand estate"),
                    ("THS",             "THS"),
                    ("THTC",            "THTC"),
                    ("Columbarium",     "Columbarium"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="clientstatus",
            name="columbarium_type",
            field=models.CharField(
                max_length=50,
                blank=True,
                null=True,
                choices=[
                    ("TCT A/R Condo Niche 1", "TCT A/R Condo Niche 1"),
                    ("TCT A/R Condo Niche 2", "TCT A/R Condo Niche 2"),
                ],
            ),
        ),
        migrations.RunPython(migrate_plan_names, reverse_migrate),
    ]