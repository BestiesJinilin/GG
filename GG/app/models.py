from django.db import models
from django.contrib.auth.models import User


class ClientPersonalInfo(models.Model):
    client_first_name = models.CharField(max_length=200)
    client_middle_name = models.CharField(max_length=200, blank=True, null=True)
    client_last_name = models.CharField(max_length=200)
    client_address = models.CharField(max_length=200)
    client_contact_number = models.CharField(max_length=13)

    client_civil_status = models.CharField(
        max_length=20,
        choices=[
            ("Single", "Single"),
            ("Married", "Married"),
            ("Widowed", "Widowed"),
            ("Separated", "Separated"),
        ],
    )

    client_date_birth = models.DateField()
    client_religion = models.CharField(max_length=200)
    client_occupation = models.CharField(max_length=200)
    client_employer_name = models.CharField(max_length=200)
    client_employer_address = models.CharField(max_length=200)
    client_spouse_name = models.CharField(max_length=200, blank=True, null=True)
    client_spouse_date_birth = models.DateField(blank=True, null=True)
    client_spouse_occupation = models.CharField(max_length=200, blank=True, null=True)
    client_spouse_employer = models.CharField(max_length=200, blank=True, null=True)

    client_id_type = models.CharField(
        max_length=50,
        choices=[
            ("Passport", "Passport"),
            ("Driver's License", "Driver's License"),
            ("National ID", "National ID"),
            ("SSS ID", "SSS ID"),
            ("GSIS ID", "GSIS ID"),
            ("UMID", "UMID"),
            ("Postal ID", "Postal ID"),
        ],
    )

    client_id_number = models.CharField(max_length=20)
    client_date_issued = models.DateField()
    client_place_issued = models.CharField(max_length=200)

    def full_name(self):
        middle = f" {self.client_middle_name}" if self.client_middle_name else ""
        return f"{self.client_first_name}{middle} {self.client_last_name}".strip()

    def __str__(self):
        return self.full_name()


class Beneficiary(models.Model):
    client = models.ForeignKey(
        ClientPersonalInfo,
        on_delete=models.CASCADE,
        related_name="beneficiaries"
    )
    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.client.full_name()}: {self.name} - {self.relationship}"


class ClientStatus(models.Model):
    client = models.ForeignKey(ClientPersonalInfo, on_delete=models.CASCADE)
    plan = models.CharField(max_length=200, choices=[
        ("Lawn lot", "Lawn lot"),
        ("Garden lot", "Garden lot"),
        ("Junior court", "Junior court"),
        ("Executive court", "Executive court"),
        ("Senior court", "Senior court"),
        ("Family estate", "Family estate"),
        ("Grand estate", "Grand estate"),
    ])
    monthly_payment = models.DecimalField(max_digits=20, decimal_places=2)
    duration = models.IntegerField(max_length=20, choices=[
        (6, "6 Months"),
        (12, "12 Months"),
        (24, "24 Months"),
        (36, "36 Months"),
        (60, "60 Months"),
    ])
    down_payment = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    months_remaining = models.IntegerField()  
    start_date = models.DateField()           
    balance = models.DecimalField(max_digits=20, decimal_places=2)
    paid_balance = models.DecimalField(max_digits=20, decimal_places=2)
    date_paid = models.DateTimeField(blank=True, null=True)
    status = models.BooleanField(default=True)
    phase = models.CharField(max_length=200, blank=True, null=True)
    section = models.CharField(max_length=200, blank=True, null=True)
    lot_number = models.CharField(max_length=200, blank=True, null=True)
    pa_number = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.client.full_name()


class Payment(models.Model):
    client_status = models.ForeignKey(
        ClientStatus,
        on_delete=models.CASCADE,
        related_name="payments"
    )
    month = models.DateField()
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    date_paid = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["month"]

    def __str__(self):
        status = "Paid" if self.is_paid else "Unpaid"
        return f"{self.client_status.client.full_name()} – {self.month.strftime('%B %Y')} – {status}"


class UserLog(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=200,
                            choices= [
                                ("Office Staff", "Office Staff"),
                            ], null=True, blank=True
                        )
    first_name = models.CharField(max_length=200, null=True, blank=True)
    middle_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, null=True, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    government_id = models.CharField(max_length=200, null=True, blank=True)
    phone_number = models.CharField(max_length=13, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(max_length=200, null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=200, null=True, blank=True)
    emergency_contact_number = models.CharField(max_length=13, null=True, blank=True)
    time_in = models.DateTimeField(blank=True, null=True)
    time_out = models.DateTimeField(blank=True, null=True)
    activities = models.CharField(max_length=500, null=True, blank=True)
    pin = models.IntegerField()

    def full_name(self):
        middle = f" {self.middle_name}" if self.middle_name else ""
        return f"{self.first_name}{middle} {self.last_name}".strip()

    def __str__(self):
        return self.full_name()
