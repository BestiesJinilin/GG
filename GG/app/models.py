from django.db import models


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
        return f"{self.client.full_name()}: {self.name} - {self.relationship} "


class ClientStatus(models.Model):
    client = models.ForeignKey(ClientPersonalInfo, on_delete=models.CASCADE)
    plan = models.CharField(max_length=200)
    monthly_payment = models.DecimalField(max_digits=20, decimal_places=2)
    duration = models.IntegerField()
    months_remaining = models.IntegerField()
    start_date = models.DateField()
    balance = models.DecimalField(max_digits=20, decimal_places=2)
    paid_balance = models.DecimalField(max_digits=20, decimal_places=2)
    date_paid = models.DateTimeField(blank=True, null=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.client.full_name()


class UserLog(models.Model):
    role = models.CharField(max_length=200)
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    time_in = models.DateTimeField(blank=True, null=True)
    time_out = models.DateTimeField(blank=True, null=True)
    activities = models.CharField(max_length=500)
    pin = models.IntegerField()

    def __str__(self):
        return self.name