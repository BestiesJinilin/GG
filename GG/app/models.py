from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User


class ClientPersonalInfo(models.Model):
    client_first_name       = models.CharField(max_length=200)
    client_middle_name      = models.CharField(max_length=200, blank=True, null=True)
    client_last_name        = models.CharField(max_length=200)
    client_address          = models.CharField(max_length=200)
    client_contact_number   = models.CharField(max_length=13)

    client_civil_status = models.CharField(
        max_length=20,
        choices=[
            ("Single",    "Single"),
            ("Married",   "Married"),
            ("Widowed",   "Widowed"),
            ("Separated", "Separated"),
        ],
    )

    client_date_birth        = models.DateField()
    client_religion          = models.CharField(max_length=200)
    client_occupation        = models.CharField(max_length=200)
    client_employer_name     = models.CharField(max_length=200)
    client_employer_address  = models.CharField(max_length=200)
    client_spouse_name       = models.CharField(max_length=200, blank=True, null=True)
    client_spouse_date_birth = models.DateField(blank=True, null=True)
    client_spouse_occupation = models.CharField(max_length=200, blank=True, null=True)
    client_spouse_employer   = models.CharField(max_length=200, blank=True, null=True)

    client_id_type = models.CharField(
        max_length=50,
        choices=[
            ("Passport",         "Passport"),
            ("Driver's License", "Driver's License"),
            ("National ID",      "National ID"),
            ("SSS ID",           "SSS ID"),
            ("GSIS ID",          "GSIS ID"),
            ("UMID",             "UMID"),
            ("Postal ID",        "Postal ID"),
        ],
    )

    client_id_number    = models.CharField(max_length=20)
    client_date_issued  = models.DateField()
    client_place_issued = models.CharField(max_length=200)

    @property
    def full_name(self):
        middle = f" {self.client_middle_name}" if self.client_middle_name else ""
        return f"{self.client_first_name}{middle} {self.client_last_name}".strip()

    def __str__(self):
        return self.full_name


class Beneficiary(models.Model):
    client       = models.ForeignKey(
        ClientPersonalInfo,
        on_delete=models.CASCADE,
        related_name="beneficiaries",
    )
    name         = models.CharField(max_length=200)
    relationship = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.client.full_name}: {self.name} — {self.relationship}"


class ClientStatus(models.Model):
    PLAN_CHOICES = [
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
    ]
    DURATION_CHOICES = [
        (6,  "6 Months"),
        (12, "12 Months"),
        (24, "24 Months"),
        (36, "36 Months"),
        (60, "60 Months"),
    ]

    client           = models.ForeignKey(ClientPersonalInfo, on_delete=models.CASCADE)
    plan             = models.CharField(max_length=200, choices=PLAN_CHOICES)
    monthly_payment  = models.DecimalField(max_digits=20, decimal_places=2)
    duration         = models.IntegerField(choices=DURATION_CHOICES)
    down_payment     = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    # ── NEW: discount on the down payment ────────────────────────────────
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Percentage discount on the down payment (0 = no discount).",
    )

    months_remaining = models.IntegerField()
    start_date       = models.DateField()
    balance          = models.DecimalField(max_digits=20, decimal_places=2)
    paid_balance     = models.DecimalField(max_digits=20, decimal_places=2)
    date_paid        = models.DateTimeField(blank=True, null=True)
    status           = models.BooleanField(default=True)

    # ── Lot location fields ───────────────────────────────────────────────
    phase      = models.CharField(max_length=200, blank=True, null=True)
    block      = models.CharField(max_length=200, blank=True, null=True)
    section    = models.CharField(max_length=200, blank=True, null=True)
    lot_number = models.CharField(max_length=200, blank=True, null=True)
    pa_number  = models.CharField(max_length=200, blank=True, null=True)

    # ── NEW: extended lot tracking ────────────────────────────────────────
    contract_number  = models.CharField(max_length=200, blank=True, null=True)
    interment_date   = models.DateField(blank=True, null=True)
    date_fully_paid  = models.DateField(
        blank=True, null=True,
        help_text="Auto-filled when the last monthly payment is settled.",
    )
    pa_date          = models.DateField(blank=True, null=True)
    
    # ── Column Level (THS / THTC lots) ───────────────────────────────────
    column_level = models.CharField(max_length=200, blank=True, null=True,
                       help_text="Column Level for THS/THTC lots.")
 
    # ── Columbarium ───────────────────────────────────────────────────────
    COLUMBARIUM_TYPE_CHOICES = [
        ("Condo",   "Condo"),
        ("Niche 1", "Niche 1"),
        ("Niche 2", "Niche 2"),
    ]
    COLUMBARIUM_LEVEL_CHOICES = [
        (1, "Level 1"),
        (2, "Level 2"),
        (3, "Level 3"),
        (4, "Level 4"),
    ]
    columbarium_type  = models.CharField(max_length=50, blank=True, null=True,
                            choices=COLUMBARIUM_TYPE_CHOICES)
    columbarium_level = models.IntegerField(blank=True, null=True,
                            choices=COLUMBARIUM_LEVEL_CHOICES)
    tomb_number       = models.CharField(max_length=200, blank=True, null=True)

    # ── NEW: cancellation ─────────────────────────────────────────────────
    is_cancelled        = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True, null=True)
    cancellation_date   = models.DateField(blank=True, null=True)

    # ── Computed property: discounted down payment ────────────────────────
    @property
    def effective_down_payment(self):
        """Down payment after applying the discount percentage."""
        if self.down_payment and self.discount_percent:
            return self.down_payment * (1 - self.discount_percent / 100)
        return self.down_payment

    def __str__(self):
        return self.client.full_name


