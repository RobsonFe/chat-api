from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.storage import FileSystemStorage
from rest_framework.permissions import AllowAny
from accounts.serializers import UserSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.auth import Authentication
from django.utils.timezone import now
from rest_framework import status
from accounts.models import User
from django.conf import settings
from core.exceptions import ValidationError


class SignInView(APIView, Authentication):
  
    permission_classes = [AllowAny]
    authentication_classes = [Authentication]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        signin = self.signin(email, password)
        
        if not signin:
            raise AuthenticationFailed('Credenciais inválidas.')
          
        user = UserSerializer(signin).data
        refresh = RefreshToken.for_user(signin)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user,
        }, status=status.HTTP_200_OK)
