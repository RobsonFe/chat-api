from rest_framework.response import Response
from rest_framework import status

from django.db.models import Q
from django.utils.timezone import now

from chats.views.base import BaseView
from chats.models import Chat
from chats.serializers import ChatSerializer

from core.socket import socket


class ChatsView(BaseView):
    """
    View para gerenciar chats entre usuários.
    Herda de BaseView para reutilizar métodos comuns.
    """

    def get(self, request, *args, **kwargs):

        chats = (
            Chat.objects.filter(
                Q(from_user_id=request.user.id) | Q(to_user_id=request.user.id),
                deleted_at_isnull=True,
            )
            .order_by("-viewed_at")
            .all()
        )

        serializer = ChatSerializer(
            chats, context={"user_id": request.user.id}, many=True
        )

        return Response(
            {
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):

        email = request.data.get("email")

        user = self.get_user(email=email)

        chat = self.has_existing_chat(user_id=request.user.id, to_user=user.id)

        if not chat:
            chat = Chat.objects.create(
                from_user=request.user,
                to_user=user,
                viewed_at=now(),
            )

            serializer = ChatSerializer(chat, context={"user_id": request.user.id}).data

            socket.emit(
                "update_chat",
                {
                    "query": {
                        "users": [request.user.id, user.id],
                    }
                },
            )

        return Response(
            {
                "result": serializer,
            },
            status=status.HTTP_201_CREATED,
        )
