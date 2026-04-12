from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Message


@receiver(post_save, sender=Message)
def bump_conversation_on_message(sender, instance, **kwargs):
    from .models import Conversation

    Conversation.objects.filter(pk=instance.conversation_id).update(
        updated_at=timezone.now()
    )
