from django import forms
from django.forms import inlineformset_factory
from .models import ClientPersonalInfo, Beneficiary
import re


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
        "client_middle_name": "Middle name",
        "client_last_name": "Last name",
        "client_address": "Home address",
        "client_contact_number": "09123456789",
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
        name = self.cleaned_data.get("client_first_name", "").strip()
        if not name:
            raise forms.ValidationError("First name is required.")
        if not re.match(r"^[A-Za-z\s\-]+$", name):
            raise forms.ValidationError("First name can only contain letters, spaces, or hyphens.")
        return name.title()

    def clean_client_last_name(self):
        name = self.cleaned_data.get("client_last_name", "").strip()
        if not name:
            raise forms.ValidationError("Last name is required.")
        if not re.match(r"^[A-Za-z\s\-]+$", name):
            raise forms.ValidationError("Last name can only contain letters, spaces, or hyphens.")
        return name.title()

    def clean_client_contact_number(self):
        number = self.cleaned_data.get("client_contact_number", "").strip()
        digits = re.sub(r"\D", "", number)

        if len(digits) == 11 and digits.startswith("09"):
            return "+63" + digits[1:]

        if len(digits) == 12 and digits.startswith("639"):
            return "+" + digits

        if len(digits) == 13 and digits.startswith("639"):
            return "+" + digits[1:]

        raise forms.ValidationError("Invalid Philippine phone number. Use 09XXXXXXXXX.")

    def clean_client_address(self):
        address = self.cleaned_data.get("client_address", "").strip()
        if not address:
            raise forms.ValidationError("Home address is required.")
        return address.title()
    
    def clean_client_date_birth(self):
        dob = self.cleaned_data.get("client_date_birth")

        if dob:
            from datetime import date
            today = date.today()

            # Correct age calculation
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

            if age < 18:
                raise forms.ValidationError("Client must be at least 18 years old.")

        return dob

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
