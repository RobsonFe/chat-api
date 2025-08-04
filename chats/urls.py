from django.urls import path
from chats.views.chats import (
  ChatsView,
  ChatView,
)

urlpatterns = [
  path('', ChatsView.as_view(), name='chats'),
  path('<int:chat_id>/', ChatView.as_view(), name='chat'),
]