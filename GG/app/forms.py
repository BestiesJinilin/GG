from django import forms
from django.forms import inlineformset_factory
from .models import ClientPersonalInfo, Beneficiary, UserLog, ClientStatus, Booking
import re
from datetime import date


RELATIONSHIP_CHOICES = [
    ("",              "Select Relationship"),
    # Immediate family
    ("Spouse",        "Spouse"),
    ("Son",           "Son"),
    ("Daughter",      "Daughter"),
    ("Father",        "Father"),
    ("Mother",        "Mother"),
    ("Brother",       "Brother"),
    ("Sister",        "Sister"),
    # Extended family
    ("Grandfather",   "Grandfather"),
    ("Grandmother",   "Grandmother"),
    ("Grandson",      "Grandson"),
    ("Granddaughter", "Granddaughter"),
    ("Uncle",         "Uncle"),
    ("Aunt",          "Aunt"),
    ("Nephew",        "Nephew"),
    ("Niece",         "Niece"),
    ("Cousin",        "Cousin"),
    # In-laws
    ("Father-in-law", "Father-in-law"),
    ("Mother-in-law", "Mother-in-law"),
    ("Brother-in-law","Brother-in-law"),
    ("Sister-in-law", "Sister-in-law"),
    # Other
    ("Guardian",      "Guardian"),
    ("Friend",        "Friend"),
    ("Other",         "Other"),
]


# ─────────────────────────────────────────────── helpers ──────────────────────

class BootstrapForm(forms.ModelForm):
    placeholders = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()
            ph = self.placeholders.get(field_name)
            if ph and not isinstance(field.widget, forms.Select):
                field.widget.attrs["placeholder"] = ph

        if "data" in kwargs:
            data = kwargs["data"].copy()
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = value.strip()
            self.data = data

    def clean(self):
        cleaned_data = super().clean()
        for field, value in cleaned_data.items():
            if isinstance(value, str):
                cleaned_data[field] = value.strip()
        return cleaned_data


def clean_name(value, field_name="Name"):
    value = (value or "").strip()
    if not value:
        raise forms.ValidationError(f"{field_name} is required.")
    if not re.match(r"^[A-Za-z\s\-]+$", value):
        raise forms.ValidationError(
            f"{field_name} can only contain letters, spaces, or hyphens."
        )
    return value.title()


def clean_address(value, field_name="Address"):
    value = (value or "").strip()
    if not value:
        raise forms.ValidationError(f"{field_name} is required.")
    return value.title()


def clean_phone_number(number):
    """
    Accepts 09XXXXXXXXX, 639XXXXXXXXX, or +639XXXXXXXXX.
    Always stores as 09XXXXXXXXX (11 digits, no + prefix).
    """
    number = (number or "").strip()
    digits = re.sub(r"\D", "", number)           # strip every non-digit (incl. +)

    if len(digits) == 11 and digits.startswith("09"):
        return digits                             # already in target format

    if len(digits) == 12 and digits.startswith("639"):
        return "0" + digits[2:]                  # 639XXXXXXXXX → 09XXXXXXXXX

    raise forms.ValidationError(
        "Enter a valid Philippine mobile number (09XXXXXXXXX)."
    )


def clean_date_of_birth(dob, min_age=18):
    if dob:
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < min_age:
            raise forms.ValidationError(f"Person must be at least {min_age} years old.")
    return dob


def clean_pin_field(value):
    """Accepts a 4-digit string; preserves leading zeros (e.g. '0010')."""
    pin = str(value or "").strip()
    if not pin.isdigit() or len(pin) != 4:
        raise forms.ValidationError("PIN must be exactly 4 digits (e.g. 0010).")
    return pin


# ─────────────────────────────────────────────── ClientForm ───────────────────

