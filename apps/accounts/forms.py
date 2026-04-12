from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class SignUpForm(UserCreationForm):
    applicant_gender = forms.ChoiceField(
        label="نوع مقدّم الطلب",
        choices=User.ApplicantGender.choices,
        required=True,
    )

    class Meta:
        model = User
        fields = ("email", "applicant_gender", "password1", "password2")


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label="البريد الإلكتروني")
