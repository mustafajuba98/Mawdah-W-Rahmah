from datetime import date

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.profiles.constants import EGYPT_GOVERNORATES
from apps.profiles.models import ApplicantProfile, BrideExtendedProfile, GroomExtendedProfile


class Command(BaseCommand):
    help = (
        "Creates demo member accounts (active + profiles) for browsing/tests. "
        "Does not create intro requests or messages."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of users (default 10).",
        )
        parser.add_argument(
            "--password",
            default="123123mM",
            help="Password for all seeded users (default 123123mM).",
        )
        parser.add_argument(
            "--email-domain",
            default="mawaddah.com",
            help="Emails: test{n}@<domain> (default mawaddah.com).",
        )

    def handle(self, *args, **options):
        count = max(1, min(options["count"], 50))
        password = options["password"]
        domain = options["email_domain"].strip().lstrip("@")

        Group.objects.get_or_create(name="moderator")
        Group.objects.get_or_create(name="platform_admin")

        gov_codes = [c for c, _ in EGYPT_GOVERNORATES]

        created = 0
        updated = 0
        for n in range(1, count + 1):
            email = f"test{n}@{domain}"
            gender = (
                User.ApplicantGender.MALE if n % 2 == 1 else User.ApplicantGender.FEMALE
            )
            birth = date(1992, 1, 1)
            birth = birth.replace(month=(n % 12) + 1, day=min(n, 28))
            gov = gov_codes[(n - 1) % len(gov_codes)]

            with transaction.atomic():
                user, was_created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "profile_status": User.ProfileStatus.ACTIVE,
                        "applicant_gender": gender,
                        "is_staff": False,
                        "is_superuser": False,
                    },
                )
                user.set_password(password)
                user.profile_status = User.ProfileStatus.ACTIVE
                user.applicant_gender = gender
                user.is_staff = False
                user.is_superuser = False
                user.is_active = True
                user.email_verified_at = timezone.now()
                user.save()

                profile, _p_created = ApplicantProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        "full_name": f"مستخدم تجريبي {n}",
                        "birth_date": birth,
                        "weight_kg": 70 + (n % 15),
                        "height_cm": 160 + (n % 25),
                        "education": ApplicantProfile.Education.UNIVERSITY,
                        "job_title": "تجريبي",
                        "governorate": gov,
                        "marital_status": ApplicantProfile.MaritalStatus.SINGLE,
                        "residence_summary": f"{gov} — تجريبي",
                        "about_me": "بيانات وهمية للاختبار.",
                        "partner_specs": "للاختبار فقط.",
                        "quran_parts": n % 6,
                        "preferred_partner_age_min": 22,
                        "preferred_partner_age_max": 45,
                        "applicant_gender": gender,
                    },
                )
                if gender == User.ApplicantGender.MALE:
                    GroomExtendedProfile.objects.get_or_create(profile=profile)
                else:
                    BrideExtendedProfile.objects.get_or_create(profile=profile)

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {created} new users, {updated} existing users reset "
                f"(password + active profile). Emails: test1..test{count}@{domain}"
            )
        )
        self.stdout.write(f"Shared password: {password}")
