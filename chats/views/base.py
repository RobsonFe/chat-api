from rest_framework.views import APIView
from rest_framework.response import Response

from django.db.models import Q
from django.utils.timezone import now

from accounts.models import User

from chats.models import Chat, ChatMessage
from chats.serializers import ChatSerializer, ChatMessageSerializer
from chats.exceptions import ChatNotFound,UserNotFound


class BaseView(APIView):
  
  def get_user(self, raise_exception=True, **kwargs) -> User | None:
    """
    Busca um usuário conforme os parâmetros fornecidos.
    Se o usuário não for encontrado e raise_exception for True, lança uma exceção UserNotFound.
    """
    user = User.objects.filter(**kwargs).first()
    
    if not user and raise_exception:
      raise UserNotFound
    
    return user
  
  def has_existing_chat(self, user_id,to_user) -> Chat | None:
    
    """
    Verifica se já existe um chat entre dois usuários.
    Retorna o chat se existir, caso contrário retorna None.
    Se o chat existir, ele não deve estar marcado como deletado (deleted_at é None).
    """
    
    chat = Chat.objects.filter(
      (Q(from_user=user_id) & Q(to_user=to_user)) |
      (Q(from_user=to_user) & Q(to_user=user_id)),
      deleted_at__isnull=True
    ).first()
    
    if chat:
      return ChatSerializer(chat, context={'user_id': user_id}).data
    
  
  def chat_belongs_to_user(self, chat_id, user_id) -> Chat | None:
    
    """
    Verifica se um chat pertence a um usuário específico.
    Retorna o chat se pertencer ao usuário, caso contrário lança uma exceção ChatNotFound.
    O chat deve estar ativo (deleted_at é None).
    """
    
    chat = Chat.objects.filter(
      Q(from_user=user_id) | Q(to_user=user_id),
      id=chat_id,
      deleted_at__isnull=True
    ).first()
    
    if not chat:
      raise ChatNotFound
    
    return chat
  
  
  def mark_messages_as_read(self, chat_id, user_id) -> None:
    
    ChatMessage.objects.filter(
      chat_id=chat_id,
      viewed_at__isnull=True,
      deleted_at_isnull=True,
    ).exclude(
      from_user=user_id
    ).update(
      viewed_at=now()
    )