class ClientForm(BootstrapForm):
    class Meta:
        model  = ClientPersonalInfo
        fields = "__all__"
        widgets = {
            "client_date_birth":        forms.DateInput(attrs={"type": "date"}),
            "client_spouse_date_birth": forms.DateInput(attrs={"type": "date"}),
            "client_date_issued":       forms.DateInput(attrs={"type": "date"}),
        }

    placeholders = {
        "client_first_name":        "First name",
        "client_middle_name":       "Middle name (Optional)",
        "client_last_name":         "Last name",
        "client_address":           "Home address",
        "client_contact_number":    "09XXXXXXXXX",
        "client_date_birth":        "YYYY-MM-DD",
        "client_religion":          "Religion",
        "client_occupation":        "Occupation",
        "client_employer_name":     "Employer name",
        "client_employer_address":  "Employer address",
        "client_spouse_name":       "Spouse name",
        "client_spouse_date_birth": "YYYY-MM-DD",
        "client_spouse_occupation": "Spouse occupation",
        "client_spouse_employer":   "Spouse employer",
        "client_id_number":         "Enter ID number",
        "client_date_issued":       "YYYY-MM-DD",
        "client_place_issued":      "Place issued",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        civil_choices = [("", "Select Status")] + list(
            ClientPersonalInfo._meta.get_field("client_civil_status").choices
        )
        self.fields["client_civil_status"] = forms.ChoiceField(
            choices=civil_choices,
            widget=forms.Select(attrs={"class": "form-control"}),
            required=True,
        )
        id_choices = [("", "Select ID Type")] + list(
            ClientPersonalInfo._meta.get_field("client_id_type").choices
        )
        self.fields["client_id_type"] = forms.ChoiceField(
            choices=id_choices,
            widget=forms.Select(attrs={"class": "form-control"}),
            required=True,
        )

    def clean_client_first_name(self):
        return clean_name(self.cleaned_data.get("client_first_name"), "First name")

    def clean_client_last_name(self):
        return clean_name(self.cleaned_data.get("client_last_name"), "Last name")

    def clean_client_contact_number(self):
        return clean_phone_number(self.cleaned_data.get("client_contact_number"))

    def clean_client_address(self):
        return clean_address(self.cleaned_data.get("client_address"), "Home address")

    def clean_client_date_birth(self):
        return clean_date_of_birth(self.cleaned_data.get("client_date_birth"))

    def clean_client_religion(self):
        v = self.cleaned_data.get("client_religion", "").strip()
        if not v:
            raise forms.ValidationError("Religion is required.")
        return v.title()

    def clean_client_occupation(self):
        v = self.cleaned_data.get("client_occupation", "").strip()
        if not v:
            raise forms.ValidationError("Occupation is required.")
        return v.title()

    def clean_client_employer_name(self):
        v = self.cleaned_data.get("client_employer_name", "").strip()
        if not v:
            raise forms.ValidationError("Employer name is required.")
        return v.title()

    def clean_client_employer_address(self):
        v = self.cleaned_data.get("client_employer_address", "").strip()
        if not v:
            raise forms.ValidationError("Employer address is required.")
        return v.title()

    def clean_client_id_type(self):
        v = self.cleaned_data.get("client_id_type")
        if not v:
            raise forms.ValidationError("Please select a valid ID type.")
        return v

    def clean_client_id_number(self):
        v = self.cleaned_data.get("client_id_number", "").strip()
        if not v:
            raise forms.ValidationError("ID number is required.")
        if not v.isdigit():
            raise forms.ValidationError("ID number must contain digits only.")
        if len(v) < 5:
            raise forms.ValidationError("ID number appears too short.")
        return v

    def clean_client_date_issued(self):
        d = self.cleaned_data.get("client_date_issued")
        if d and d > date.today():
            raise forms.ValidationError("Date issued cannot be in the future.")
        return d

    def clean_client_place_issued(self):
        v = self.cleaned_data.get("client_place_issued", "").strip()
        if not v:
            raise forms.ValidationError("Place issued is required.")
        return v.title()


# ─────────────────────────────────────────────── BeneficiaryForm ──────────────

class BeneficiaryForm(forms.ModelForm):
    class Meta:
        model  = Beneficiary
        fields = ("name", "relationship")
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Beneficiary Name",
            }),
            "relationship": forms.Select(
                choices=RELATIONSHIP_CHOICES,
                attrs={"class": "form-select"},
            ),
        }


BeneficiaryFormSet = inlineformset_factory(
    ClientPersonalInfo,
    Beneficiary,
    form=BeneficiaryForm,
    extra=1,
    can_delete=True,
)


