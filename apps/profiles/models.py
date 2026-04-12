from django.conf import settings
from django.db import models

from apps.accounts.models import User


class ApplicantProfile(models.Model):
    class Education(models.TextChoices):
        NONE = "none", "بدون مؤهل"
        BELOW_AVG = "below_avg", "متوسط"
        ABOVE_AVG = "above_avg", "فوق المتوسط"
        UNIVERSITY = "university", "جامعي"
        POSTGRAD = "postgrad", "دراسات عليا"

    class MaritalStatus(models.TextChoices):
        SINGLE = "single", "أعزب/عزباء"
        ENGAGED = "engaged", "سبق عقد/كتب كتاب"
        DIVORCED = "divorced", "مطلق/مطلقة"
        WIDOWED = "widowed", "أرمل/أرملة"
        POLYGAMY = "polygamy", "متزوج يرغب في الزوجة الثانية"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applicant_profile",
    )
    full_name = models.CharField("الاسم الثلاثي", max_length=200)
    birth_date = models.DateField("تاريخ الميلاد")
    weight_kg = models.PositiveSmallIntegerField("الوزن (كجم)", null=True, blank=True)
    height_cm = models.PositiveSmallIntegerField("الطول (سم)", null=True, blank=True)
    education = models.CharField(
        "المؤهل",
        max_length=32,
        choices=Education.choices,
        default=Education.UNIVERSITY,
    )
    job_title = models.CharField("الوظيفة", max_length=300, blank=True)
    governorate = models.CharField("المحافظة", max_length=64)
    marital_status = models.CharField(
        max_length=32,
        choices=MaritalStatus.choices,
    )
    residence_summary = models.CharField(
        "محل الإقامة (بلد - محافظة - مدينة)",
        max_length=300,
    )
    about_me = models.TextField("نبذة عني والأهل", blank=True)
    partner_specs = models.TextField("مواصفات شريك الحياة المطلوبة", blank=True)
    quran_parts = models.PositiveSmallIntegerField(
        "أجزاء الحفظ",
        default=0,
    )
    preferred_partner_age_min = models.PositiveSmallIntegerField(default=18)
    preferred_partner_age_max = models.PositiveSmallIntegerField(default=50)
    whatsapp_phone = models.CharField("واتساب", max_length=32, blank=True)
    telegram_username = models.CharField("تليجرام", max_length=120, blank=True)
    facebook_url = models.CharField("فيسبوك", max_length=300, blank=True)
    applicant_gender = models.CharField(
        max_length=16,
        choices=User.ApplicantGender.choices,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ملف مقدّم الطلب"
        verbose_name_plural = "ملفات مقدّمي الطلبات"
        indexes = [
            models.Index(fields=["governorate", "marital_status"]),
            models.Index(fields=["applicant_gender"]),
        ]

    def __str__(self):
        return self.full_name

    @property
    def age(self):
        from datetime import date

        today = date.today()
        bd = self.birth_date
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))


class GroomExtendedProfile(models.Model):
    profile = models.OneToOneField(
        ApplicantProfile,
        on_delete=models.CASCADE,
        related_name="groom_extra",
    )
    expat = models.BooleanField("مغترب", default=False)
    take_abroad = models.BooleanField("نية السفر بالزوجة", default=False)
    smokes = models.BooleanField(default=False)
    polygamy_notes = models.TextField("تفاصيل التعدد", blank=True)

    class Meta:
        verbose_name = "بيانات إضافية (عريس)"


class BrideExtendedProfile(models.Model):
    profile = models.OneToOneField(
        ApplicantProfile,
        on_delete=models.CASCADE,
        related_name="bride_extra",
    )
    father_mother_work = models.CharField("عمل الوالدين", max_length=300, blank=True)
    siblings_summary = models.CharField("الأخوات والكليات", max_length=300, blank=True)
    parents_separated = models.BooleanField("انفصال الوالدين", default=False)
    hijab_type = models.CharField("نوع الحجاب", max_length=120, blank=True)

    class Meta:
        verbose_name = "بيانات إضافية (عروس)"


class ProfileMedia(models.Model):
    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "قيد المراجعة"
        APPROVED = "approved", "مقبول"
        REJECTED = "rejected", "مرفوض"

    profile = models.ForeignKey(
        ApplicantProfile,
        on_delete=models.CASCADE,
        related_name="media_items",
    )
    image = models.ImageField(upload_to="profiles/%Y/%m/")
    review_status = models.CharField(
        max_length=16,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مرفق ملف"
        verbose_name_plural = "مرفقات الملفات"
