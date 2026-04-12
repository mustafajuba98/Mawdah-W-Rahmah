from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("يجب تعيين البريد الإلكتروني")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class ProfileStatus(models.TextChoices):
        REGISTERED = "registered", "مسجّل"
        PENDING_REVIEW = "pending_review", "قيد المراجعة"
        ACTIVE = "active", "مفعّل"
        REJECTED = "rejected", "مرفوض"
        SUSPENDED = "suspended", "موقوف"

    class ApplicantGender(models.TextChoices):
        MALE = "male", "ذكر (عريس)"
        FEMALE = "female", "أنثى (عروس)"

    username = None
    email = models.EmailField("البريد الإلكتروني", unique=True)
    profile_status = models.CharField(
        max_length=32,
        choices=ProfileStatus.choices,
        default=ProfileStatus.REGISTERED,
    )
    applicant_gender = models.CharField(
        max_length=16,
        choices=ApplicantGender.choices,
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