# ─────────────────────────────────────────────── EmployeeCreateForm ───────────

class EmployeeCreateForm(BootstrapForm):
    username  = forms.CharField()
    email     = forms.EmailField()
    password  = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    pin = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "4-digit PIN (e.g. 0010)",
            "inputmode": "numeric",
            "maxlength": "4",
        }),
    )

    class Meta:
        model  = UserLog
        fields = [
            "first_name", "middle_name", "last_name",
            "date_of_birth", "address", "phone_number",
            "emergency_contact_name", "emergency_contact_number",
            "role", "government_id",
        ]
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"})}

    placeholders = {
        "username":                 "Username",
        "password":                 "Password",
        "password2":                "Confirm Password",
        "first_name":               "First Name",
        "middle_name":              "Middle name (Optional)",
        "last_name":                "Last name",
        "date_of_birth":            "YYYY-MM-DD",
        "address":                  "Address",
        "phone_number":             "09XXXXXXXXX",
        "email":                    "Email",
        "emergency_contact_name":   "Contact Name",
        "emergency_contact_number": "09XXXXXXXXX",
        "government_id":            "Government ID number",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        role_choices = [("", "Select Role")] + list(
            UserLog._meta.get_field("role").choices
        )
        self.fields["role"] = forms.ChoiceField(
            choices=role_choices,
            widget=forms.Select(attrs={"class": "form-control"}),
            required=True,
        )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if username.lower() == "admin":
            raise forms.ValidationError("The username 'admin' is reserved.")
        return username

    def clean_first_name(self):
        return clean_name(self.cleaned_data.get("first_name"), "First name")

    def clean_last_name(self):
        return clean_name(self.cleaned_data.get("last_name"), "Last name")

    def clean_address(self):
        return clean_address(self.cleaned_data.get("address"), "Home address")

    def clean_phone_number(self):
        return clean_phone_number(self.cleaned_data.get("phone_number"))

    def clean_emergency_contact_number(self):
        return clean_phone_number(self.cleaned_data.get("emergency_contact_number"))

    def clean_date_of_birth(self):
        return clean_date_of_birth(self.cleaned_data.get("date_of_birth"))

    def clean_pin(self):
        return clean_pin_field(self.cleaned_data.get("pin"))

    def clean(self):
        cleaned_data = super().clean()
        pw  = cleaned_data.get("password", "")
        pw2 = cleaned_data.get("password2", "")
        if pw and pw2 and pw != pw2:
            raise forms.ValidationError("Passwords do not match.")
        if pw and len(pw) < 6:
            raise forms.ValidationError("Password must be at least 6 characters.")
        return cleaned_data


# ─────────────────────────────────────────────── EmployeeUpdateForm ───────────

class EmployeeUpdateForm(forms.Form):
    first_name               = forms.CharField()
    middle_name              = forms.CharField(required=False)
    last_name                = forms.CharField()
    date_of_birth            = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    address                  = forms.CharField()
    email                    = forms.EmailField()
    phone_number             = forms.CharField()
    emergency_contact_name   = forms.CharField()
    emergency_contact_number = forms.CharField()
    role                     = forms.ChoiceField(
        choices=[("", "Select Role")] + list(UserLog._meta.get_field("role").choices)
    )
    government_id    = forms.CharField()
    pin              = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={"inputmode": "numeric", "maxlength": "4"}),
    )
    new_password     = forms.CharField(required=False, widget=forms.PasswordInput,
                                       label="New Password (leave blank to keep current)")
    confirm_password = forms.CharField(required=False, widget=forms.PasswordInput,
                                       label="Confirm New Password")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "first_name":               "First Name",
            "middle_name":              "Middle name (Optional)",
            "last_name":                "Last name",
            "address":                  "Address",
            "phone_number":             "09XXXXXXXXX",
            "email":                    "Email",
            "emergency_contact_name":   "Contact Name",
            "emergency_contact_number": "09XXXXXXXXX",
            "government_id":            "Government ID number",
            "pin":                      "4-digit PIN (e.g. 0010)",
            "new_password":             "Leave blank to keep current",
            "confirm_password":         "Confirm new password",
        }
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            if name in placeholders and not isinstance(field.widget, forms.Select):
                field.widget.attrs["placeholder"] = placeholders[name]

    def clean_first_name(self):
        return clean_name(self.cleaned_data.get("first_name"), "First name")

    def clean_last_name(self):
        return clean_name(self.cleaned_data.get("last_name"), "Last name")

    def clean_address(self):
        return clean_address(self.cleaned_data.get("address"), "Home address")

    def clean_phone_number(self):
        return clean_phone_number(self.cleaned_data.get("phone_number"))

    def clean_emergency_contact_number(self):
        return clean_phone_number(self.cleaned_data.get("emergency_contact_number"))

    def clean_date_of_birth(self):
        return clean_date_of_birth(self.cleaned_data.get("date_of_birth"))

    def clean_pin(self):
        return clean_pin_field(self.cleaned_data.get("pin"))

    def clean(self):
        cleaned_data = super().clean()
        new_pw  = cleaned_data.get("new_password", "")
        conf_pw = cleaned_data.get("confirm_password", "")
        if new_pw:
            if len(new_pw) < 6:
                raise forms.ValidationError("New password must be at least 6 characters.")
            if new_pw != conf_pw:
                raise forms.ValidationError("New passwords do not match.")
        return cleaned_data


