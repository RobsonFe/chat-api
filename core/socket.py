import socketio 
from django.conf import settings

socket = socketio.Server(async_mode='threading', cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS)