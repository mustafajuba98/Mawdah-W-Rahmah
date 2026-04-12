from datetime import date

from django import forms
from django.contrib.auth.models import Group

from apps.accounts.models import User
from apps.profiles.models import ApplicantProfile, BrideExtendedProfile, GroomExtendedProfile

ROLE_GROUP_NAMES = ("platform_admin", "moderator")


class ConsoleUserEditForm(forms.ModelForm):
    role_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.filter(name__in=ROLE_GROUP_NAMES).order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="أدوار المنصة (مجموعات)",
    )

    class Meta:
        model = User
        fields = ("email", "is_active", "is_staff", "profile_status", "applicant_gender")
        labels = {
            "email": "البريد",
            "is_active": "الحساب نشط",
            "is_staff": "صلاحية staff (لوحة إدارية قديمة — عادة لا حاجة)",
            "profile_status": "حالة الحساب",
            "applicant_gender": "نوع مقدّم الطلب (عريس/عروس)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["role_groups"].initial = self.instance.groups.filter(
                name__in=ROLE_GROUP_NAMES
            )

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and "role_groups" in self.cleaned_data:
            role_qs = list(Group.objects.filter(name__in=ROLE_GROUP_NAMES))
            user.groups.remove(*role_qs)
            user.groups.add(*self.cleaned_data["role_groups"])
        return user


class ConsoleUserCreateForm(forms.Form):
    email = forms.EmailField(label="البريد")
    password = forms.CharField(
        label="كلمة المرور",
        widget=forms.PasswordInput,
        min_length=8,
    )
    applicant_gender = forms.ChoiceField(
        label="النوع",
        choices=User.ApplicantGender.choices,
    )
    profile_status = forms.ChoiceField(
        label="حالة الحساب",
        choices=User.ProfileStatus.choices,
        initial=User.ProfileStatus.ACTIVE,
    )
    full_name = forms.CharField(
        label="الاسم الظاهر في الملف",
        max_length=200,
        initial="مستخدم جديد",
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("هذا البريد مستخدم بالفعل.")
        return email

    def save(self):
        data = self.cleaned_data
        user = User(
            email=data["email"],
            profile_status=data["profile_status"],
            applicant_gender=data["applicant_gender"],
            is_staff=False,
            is_superuser=False,
        )
        user.set_password(data["password"])
        user.save()
        profile = ApplicantProfile.objects.create(
            user=user,
            full_name=data["full_name"],
            birth_date=date(1995, 6, 15),
            governorate="cairo",
            marital_status=ApplicantProfile.MaritalStatus.SINGLE,
            residence_summary="القاهرة — تجريبي",
            about_me="حساب تجريبي.",
            partner_specs="—",
            applicant_gender=data["applicant_gender"],
        )
        if data["applicant_gender"] == User.ApplicantGender.MALE:
            GroomExtendedProfile.objects.get_or_create(profile=profile)
        else:
            BrideExtendedProfile.objects.get_or_create(profile=profile)
        return user