# ─────────────────────────────────────────────── PlanForm ─────────────────────
# Replace the existing PlanForm class in forms.py with this version.
# Key fix: PLAN_CHOICES now includes THS, THTC, and TCT A/R.

class PlanForm(forms.Form):
    PLAN_CHOICES = [
        ("", "Select Plan"),
        # Standard lots
        ("Lawn lot",        "Lawn lot"),
        ("Garden lot",      "Garden lot"),
        ("Junior court",    "Junior court"),
        ("Executive court", "Executive court"),
        ("Senior court",    "Senior court"),
        ("Family estate",   "Family estate"),
        ("Grand estate",    "Grand estate"),
        # Special types
        ("THS",             "THS"),
        ("THTC",            "THTC"),
        ("TCT A/R",         "TCT A/R"),
    ]
    DURATION_CHOICES = [
        ("", "Select Duration"),
        (6,  "6 Months"),
        (12, "12 Months"),
        (24, "24 Months"),
        (36, "36 Months"),
        (60, "60 Months"),
    ]
    DISCOUNT_CHOICES = [
        (0,  "No discount (0%)"),
        (5,  "5%"),
        (10, "10%"),
        (15, "15%"),
        (20, "20%"),
        (25, "25%"),
        (30, "30%"),
    ]

    plan = forms.ChoiceField(
        choices=PLAN_CHOICES,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_plan"}),
    )
    monthly_payment = forms.DecimalField(
        max_digits=20, decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": "form-control", "placeholder": "e.g. 2500.00",
            "min": "1", "step": "0.01",
        }),
    )
    down_payment = forms.DecimalField(
        max_digits=20, decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            "class": "form-control", "placeholder": "e.g. 5000.00",
            "min": "0", "step": "0.01", "id": "id_down_payment",
        }),
    )
    discount_percent = forms.ChoiceField(
        choices=DISCOUNT_CHOICES,
        required=False,
        initial=0,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_discount_percent"}),
        label="Discount %",
    )
    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    # ── Standard lot location fields ──────────────────────────────────────
    phase = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. P-1", "data-uppercase": "true",}),
    )
    block = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. B-1", "data-uppercase": "true",}),
    )
    section = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. S-A", "data-uppercase": "true",}),
    )
    lot_number = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. L-12", "data-uppercase": "true",}),
    )
    pa_number = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 00123", "data-uppercase": "true",}),
    )

    # ── THS / THTC ────────────────────────────────────────────────────────
    column_level = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control", "placeholder": "e.g. A, B, C","data-uppercase": "true",}),
        label="Column Level",
    )

    # ── Columbarium (TCT A/R) ─────────────────────────────────────────────
    columbarium_type = forms.ChoiceField(
        choices=[
            ("",        "Select Type"),
            ("Condo",   "Condo"),
            ("Niche 1", "Niche 1"),
            ("Niche 2", "Niche 2"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="TCT A/R Type",
    )
    columbarium_level = forms.ChoiceField(
        choices=[
            ("", "Select Level"),
            (1,  "Level 1"),
            (2,  "Level 2"),
            (3,  "Level 3"),
            (4,  "Level 4"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Level",
    )
    tomb_number = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control", "placeholder": "Tomb Number", "data-uppercase": "true",}),
        label="Tomb Number",
    )

    # ── Extended tracking ─────────────────────────────────────────────────
    contract_number = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control", "placeholder": "Contract / P.A. number", "data-uppercase": "true",}),
    )
    interment_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    pa_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    def clean_columbarium_level(self):
        v = self.cleaned_data.get("columbarium_level")
        if v:
            try:
                return int(v)
            except (ValueError, TypeError):
                return None
        return None

    def clean_plan(self):
        v = self.cleaned_data.get("plan")
        if not v:
            raise forms.ValidationError("Please select a plan.")
        return v

    def clean_monthly_payment(self):
        v = self.cleaned_data.get("monthly_payment")
        if v is not None and v <= 0:
            raise forms.ValidationError("Monthly payment must be greater than zero.")
        return v

    def clean_down_payment(self):
        v = self.cleaned_data.get("down_payment")
        if v is not None and v < 0:
            raise forms.ValidationError("Down payment cannot be negative.")
        return v

    def clean_discount_percent(self):
        v = self.cleaned_data.get("discount_percent")
        try:
            v = int(v or 0)
        except (ValueError, TypeError):
            v = 0
        if not (0 <= v <= 100):
            raise forms.ValidationError("Discount must be between 0 and 100.")
        return v

    def clean_duration(self):
        v = self.cleaned_data.get("duration")
        if not v:
            raise forms.ValidationError("Please select a duration.")
        return int(v)
    
    _UPPERCASE_FIELDS = [
        "phase", "block", "section", "lot_number", "pa_number",
        "contract_number", "column_level", "tomb_number",
    ]
 
    def clean(self):
        cleaned_data = super().clean()
        for field in self._UPPERCASE_FIELDS:
            val = cleaned_data.get(field)
            if val and isinstance(val, str):
                cleaned_data[field] = val.strip().upper()
        return cleaned_data


# ─────────────────────────────────────────────── BookingForm ──────────────────

class BookingForm(forms.ModelForm):
    class Meta:
        model  = Booking
        fields = ["client_name", "contact_number", "event_type",
                  "booking_date", "booking_time", "notes"]
        widgets = {
            "booking_date": forms.DateInput(attrs={
                "type": "date", "class": "form-control", "id": "id_booking_date"
            }),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "client_name":    "Full name",
            "contact_number": "09XXXXXXXXX",
        }
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            elif name not in ("booking_date", "notes"):
                field.widget.attrs["class"] = "form-control"
            if name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[name]
        # Hide the native time select — JS slot picker writes into it
        self.fields["booking_time"].widget.attrs.update({
            "class": "form-select d-none",
            "id": "id_booking_time",
        })
 
    def clean_client_name(self):
        v = self.cleaned_data.get("client_name", "").strip()
        if not v:
            raise forms.ValidationError("Client name is required.")
        if not re.match(r"^[A-Za-z\s\.\-]+$", v):
            raise forms.ValidationError(
                "Name can only contain letters, spaces, hyphens, or periods."
            )
        return v.title()
 
    def clean_contact_number(self):
        return clean_phone_number(self.cleaned_data.get("contact_number"))
 
    def clean_booking_date(self):
        d = self.cleaned_data.get("booking_date")
        if d and d < date.today():
            raise forms.ValidationError("Booking date cannot be in the past.")
        return d
 
    def clean(self):
        cleaned = super().clean()
        booking_date = cleaned.get("booking_date")
        booking_time = cleaned.get("booking_time")
        if booking_date and booking_time:
            qs = Booking.objects.filter(
                booking_date=booking_date,
                booking_time=booking_time,
                status="Active",
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"That time slot is already booked on {booking_date}. "
                    "Please choose a different time."
                )
        return cleaned
