# Generated migration — add THS / THTC / TCT A/R lot types and Columbarium fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0014_new_features"),
    ]

    operations = [
        # ── 1. Expand plan choices ────────────────────────────────────────────
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
                    ("TCT A/R",         "TCT A/R"),
                ],
            ),
        ),

        # ── 2. Column Level (shown for THS / THTC lots) ───────────────────────
        migrations.AddField(
            model_name="clientstatus",
            name="column_level",
            field=models.CharField(
                max_length=200,
                blank=True,
                null=True,
                help_text="Column Level — displayed for THS and THTC lots.",
            ),
        ),

        # ── 3. Columbarium: TCT A/R type ──────────────────────────────────────
        migrations.AddField(
            model_name="clientstatus",
            name="columbarium_type",
            field=models.CharField(
                max_length=50,
                blank=True,
                null=True,
                choices=[
                    ("Condo",   "Condo"),
                    ("Niche 1", "Niche 1"),
                    ("Niche 2", "Niche 2"),
                ],
            ),
        ),

        # ── 4. Columbarium: level (1–4) ────────────────────────────────────────
        migrations.AddField(
            model_name="clientstatus",
            name="columbarium_level",
            field=models.IntegerField(
                blank=True,
                null=True,
                choices=[
                    (1, "Level 1"),
                    (2, "Level 2"),
                    (3, "Level 3"),
                    (4, "Level 4"),
                ],
            ),
        ),

        # ── 5. Columbarium: tomb number ────────────────────────────────────────
        migrations.AddField(
            model_name="clientstatus",
            name="tomb_number",
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
    ]
