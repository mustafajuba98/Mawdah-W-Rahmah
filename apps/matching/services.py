from django.utils import timezone

from apps.messaging.models import Conversation
from services.audit import log_action

from .models import IntroductionRequest


def ensure_conversation_for_intro(intro: IntroductionRequest):
    if intro.status != IntroductionRequest.Status.APPROVED:
        return None
    conv, _created = Conversation.objects.get_or_create(
        introduction=intro,
        defaults={
            "user_a": intro.requester,
            "user_b": intro.recipient,
        },
    )
    return conv


def apply_moderator_decision(intro, moderator, approve: bool, notes: str = ""):
    intro.moderator_notes = notes
    intro.decided_by = moderator
    intro.decided_at = timezone.now()
    if approve:
        intro.status = IntroductionRequest.Status.APPROVED
        intro.save()
        ensure_conversation_for_intro(intro)
        log_action(
            moderator,
            "intro_approved",
            target_user=intro.requester,
            metadata={"intro_id": intro.pk, "recipient_id": intro.recipient_id},
        )
    else:
        intro.status = IntroductionRequest.Status.REJECTED
        intro.save()
        log_action(
            moderator,
            "intro_rejected",
            target_user=intro.requester,
            metadata={"intro_id": intro.pk},
        )
    return intro
