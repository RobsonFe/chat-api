from email import message
from core.socket import socket
from core.exceptions import ValidationError

from chats.views.base import BaseView
from chats.models import (
    ChatMessage,
    Chat,
)
from chats.serializers import ChatMessageSerializer

from attachments.models import (
    AudioAttachment,
    FileAttachment,
)

from rest_framework.response import Response
from rest_framework import status

from django.utils.timezone import now
from django.core.files.storage import FileSystemStorage
from django.conf import settings

import uuid


class ChatMessagesView(BaseView):
    """
    View para gerenciar mensagens de chat.
    Herda de BaseView para reutilizar métodos comuns.
    Esta view permite listar mensagens de um chat específico e criar novas mensagens.

    """

    def get(self, request, chat_id):

        chat = self.chat_belongs_to_user(chat_id=chat_id, user_id=request.user.id)
        self.mark_messages_as_read(chat_id, request.user.id)

        socket.emit(
            "mark_messages_as_read",
            {"query": {"chat_id": chat_id, "exclude_user_id": request.user.id}},
        )

        messages = (
            ChatMessage.objects.filter(chat=chat_id, deleted_at__isnull=True)
            .order_by("created_at")
            .all()
        )

        serializer = ChatMessageSerializer(messages, many=True)

        socket.emit(
            "update_chat",
            {
                "query": {
                    "users": [chat.from_user, chat.to_user.id],
                }
            },
        )

        return Response(
            {
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, chat_id):
        """
        Cria uma nova mensagem de chat.
        A mensagem pode ser de texto, áudio ou arquivo.
        Se for um arquivo, ele deve ser enviado como multipart/form-data.
        O corpo da mensagem é obrigatório, mas o arquivo ou áudio são opcionais.
        Retorna a mensagem criada.
        """

        body = request.data.get("body")
        file = request.FILES.get("file")
        audio = request.FILES.get("audio")

        chat = self.chat_belongs_to_user(chat_id=chat_id, user_id=request.user.id)

        self.mark_messages_as_read(chat_id, request.user.id)

        if not body and not file and not audio:
            raise ValidationError("O corpo da mensagem não pode estar vazio.")

        attachment = None

        if file:
            storage = FileSystemStorage(
                settings.MEDIA_ROOT / "files", settings.MEDIA_URL + "files"
            )
            content_type = file.content_type
            name = file.name.split(".")[0]
            extension = file.name.split(".")[-1]
            size = file.size

            self.validate_file(size, extension, content_type)

            file = storage.save(f"{name}-{uuid.uuid4()}.{extension}", file)
            src = storage.url(file)

            attachment = FileAttachment.objects.create(
                name=name,
                extension=extension,
                size=size,
                src=src,
                content_type=content_type,
            )

        elif audio:
            storage = FileSystemStorage(
                settings.MEDIA_ROOT / "audios", settings.MEDIA_URL + "audios"
            )

            audio = storage.save(f"{name}-{uuid.uuid4()}.mp3", audio)
            src = storage.url(audio)

            attachment = AudioAttachment.objects.create(src=src)

        chat_message = ChatMessage.objects.create(
            chat_id=chat_id,
            from_user_id=request.user.id,
            body=body,
            attachment_code="FILE" if file else "AUDIO" if audio else None,
            attachment_id=attachment.id if attachment else None,
        )

        serializer = ChatMessageSerializer(
            chat_message, context={"user_id": request.user.id}
        ).data

        socket.emit(
            "update_chat_message",
            {
                "type": "create",
                "message": serializer,
                "query": {
                    "chat_id": chat_id,
                },
            },
        )

        Chat.objects.filter(id=chat_id).update(viewed_at=now())

        socket.emit(
            "update_chat",
            data={
                "query": {
                    "users": [chat.from_user, chat.to_user.id],
                }
            },
        )
        return Response(
            {
                "result": serializer,
            },
            status=status.HTTP_201_CREATED,
        )


class ChatMessageView(BaseView):
    """
    View para gerenciar uma mensagem de chat específica.
    Permite atualizar ou deletar uma mensagem de chat.
    Herda de BaseView para reutilizar métodos comuns.
    """

    def delete(self, request, chat_id, message_id):
        """
        Deleta uma mensagem de chat específica.
        Marca a mensagem como deletada, mas não a remove do banco de dados.
        Retorna a mensagem deletada.
        """
        chat = self.chat_belongs_to_user(chat_id=chat_id, user_id=request.user.id)

        deleted_message = ChatMessage.objects.filter(
            id=message_id,
            chat=chat_id,
            from_user=request.user.id,
            deleted_at__isnull=True,
        ).update(deleted_at=now())

        if not deleted_message:
            raise ValidationError("Mensagem não encontrada ou já deletada.")

        if deleted_message:
            socket.emit(
                "update_chat_message",
                {
                    "type": "delete",
                    "query": {
                        "chat_id": chat_id,
                        "message_id": message_id,
                    },
                },
            )

        socket.emit(
            "update_chat",
            {
                "query": {
                    "users": [chat.from_user, chat.to_user.id],
                }
            },
        )

        return Response(
            {"message": "Mensagem deletada com sucesso.", "sucess": True},
            status=status.HTTP_200_OK,
        )
