import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .models import Conversation, Message


@login_required
def conversation_list(request):
    qs = Conversation.objects.filter(
        Q(user_a=request.user) | Q(user_b=request.user)
    ).select_related("user_a", "user_b", "introduction")
    return render(request, "messaging/list.html", {"conversations": qs})


@login_required
def conversation_room(request, pk):
    conv = get_object_or_404(Conversation, pk=pk)
    if not conv.involves(request.user):
        messages.error(request, "لا تملك صلاحية هذه المحادثة.")
        return redirect("conversation_list")
    msgs = list(conv.messages.filter(is_deleted=False).order_by("id"))
    last_message_id = msgs[-1].id if msgs else 0
    return render(
        request,
        "messaging/room.html",
        {
            "conversation": conv,
            "messages_list": msgs,
            "other_user": conv.other_user(request.user),
            "last_message_id": last_message_id,
        },
    )


@login_required
@require_POST
def post_message(request, pk):
    conv = get_object_or_404(Conversation, pk=pk)
    if not conv.involves(request.user):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
    body = (request.POST.get("body") or "").strip()
    if not body:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)
    m = Message.objects.create(conversation=conv, sender=request.user, body=body[:8000])
    return JsonResponse(
        {
            "ok": True,
            "message": {
                "id": m.id,
                "body": m.body,
                "sender_id": m.sender_id,
                "created_at": m.created_at.isoformat(),
            },
        }
    )


@login_required
@require_GET
def long_poll_messages(request, pk):
    """
    Long polling: يحتفظ بالطلب مفتوحاً حتى ~25 ثانية أو حتى وصول رسائل جديدة.
    لا WebSockets ولا FCM — مناسب لاستضافة بسيطة مع SQLite.
    """
    conv = get_object_or_404(Conversation, pk=pk)
    if not conv.involves(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)
    try:
        since_id = int(request.GET.get("since", 0))
    except ValueError:
        since_id = 0

    deadline = time.monotonic() + 25.0
    while time.monotonic() < deadline:
        qs = conv.messages.filter(id__gt=since_id, is_deleted=False).order_by("id")
        if qs.exists():
            return JsonResponse(
                {
                    "messages": [
                        {
                            "id": m.id,
                            "body": m.body,
                            "sender_id": m.sender_id,
                            "created_at": m.created_at.isoformat(),
                        }
                        for m in qs
                    ]
                }
            )
        time.sleep(0.4)
    return JsonResponse({"messages": []})
