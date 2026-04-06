from django import forms
from django.forms import inlineformset_factory
from .models import ClientPersonalInfo, Beneficiary, UserLog, ClientStatus
import re
from datetime import date


class BootstrapForm(forms.ModelForm):
    placeholders = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing_class + " form-control").strip()

            placeholder = self.placeholders.get(field_name)
            if placeholder and not isinstance(field.widget, forms.Select):
                field.widget.attrs["placeholder"] = placeholder

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
        raise forms.ValidationError(f"{field_name} can only contain letters, spaces, or hyphens.")
    return value.title()


def clean_address(value, field_name="Address"):
    value = (value or "").strip()
    if not value:
        raise forms.ValidationError(f"{field_name} is required.")
    return value.title()


def clean_phone_number(number):
    number = (number or "").strip()
    digits = re.sub(r"\D", "", number)

    if len(digits) == 11 and digits.startswith("09"):
        return "+63" + digits[1:]
    if len(digits) == 12 and digits.startswith("639"):
        return "+" + digits
    if len(digits) == 13 and digits.startswith("639"):
        return "+" + digits[1:]

    raise forms.ValidationError("Invalid Philippine phone number. Use 09XXXXXXXXX.")


def clean_date_of_birth(dob, min_age=18):
    if dob:
        today = date.today()
        age   = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < min_age:
            raise forms.ValidationError(f"Person must be at least {min_age} years old.")
    return dob


class ClientForm(BootstrapForm):
    class Meta:
        model  = ClientPersonalInfo
        fields = "__all__"
        widgets = {
            "client_date_birth":       forms.DateInput(attrs={"type": "date"}),
            "client_spouse_date_birth": forms.DateInput(attrs={"type": "date"}),
            "client_date_issued":       forms.DateInput(attrs={"type": "date"}),
        }

    placeholders = {
        "client_first_name":       "First name",
        "client_middle_name":      "Middle name (Optional)",
        "client_last_name":        "Last name",
        "client_address":          "Home address",
        "client_contact_number":   "09XXXXXXXXX",
        "client_date_birth":       "YYYY-MM-DD",
        "client_religion":         "Religion",
        "client_occupation":       "Occupation",
        "client_employer_name":    "Employer name",
        "client_employer_address": "Employer address",
        "client_spouse_name":      "Spouse name",
        "client_spouse_date_birth":"YYYY-MM-DD",
        "client_spouse_occupation":"Spouse occupation",
        "client_spouse_employer":  "Spouse employer",
        "client_id_number":        "Enter ID number",
        "client_date_issued":      "YYYY-MM-DD",
        "client_place_issued":     "Place issued",
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


class BeneficiaryForm(forms.ModelForm):
    class Meta:
        model  = Beneficiary
        fields = ("name", "relationship")
        widgets = {
            "name":         forms.TextInput(attrs={"class": "form-control", "placeholder": "Beneficiary Name"}),
            "relationship": forms.TextInput(attrs={"class": "form-control", "placeholder": "Relationship"}),
        }


BeneficiaryFormSet = inlineformset_factory(
    ClientPersonalInfo,
    Beneficiary,
    form=BeneficiaryForm,
    extra=1,
    can_delete=True,
)


class EmployeeCreateForm(BootstrapForm):
    username  = forms.CharField()
    email     = forms.EmailField()
    password  = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model  = UserLog
        fields = [
            "first_name", "middle_name", "last_name",
            "date_of_birth", "address", "phone_number",
            "emergency_contact_name", "emergency_contact_number",
            "role", "government_id", "pin",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }

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
        "pin":                      "4-digit PIN",
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
        pin = self.cleaned_data.get("pin")
        if pin is None or not str(pin).isdigit() or len(str(pin)) != 4:
            raise forms.ValidationError("PIN must be exactly 4 digits.")
        return pin

    def clean(self):
        cleaned_data = super().clean()
        password  = cleaned_data.get("password", "")
        password2 = cleaned_data.get("password2", "")

        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match.")
        if password and len(password) < 6:
            raise forms.ValidationError("Password must be at least 6 characters.")

        return cleaned_data


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
    government_id  = forms.CharField()
    pin            = forms.IntegerField()
    new_password   = forms.CharField(required=False, widget=forms.PasswordInput,
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
            "phone_number":             "09XXXXXXXXX or +63XXXXXXXXX",
            "email":                    "Email",
            "emergency_contact_name":   "Contact Name",
            "emergency_contact_number": "09XXXXXXXXX",
            "government_id":            "Government ID number",
            "pin":                      "4-digit PIN",
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
        pin = self.cleaned_data.get("pin")
        if pin is None or not str(pin).isdigit() or len(str(pin)) != 4:
            raise forms.ValidationError("PIN must be exactly 4 digits.")
        return pin

    def clean(self):
        cleaned_data     = super().clean()
        new_password     = cleaned_data.get("new_password", "")
        confirm_password = cleaned_data.get("confirm_password", "")

        if new_password:
            if len(new_password) < 6:
                raise forms.ValidationError("New password must be at least 6 characters.")
            if new_password != confirm_password:
                raise forms.ValidationError("New passwords do not match.")

        return cleaned_data
    

class PlanForm(forms.Form):
    PLAN_CHOICES = [("", "Select Plan")] + [
        ("Plan A", "Plan A"),
        ("Plan B", "Plan B"),
        ("Plan C", "Plan C"),
    ]
    DURATION_CHOICES = [("", "Select Duration")] + [
        (12,  "12 Months"),
        (24,  "24 Months"),
        (36,  "36 Months"),
        (60,  "60 Months"),
    ]

    plan = forms.ChoiceField(
        choices=PLAN_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
        required=True,
    )
    monthly_payment = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class":       "form-control",
            "placeholder": "e.g. 2000.00",
            "min":         "1",
        }),
        required=True,
    )
    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
        required=True,
    )

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

    def clean_duration(self):
        v = self.cleaned_data.get("duration")
        if not v:
            raise forms.ValidationError("Please select a duration.")
        return int(v)
