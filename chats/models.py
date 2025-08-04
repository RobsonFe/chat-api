from django.db import models
from accounts.models import User

class Chat(models.Model):
    from_user = models.ForeignKey(User, related_name='chats_from_user_id', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='chats_to_user_id', on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    class Meta:
      db_table = 'chats'
      
      
class ChatMessage(models.Model):

    body = models.TextField(null=True, blank=True)
    attachment_code = models.CharField(
      choices=[
        ("FILE", "FILE"),('AUDIO', 'AUDIO'),
        ],
      max_length=10, null=True, blank=True
    )
    attachment_id = models.IntegerField(null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    from_user = models.ForeignKey(User, related_name='messages_from_user_id', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['-created_at']