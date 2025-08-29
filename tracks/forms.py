import re

from django import forms

from .models import Inquiry

COMMON_INPUT = "w-full px-3 py-2 rounded-lg bg-neutral-900 border border-neutral-800"


class InquiryForm(forms.ModelForm):
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Inquiry
        fields = ["name", "contact", "license_type", "message", "track", "honeypot"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Як до вас звертатися?"}),
            "contact": forms.TextInput(attrs={"placeholder": "Email або @telegram"}),
            "license_type": forms.Select(),
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "Коротко що треба"}),
            "track": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ["name", "contact", "license_type", "message"]:
            self.fields[field].widget.attrs["class"] = COMMON_INPUT

    def clean_contact(self):
        v = self.cleaned_data["contact"].strip()

        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        tg_regex = r"^@[A-Za-z0-9_]{3,}$"

        if re.match(email_regex, v):
            return v  # валідний email
        if re.match(tg_regex, v):
            return v  # валідний телеграм
        raise forms.ValidationError("Введіть коректний Email або Telegram (@username).")

    def clean_honeypot(self):
        if self.cleaned_data.get("honeypot"):
            raise forms.ValidationError("Spam detected.")
        return ""
