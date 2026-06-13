# Generated migration — add block field to ClientStatus, create Booking model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_alter_clientstatus_down_payment_and_more'),
    ]

    operations = [
        # Add block column to ClientStatus
        migrations.AddField(
            model_name='clientstatus',
            name='block',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),

        # New Booking model
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('client_name',    models.CharField(max_length=200)),
                ('contact_number', models.CharField(max_length=13)),
                ('event_type',     models.CharField(
                    max_length=50,
                    choices=[('Viewing', 'Viewing'), ('Interment', 'Interment')],
                )),
                ('booking_date', models.DateField()),
                ('booking_time', models.CharField(
                    max_length=5,
                    choices=[
                        ('07:00', '7:00 AM'), ('08:00', '8:00 AM'),
                        ('09:00', '9:00 AM'), ('10:00', '10:00 AM'),
                        ('11:00', '11:00 AM'), ('12:00', '12:00 PM'),
                        ('13:00', '1:00 PM'), ('14:00', '2:00 PM'),
                        ('15:00', '3:00 PM'), ('16:00', '4:00 PM'),
                        ('17:00', '5:00 PM'),
                    ],
                )),
                ('notes',      models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['booking_date', 'booking_time']},
        ),
    ]
