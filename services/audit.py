from apps.moderation.models import AuditLog


def log_action(actor, action, target_user=None, metadata=None):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_user=target_user,
        metadata=metadata or {},
    )
