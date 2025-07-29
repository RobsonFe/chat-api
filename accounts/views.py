from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.storage import FileSystemStorage
from rest_framework.permissions import AllowAny
from accounts.serializers import UserSerializer
from rest_framework.response import Response
from core.exceptions import ValidationError
from rest_framework.views import APIView
from accounts.auth import Authentication
from django.utils.timezone import now
from rest_framework import status
from accounts.models import User
from django.conf import settings


class SignInView(APIView, Authentication):
  
    permission_classes = [AllowAny]
    authentication_classes = [Authentication]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        signin = self.signin(email, password)
        
        if not signin:
            raise AuthenticationFailed('Credenciais inválidas.', code=status.HTTP_401_UNAUTHORIZED)
          
        user = UserSerializer(signin).data
        refresh = RefreshToken.for_user(signin)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user,
        }, status=status.HTTP_200_OK)
        
class SignUpView(APIView, Authentication):
  
    permission_classes = [AllowAny]
    authentication_classes = [Authentication]

    def post(self, request):

        name = request.data.get('name')
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not name or not email or not password:
            raise ValidationError('Todos os campos são obrigatórios.', code=status.HTTP_400_BAD_REQUEST)
        
        singup = self.signup(name, email, password)
        
        if not singup:
            raise AuthenticationFailed('Erro ao registrar.', code= status.HTTP_400_BAD_REQUEST)
          
        user = UserSerializer(singup).data
        refresh = RefreshToken.for_user(singup)
        
        return Response({
            'user': user,
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
