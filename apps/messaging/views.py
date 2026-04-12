import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import Conversation, Message
from .utils import conversation_signature, conversation_state_dict


def _messages_payload(qs):
    return [
        {
            "id": m.id,
            "body": m.body,
            "sender_id": m.sender_id,
            "created_at": m.created_at.isoformat(),
        }
        for m in qs
    ]


@login_required
def conversation_list(request):
    qs = (
        Conversation.objects.filter(Q(user_a=request.user) | Q(user_b=request.user))
        .select_related(
            "user_a",
            "user_b",
            "introduction",
            "user_a__applicant_profile",
            "user_b__applicant_profile",
        )
        .order_by("-updated_at")
    )
    return render(request, "messaging/list.html", {"conversations": qs})


@login_required
def conversation_room(request, pk):
    conv = get_object_or_404(
        Conversation.objects.select_related(
            "user_a",
            "user_b",
            "user_a__applicant_profile",
            "user_b__applicant_profile",
            "closed_by",
            "reopen_requested_by",
        ),
        pk=pk,
    )
    if not conv.involves(request.user):
        messages.error(request, "لا تملك صلاحية هذه المحادثة.")
        return redirect("conversation_list")
    msgs = list(conv.messages.filter(is_deleted=False).order_by("id"))
    last_message_id = msgs[-1].id if msgs else 0
    other = conv.other_user(request.user)
    return render(
        request,
        "messaging/room.html",
        {
            "conversation": conv,
            "messages_list": msgs,
            "other_user": other,
            "last_message_id": last_message_id,
        },
    )


@login_required
@require_POST
def post_message(request, pk):
    conv = get_object_or_404(Conversation, pk=pk)
    if not conv.involves(request.user):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
    if not conv.can_send_messages():
        return JsonResponse(
            {
                "ok": False,
                "error": "conversation_not_active",
                "conversation": conversation_state_dict(conv),
            },
            status=403,
        )
    body = (request.POST.get("body") or "").strip()
    if not body:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)
    m = Message.objects.create(conversation=conv, sender=request.user, body=body[:8000])
    conv.refresh_from_db()
    return JsonResponse(
        {
            "ok": True,
            "message": {
                "id": m.id,
                "body": m.body,
                "sender_id": m.sender_id,
                "created_at": m.created_at.isoformat(),
            },
            "conversation": conversation_state_dict(conv),
        }
    )


@login_required
@require_GET
def long_poll_messages(request, pk):
    conv = get_object_or_404(Conversation, pk=pk)
    if not conv.involves(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)
    try:
        since_id = int(request.GET.get("since", 0))
    except ValueError:
        since_id = 0

    conv.refresh_from_db()
    start_sig = conversation_signature(conv)
    deadline = time.monotonic() + 25.0
    while time.monotonic() < deadline:
        conv.refresh_from_db()
        new_msgs = list(
            conv.messages.filter(id__gt=since_id, is_deleted=False).order_by("id")
        )
        if new_msgs or conversation_signature(conv) != start_sig:
            return JsonResponse(
                {
                    "messages": _messages_payload(new_msgs),
                    "conversation": conversation_state_dict(conv),
                }
            )
        time.sleep(0.4)
    conv.refresh_from_db()
    return JsonResponse(
        {
            "messages": [],
            "conversation": conversation_state_dict(conv),
        }
    )


@login_required
@require_POST
def conversation_close(request, pk):
    conv = get_object_or_404(Conversation, pk=pk)
    if not conv.involves(request.user):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
    if conv.status != Conversation.Status.ACTIVE:
        return JsonResponse(
            {"ok": False, "error": "not_active", "conversation": conversation_state_dict(conv)},
            status=400,
        )
    now = timezone.now()
    conv.status = Conversation.Status.CLOSED
    conv.closed_by = request.user
    conv.closed_at = now
    conv.reopen_requested_by = None
    conv.save(update_fields=["status", "closed_by", "closed_at", "reopen_requested_by", "updated_at"])
    return JsonResponse({"ok": True, "conversation": conversation_state_dict(conv)})


@login_required
@require_POST
def conversation_request_reopen(request, pk):
    conv = get_object_or_404(Conversation, pk=pk)
    if not conv.involves(request.user):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
    if conv.status != Conversation.Status.CLOSED:
        return JsonResponse(
            {"ok": False, "error": "not_closed", "conversation": conversation_state_dict(conv)},
            status=400,
        )
    conv.status = Conversation.Status.REOPEN_PENDING
    conv.reopen_requested_by = request.user
    conv.save(update_fields=["status", "reopen_requested_by", "updated_at"])
    return JsonResponse({"ok": True, "conversation": conversation_state_dict(conv)})


@login_required
@require_POST
def conversation_respond_reopen(request, pk):
    conv = get_object_or_404(Conversation, pk=pk)
    if not conv.involves(request.user):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
    if conv.status != Conversation.Status.REOPEN_PENDING or not conv.reopen_requested_by_id:
        return JsonResponse(
            {"ok": False, "error": "no_pending_reopen", "conversation": conversation_state_dict(conv)},
            status=400,
        )
    if conv.reopen_requested_by_id == request.user.id:
        return JsonResponse({"ok": False, "error": "cannot_respond_own"}, status=400)
    accept = request.POST.get("accept") == "1"
    if accept:
        conv.status = Conversation.Status.ACTIVE
        conv.reopen_requested_by = None
        conv.closed_by = None
        conv.closed_at = None
        conv.save(
            update_fields=[
                "status",
                "reopen_requested_by",
                "closed_by",
                "closed_at",
                "updated_at",
            ]
        )
    else:
        conv.status = Conversation.Status.CLOSED
        conv.reopen_requested_by = None
        conv.save(update_fields=["status", "reopen_requested_by", "updated_at"])
    return JsonResponse({"ok": True, "conversation": conversation_state_dict(conv)})
