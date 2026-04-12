from django import forms

from apps.accounts.models import User

from .models import ApplicantProfile, BrideExtendedProfile, GroomExtendedProfile, ProfileMedia


class ApplicantProfileForm(forms.ModelForm):
    class Meta:
        model = ApplicantProfile
        exclude = ("user", "applicant_gender", "submitted_at", "updated_at")
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional_numbers = (
            "weight_kg",
            "height_cm",
            "quran_parts",
            "preferred_partner_age_min",
            "preferred_partner_age_max",
        )
        for name in optional_numbers:
            if name in self.fields:
                self.fields[name].required = False

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        if cleaned.get("preferred_partner_age_min") is None:
            cleaned["preferred_partner_age_min"] = 18
        if cleaned.get("preferred_partner_age_max") is None:
            cleaned["preferred_partner_age_max"] = 50
        if cleaned.get("quran_parts") is None:
            cleaned["quran_parts"] = 0
        lo = cleaned.get("preferred_partner_age_min")
        hi = cleaned.get("preferred_partner_age_max")
        if lo is not None and hi is not None and lo > hi:
            self.add_error(
                "preferred_partner_age_max",
                "يجب أن يكون الحد الأعلى للعمر أكبر أو يساوي الأدنى.",
            )
        return cleaned


class GroomExtraForm(forms.ModelForm):
    class Meta:
        model = GroomExtendedProfile
        exclude = ("profile",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                field.required = False


class BrideExtraForm(forms.ModelForm):
    class Meta:
        model = BrideExtendedProfile
        exclude = ("profile",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                field.required = False


class ProfileMediaForm(forms.ModelForm):
    class Meta:
        model = ProfileMedia
        fields = ("image",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].required = False
