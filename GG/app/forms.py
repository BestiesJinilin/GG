from django import forms
from django.forms import inlineformset_factory
from .models import ClientPersonalInfo, Beneficiary, UserLog
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
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < min_age:
            raise forms.ValidationError(f"Person must be at least {min_age} years old.")
    return dob

    

class ClientForm(BootstrapForm):
    class Meta:
        model = ClientPersonalInfo
        fields = "__all__"
        widgets = {
            "client_date_birth": forms.DateInput(attrs={"type": "date"}),
            "client_spouse_date_birth": forms.DateInput(attrs={"type": "date"}),
            "client_date_issued": forms.DateInput(attrs={"type": "date"}),
        }

    placeholders = {
        "client_first_name": "First name",
        "client_middle_name": "Middle name (Optional)",
        "client_last_name": "Last name",
        "client_address": "Home address",
        "client_contact_number": "09XXXXXXXXX",
        "client_civil_status": "Select status",
        "client_date_birth": "YYYY-MM-DD",
        "client_religion": "Religion",
        "client_occupation": "Occupation",
        "client_employer_name": "Employer name",
        "client_employer_address": "Employer address",
        "client_spouse_name": "Spouse name",
        "client_spouse_date_birth": "YYYY-MM-DD",
        "client_spouse_occupation": "Spouse occupation",
        "client_spouse_employer": "Spouse employer",
        "client_id_type": "Select ID type",
        "client_id_number": "Enter ID number",
        "client_date_issued": "YYYY-MM-DD",
        "client_place_issued": "Place issued",
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

        id_choices = [('', 'Select ID Type')] + list(
            ClientPersonalInfo._meta.get_field('client_id_type').choices
        )

        self.fields['client_id_type'] = forms.ChoiceField(
            choices=id_choices,
            widget=forms.Select(attrs={'class': 'form-control'}),
            required=True
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
        religion = self.cleaned_data.get("client_religion", "").strip()
        if not religion:
            raise forms.ValidationError("Religion is required.")
        return religion.title()

    def clean_client_occupation(self):
        occupation = self.cleaned_data.get("client_occupation", "").strip()
        if not occupation:
            raise forms.ValidationError("Occupation is required.")
        return occupation.title()

    def clean_client_employer_name(self):
        employer = self.cleaned_data.get("client_employer_name", "").strip()
        if not employer:
            raise forms.ValidationError("Employer name is required.")
        return employer.title()

    def clean_client_employer_address(self):
        address = self.cleaned_data.get("client_employer_address", "").strip()
        if not address:
            raise forms.ValidationError("Employer address is required.")
        return address.title()

    def clean_client_id_type(self):
        id_type = self.cleaned_data.get('client_id_type')
        if not id_type:
            raise forms.ValidationError('Please select a valid ID type.')
        return id_type

    def clean_client_id_number(self):
        id_num = self.cleaned_data.get("client_id_number", "").strip()

        if not id_num:
            raise forms.ValidationError("ID number is required.")

        if not id_num.isdigit():
            raise forms.ValidationError("ID number must contain digits only.")

        if len(id_num) < 5:
            raise forms.ValidationError("ID number appears too short.")

        return id_num

    def clean_client_date_issued(self):
        date_value = self.cleaned_data.get("client_date_issued")
        if date_value:
            from datetime import date as datedate
            if date_value > datedate.today():
                raise forms.ValidationError("Date issued cannot be in the future.")
        return date_value

    def clean_client_place_issued(self):
        place = self.cleaned_data.get("client_place_issued", "").strip()
        if not place:
            raise forms.ValidationError("Place issued is required.")
        return place.title()


class BeneficiaryForm(forms.ModelForm):
    class Meta:
        model = Beneficiary
        fields = ("name", "relationship")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Beneficiary Name"}),
            "relationship": forms.TextInput(attrs={"class": "form-control", "placeholder": "Relationship"}),
        }


BeneficiaryFormSet = inlineformset_factory(
    ClientPersonalInfo,
    Beneficiary,
    form=BeneficiaryForm,
    extra=1,
    can_delete=True
)


class EmployeeCreateForm(BootstrapForm):
    username = forms.CharField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = UserLog
        fields = [
            "first_name", "middle_name", "last_name",
            "date_of_birth", "address", "phone_number",
            "emergency_contact_name", "emergency_contact_number",
            "role", "government_id", "pin"
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }

    placeholders = {
        "username": "Username",
        "password": "Password",
        "password2": "Confirm Password",
        "first_name": "First Name",
        "middle_name": "Middle name (Optional)",
        "last_name": "Last name",
        "date_of_birth": "YYYY-MM-DD",
        "address": "Address",
        "phone_number": "09XXXXXXXXX",
        "email": "Email",
        "emergency_contact_name": "Contact Name",
        "emergency_contact_number": "09XXXXXXXXX",
        "government_id": "Government ID number",
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


    def clean_employee_first_name(self):
        return clean_name(self.cleaned_data.get("first_name"), "First name")

    def clean_employee_last_name(self):
        return clean_name(self.cleaned_data.get("last_name"), "Last name")

    def clean_employee_address(self):
        return clean_address(self.cleaned_data.get("address"), "Home address")

    def clean_employee_contact_number(self):
        return clean_phone_number(self.cleaned_data.get("phone_number"))

    def clean_employee_date_birth(self):
        return clean_date_of_birth(self.cleaned_data.get("date_of_birth"))
    
    def clean_emecon_name(self):
        return clean_name(self.cleaned_data.get("emergency_contact_name"), "Contact name")

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match.")
        if len(password) < 6:
            raise forms.ValidationError("Password must be at least 6 characters.")

        return cleaned_data
    
    def clean_pin(self):
        pin = self.cleaned_data.get("pin")
        if not str(pin).isdigit() or len(str(pin)) != 4:
            raise forms.ValidationError("PIN must be exactly 4 digits.")
        return pin


