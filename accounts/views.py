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
                }
            },
            status=status.HTTP_200_OK,
        )


class SignOutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        refresh_token = request.data.get("refresh")
        

        if not refresh_token:
            raise AuthenticationFailed(
                "Token de atualização não fornecido.", code=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
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

        name = request.data.get("name")
        email = request.data.get("email")
        password = request.data.get("password")
        avatar = request.FILES.get("avatar")

        if not name or not email or not password:
            raise ValidationError(
                "Todos os campos são obrigatórios.", code=status.HTTP_400_BAD_REQUEST
            )

        user.name = name
        user.email = email
        user.set_password(password)

        storage = FileSystemStorage(
            settings.MEDIA_ROOT / "avatars", settings.MEDIA_URL / "avatars"
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
            filename = f"{uuid.uuid4()}.{extension}"
            file_path = storage.save(filename, avatar)
            url = storage.url(file_path)
            user.avatar = url

        user.save()

        serializer = UserSerializer(request.user, data=request.data, partial=True)

        if not serializer.is_valid():

            if avatar:
                storage.delete(file_path)

            raise ValidationError(serializer.errors, code=status.HTTP_400_BAD_REQUEST)

        if avatar and request.user.avatar != "/media/avatars/default.png":
            storage.delete(request.user.avatar.split("/")[-1])

        if password:
            request.user.set_password(password)
            request.user.save(update_fields=["password"])

        serializer.save()

        return Response({"result": serializer.data}, status=status.HTTP_200_OK)