class Payment(models.Model):
    client_status = models.ForeignKey(
        ClientStatus,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    month     = models.DateField()
    amount    = models.DecimalField(max_digits=20, decimal_places=2)
    is_paid   = models.BooleanField(default=False)
    date_paid = models.DateTimeField(blank=True, null=True)

    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="processed_payments",
    )

    class Meta:
        ordering = ["month"]

    def __str__(self):
        status = "Paid" if self.is_paid else "Unpaid"
        return f"{self.client_status.client.full_name} – {self.month.strftime('%B %Y')} – {status}"


class Booking(models.Model):
    EVENT_CHOICES = [
        ("Viewing",   "Viewing"),
        ("Interment", "Interment"),
    ]
    TIME_SLOTS = [
        ("07:00", "7:00 AM"),
        ("08:00", "8:00 AM"),
        ("09:00", "9:00 AM"),
        ("10:00", "10:00 AM"),
        ("11:00", "11:00 AM"),
        ("12:00", "12:00 PM"),
        ("13:00", "1:00 PM"),
        ("14:00", "2:00 PM"),
        ("15:00", "3:00 PM"),
        ("16:00", "4:00 PM"),
        ("17:00", "5:00 PM"),
    ]
    # ── NEW: booking status ───────────────────────────────────────────────
    STATUS_CHOICES = [
        ("Active",    "Active"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
        ("No Show",   "No Show"),
    ]

    client_name    = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=13)
    event_type     = models.CharField(max_length=50, choices=EVENT_CHOICES)
    booking_date   = models.DateField()
    booking_time   = models.CharField(max_length=5, choices=TIME_SLOTS)
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    # ── NEW fields ────────────────────────────────────────────────────────
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_at        = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["booking_date", "booking_time"]
        unique_together = [("booking_date", "booking_time")]

    def __str__(self):
        return (
            f"{self.client_name} — {self.event_type} on "
            f"{self.booking_date} at {self.get_booking_time_display()}"
        )


class UserLog(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(
        max_length=200,
        choices=[
            ("General Staff",   "General Staff"),
            ("Financial Staff", "Financial Staff"),
        ],
        null=True, blank=True,
    )
    first_name               = models.CharField(max_length=200, null=True, blank=True)
    middle_name              = models.CharField(max_length=200, null=True, blank=True)
    last_name                = models.CharField(max_length=200, null=True, blank=True)
    date_of_birth            = models.DateField(blank=True, null=True)
    government_id            = models.CharField(max_length=200, null=True, blank=True)
    phone_number             = models.CharField(max_length=13, null=True, blank=True)
    address                  = models.CharField(max_length=200, null=True, blank=True)
    email                    = models.EmailField(max_length=200, null=True, blank=True)
    emergency_contact_name   = models.CharField(max_length=200, null=True, blank=True)
    emergency_contact_number = models.CharField(max_length=13, null=True, blank=True)
    time_in                  = models.DateTimeField(blank=True, null=True)
    time_out                 = models.DateTimeField(blank=True, null=True)
    activities               = models.CharField(max_length=500, null=True, blank=True)
    pin                      = models.CharField(max_length=128)  # hashed via make_password

    @property
    def full_name(self):
        middle = f" {self.middle_name}" if self.middle_name else ""
        return f"{self.first_name or ''}{middle} {self.last_name or ''}".strip()

    def __str__(self):
        return self.full_name

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ("Login",           "Login"),
        ("Logout",          "Logout"),
        ("Add Client",      "Add Client"),
        ("Edit Record",     "Edit Record"),
        ("Delete Client",   "Delete Client"),
        ("Add Plan",        "Add Plan"),
        ("Cancel Plan",     "Cancel Plan"),
        ("Add Payment",     "Add Payment"),
        ("Add Booking",     "Add Booking"),
        ("Cancel Booking",  "Cancel Booking"),
        ("Add Employee",    "Add Employee"),
        ("Edit Employee",   "Edit Employee"),
        ("Delete Employee", "Delete Employee"),
    ]
 
    user       = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="activity_logs",
    )
    staff_name = models.CharField(max_length=200, blank=True)
    role       = models.CharField(max_length=200, blank=True)
    action     = models.CharField(max_length=100, choices=ACTION_CHOICES)
    detail     = models.CharField(max_length=500, blank=True)
    timestamp  = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["-timestamp"]
 
    def __str__(self):
        return f"{self.staff_name} — {self.action}"