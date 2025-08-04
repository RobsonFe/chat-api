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
    View para gerenciar a lista de chats do usuário.
    Herda de BaseView para reutilizar métodos comuns.
    Esta view permite listar chats existentes e criar novos chats com base no email do usuário.
    - GET: Retorna a lista de chats do usuário autenticado.
    - POST: Cria um novo chat com o usuário especificado pelo email.
    Requer que o usuário esteja autenticado.
    O método GET retorna todos os chats onde o usuário é o remetente ou destinatário,
    ordenados pela data de visualização mais recente. O método POST cria um novo chat
    se não existir um chat prévio com o usuário especificado pelo email.
    Se um chat já existir, ele não será duplicado, e o chat existente será retornado.
    A criação de um novo chat também emite um evento via socket para atualizar a interface do usuário.
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

class ChatView(BaseView):
    """
    View para gerenciar um chat específico.
    Herda de BaseView para reutilizar métodos comuns.
    Esta view permite excluir um chat específico pelo ID.
    - DELETE: Exclui o chat especificado pelo ID.
    Requer que o usuário esteja autenticado.
    O método DELETE marca o chat como excluído, atualizando o campo `deleted_at` com a data e hora atual.
    Após a exclusão, um evento é emitido via socket para atualizar a interface do usuário,
    informando que o chat foi excluído.
    """
    
    def delete(self, request, chat_id):
        
        chat = self.chat_belongs_to_user(
            user_id=request.user.id,
            chat_id=chat_id
        )
        
        deleted = Chat.objects.filter(id=chat.id, deleted_at_isnull=True).update(
            deleted_at=now()
        )
        
        if deleted:
            socket.emit(
                "update_chat",
                {
                    "type": "delete",
                    "query": {
                        "chat_id": chat.id,
                        "users": [chat.from_user.id, chat.to_user.id],
                    }
                },
            )
        return Response(
            {
                "message": "Chat deletado com sucesso.",
                "deleted": True,
            },
            status=status.HTTP_204_NO_CONTENT,
        )