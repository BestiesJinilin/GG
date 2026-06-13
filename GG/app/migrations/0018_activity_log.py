from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0017_alter_userlog_role'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Add processed_by to Payment ───────────────────────────────────────
        migrations.AddField(
            model_name='payment',
            name='processed_by',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.SET_NULL,
                null=True, blank=True,
                related_name='processed_payments',
            ),
        ),

        # ── Create ActivityLog model ──────────────────────────────────────────
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('staff_name', models.CharField(blank=True, max_length=200)),
                ('role',       models.CharField(blank=True, max_length=200)),
                ('action',     models.CharField(
                    max_length=100,
                    choices=[
                        ('Login',           'Login'),
                        ('Logout',          'Logout'),
                        ('Add Client',      'Add Client'),
                        ('Edit Record',     'Edit Record'),
                        ('Delete Client',   'Delete Client'),
                        ('Add Plan',        'Add Plan'),
                        ('Cancel Plan',     'Cancel Plan'),
                        ('Add Payment',     'Add Payment'),
                        ('Add Booking',     'Add Booking'),
                        ('Cancel Booking',  'Cancel Booking'),
                        ('Add Employee',    'Add Employee'),
                        ('Edit Employee',   'Edit Employee'),
                        ('Delete Employee', 'Delete Employee'),
                    ],
                )),
                ('detail',    models.CharField(blank=True, max_length=500)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True, blank=True,
                    related_name='activity_logs',
                )),
            ],
            options={'ordering': ['-timestamp']},
        ),
    ]
