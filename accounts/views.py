from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.core.files.storage import FileSystemStorage
from rest_framework.permissions import AllowAny, IsAuthenticated
from accounts.serializers import UserSerializer
from rest_framework.response import Response
from core.exceptions import ValidationError
from rest_framework.views import APIView
from accounts.auth import AuthenticationService
from django.utils.timezone import now
from rest_framework import status
from accounts.models import User
from django.conf import settings
import uuid
import os


class SignInView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        auth_service = AuthenticationService()
        signin = auth_service.signin(email, password)

        if not signin:
            raise AuthenticationFailed(
                "Credenciais inválidas.", code=status.HTTP_401_UNAUTHORIZED
            )

        user = UserSerializer(signin).data
        refresh = RefreshToken.for_user(signin)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class SignUpView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        name = request.data.get("name")
        email = request.data.get("email")
        password = request.data.get("password")

        if not name or not email or not password:
            raise ValidationError(
                "Todos os campos são obrigatórios.", code=status.HTTP_400_BAD_REQUEST
            )

        auth_service = AuthenticationService()
        singup = auth_service.signup(name, email, password)

        if not singup:
            raise AuthenticationFailed(
                "Erro ao registrar.", code=status.HTTP_400_BAD_REQUEST
            )

        user = UserSerializer(singup).data
        refresh = RefreshToken.for_user(singup)

        return Response(
            {
                "result": {
                    "user": user,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }
            },
            status=status.HTTP_200_OK,
        )


class SignOutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        refresh_token = request.data.get("refresh")
        user = request.user
        

        if not refresh_token:
            raise AuthenticationFailed(
                "Token de atualização não fornecido.", code=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            user.last_access = now()
            user.save()
            token.blacklist()
        except TokenError:
            raise AuthenticationFailed(
                "Erro ao invalidar o token.", code=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            status=status.HTTP_205_RESET_CONTENT
        )


class UserView(APIView):

    def get(self, request):
        user = request.user

        User.objects.filter(id=user.id).update(last_access=now())

        if not user:
            raise AuthenticationFailed(
                "Usuário não autenticado.", code=status.HTTP_401_UNAUTHORIZED
            )

        user_data = UserSerializer(user).data

        return Response({"result": user_data}, status=status.HTTP_200_OK)

    def patch(self, request):
        user = request.user

        if not user:
            raise AuthenticationFailed(
                "Usuário não autenticado.", code=status.HTTP_401_UNAUTHORIZED
            )

        name = request.data.get("name", user.name)
        email = request.data.get("email", user.email)
        password = request.data.get("password")
        avatar = request.FILES.get("avatar")

        user.name = name
        user.email = email
        
        if password:
            user.set_password(password)

        storage = FileSystemStorage(
            location=os.path.join(settings.MEDIA_ROOT, 'avatars'),
            base_url=f"{settings.MEDIA_URL}avatars/"
        )

        if avatar:
            content_type = avatar.content_type
            extension = avatar.name.split(".")[-1]
            if content_type not in ["image/jpeg", "image/png"]:
                raise ValidationError(
                    "Formato de imagem inválido. Use JPEG ou PNG.",
                    code=status.HTTP_400_BAD_REQUEST,
                )
            if extension not in ["jpg", "jpeg", "png"]:
                raise ValidationError(
                    "Extensão de imagem inválida. Use .jpg, .jpeg ou .png.",
                    code=status.HTTP_400_BAD_REQUEST,
                )
            
            # Remove avatar anterior se existir e não for o padrão
            if user.avatar and user.avatar != "/media/avatars/default.png":
                old_file_path = user.avatar.replace(settings.MEDIA_URL, "")
                if storage.exists(old_file_path):
                    storage.delete(old_file_path)
            
            filename = f"{uuid.uuid4()}.{extension}"
            file_path = storage.save(filename, avatar)
            user.avatar = storage.url(file_path)

        user.save()

        user_data = UserSerializer(user).data

        return Response({"result": user_data}, status=status.HTTP_200_OK)
