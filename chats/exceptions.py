from rest_framework.exceptions import APIException

class UserNotFound(APIException):
    status_code = 401
    default_detail = 'Usuáio não encontrado'
    default_code = 'user_not_found'
    
class ChatNotFound(APIException):
    status_code = 404
    default_detail = 'Chat não encontrado'
    default_code = 'chat_not_found'