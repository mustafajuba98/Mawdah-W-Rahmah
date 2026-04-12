from django.conf import settings
from django.db import models


class IntroductionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "بانتظار الطرف الآخر"
        ACCEPTED = "accepted_by_recipient", "مقبول من الطرف الآخر"
        PENDING_MODERATOR = "pending_moderator", "بانتظار المشرف"
        APPROVED = "approved", "موافقة المشرف"
        REJECTED = "rejected", "رفض المشرف"

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="intro_requests_sent",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="intro_requests_received",
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    message = models.TextField("رسالة مختصرة", blank=True)
    moderator_notes = models.TextField("ملاحظات المشرف", blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="intro_decisions",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["requester", "recipient"],
                name="unique_intro_pair",
            ),
        ]
        verbose_name = "طلب تعارف / رؤية شرعية"
        verbose_name_plural = "طلبات التعارف"

    def __str__(self):
        return f"{self.requester_id} → {self.recipient_id} ({self.status})"
