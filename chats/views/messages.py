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


class ChatMessageView(BaseView):
  
  def get(self, request, chat_id):
  
    chat = self.chat_belongs_to_user(
      chat_id=chat_id,
      user_id=request.user.id
    )
    self.mark_messages_as_read(chat_id, request.user.id)
    
    socket.emit(
      'mark_messages_as_read',
      {
        "query": {
        "chat_id": chat_id,
        "exclude_user_id": request.user.id
      }
      }
    )
    
    messages = ChatMessage.objects.filter(chat=chat_id, deleted_at__isnull=True).order_by('created_at').all()
    
    serializer = ChatMessageSerializer(messages, many=True)
    
    socket.emit(
      'update_chat',
      {
        "query": {
        "users": [chat.from_user, chat.to_user.id],
      }
      }
    )
    
    return Response(
      {
        "results": serializer.data,
      },
      status=status.HTTP_200_OK
    )