from django.conf import settings
from django.db import models


class Conversation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "نشطة"
        CLOSED = "closed", "منتهية"
        REOPEN_PENDING = "reopen_pending", "بانتظار موافقة إعادة الفتح"

    introduction = models.OneToOneField(
        "matching.IntroductionRequest",
        on_delete=models.CASCADE,
        related_name="conversation",
    )
    user_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_a",
    )
    user_b = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_b",
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations_closed",
    )
    reopen_requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations_reopen_requested",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "محادثة"
        verbose_name_plural = "محادثات"

    def other_user(self, user):
        return self.user_b if user.pk == self.user_a_id else self.user_a

    def involves(self, user):
        return user.pk in (self.user_a_id, self.user_b_id)

    def can_send_messages(self) -> bool:
        return self.status == self.Status.ACTIVE


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    body = models.TextField()
    read_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("id",)
        indexes = [
            models.Index(fields=["conversation", "id"]),
        ]
