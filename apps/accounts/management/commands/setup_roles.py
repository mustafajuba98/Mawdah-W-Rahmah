from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Creates platform_admin and moderator groups with sensible model permissions."

    def handle(self, *args, **options):
        mod_group, _ = Group.objects.get_or_create(name="moderator")
        admin_group, _ = Group.objects.get_or_create(name="platform_admin")

        user_ct = ContentType.objects.get_for_model(User)
        perms = Permission.objects.filter(content_type=user_ct)
        admin_group.permissions.set(perms)
        mod_group.permissions.set(
            perms.filter(codename__in=["change_user", "view_user"])
        )

        self.stdout.write(self.style.SUCCESS("Groups platform_admin and moderator are ready."))
