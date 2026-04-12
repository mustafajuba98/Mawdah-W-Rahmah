"""Shared JSON helpers for chat API responses."""


def conversation_state_dict(conv) -> dict:
    return {
        "status": conv.status,
        "closed_by_id": conv.closed_by_id,
        "reopen_requested_by_id": conv.reopen_requested_by_id,
    }


def conversation_signature(conv) -> str:
    return f"{conv.status}:{conv.reopen_requested_by_id}:{conv.closed_by_id}"
