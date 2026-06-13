"""
Migration 0014 – new features
- ClientStatus: discount_percent, contract_number, interment_date,
                date_fully_paid, pa_date,
                is_cancelled, cancellation_reason, cancellation_date
- Booking:      status, cancellation_reason, cancelled_at
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0013_alter_clientstatus_plan_alter_userlog_pin_and_more"),
    ]

    operations = [
        # ── ClientStatus new fields ───────────────────────────────────────
        migrations.AddField(
            model_name="clientstatus",
            name="discount_percent",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=5,
                help_text="Discount percentage applied to the down payment (0–100).",
            ),
        ),
        migrations.AddField(
            model_name="clientstatus",
            name="contract_number",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="clientstatus",
            name="interment_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="clientstatus",
            name="date_fully_paid",
            field=models.DateField(
                blank=True,
                null=True,
                help_text="Auto-filled when all monthly payments are settled.",
            ),
        ),
        migrations.AddField(
            model_name="clientstatus",
            name="pa_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="clientstatus",
            name="is_cancelled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="clientstatus",
            name="cancellation_reason",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="clientstatus",
            name="cancellation_date",
            field=models.DateField(blank=True, null=True),
        ),
        # ── Booking new fields ────────────────────────────────────────────
        migrations.AddField(
            model_name="booking",
            name="status",
            field=models.CharField(
                choices=[("Active", "Active"), ("Cancelled", "Cancelled")],
                default="Active",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="cancellation_reason",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
