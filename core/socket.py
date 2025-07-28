import socketio 
from django.conf import settings

socket = socketio.Server(async_mode='eventlet', cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS)