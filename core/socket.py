import socketio
from django.conf import settings
from django.utils.timezone import now

from chats.models import Chat, ChatMessage

socket = socketio.Server(
    async_mode="eventlet", cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS
)


@socket.event
def update_messages_as_read(sid, data):
    chat_id = data.get("chat_id")

    chat = Chat.objects.values("from_user_id", "to_user_id").filter(id=chat_id).first()

    ChatMessage.objects.filter(
        chat_id=chat_id,
        viewed_at__isnull=True,
    ).update(
        viewed_at=now(),
    )

    socket.emit(
        "update_chat",
        {
            "query": {
                "users": [chat["from_user_id"], chat["to_user_id"]],
            }
        },
    )

    socket.emit(
        "mark_messages_as_read",
        {
            "query": {
                "chat_id": chat_id,
                "exclude_user_id": data.get("exclude_user_id", None),
            }
        },
    )
