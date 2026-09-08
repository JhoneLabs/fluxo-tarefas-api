from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from usuarios.serializers import (
    LogoutSerializer,
    UsuarioCadastroSerializer,
    UsuarioResponseSerializer,
)
from usuarios.services import UsuarioService


class CadastroView(APIView):
    """
    Endpoint para cadastro de novos usuários.
    POST /api/usuarios/cadastro/
    """
    permission_classes = [AllowAny]

    def __init__(self, service: UsuarioService = None, **kwargs):
        super().__init__(**kwargs)
        self.service = service or UsuarioService()

    def post(self, request):
        serializer = UsuarioCadastroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = self.service.cadastrar_usuario(serializer.validated_data)
        response_serializer = UsuarioResponseSerializer(usuario)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """
    Endpoint para autenticação de usuários via JWT.
    POST /api/usuarios/login/
    Retorna access e refresh tokens.
    """
    permission_classes = [AllowAny]


class RefreshTokenView(TokenRefreshView):
    """
    Endpoint para renovação do access token expirado.
    POST /api/usuarios/refresh/
    Retorna novo access token.
    """
    permission_classes = [AllowAny]


class LogoutView(APIView):
    """
    Endpoint para encerramento de sessão do usuário.
    POST /api/usuarios/logout/
    Invalida o refresh token adicionando-o à blacklist.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self, service: UsuarioService = None, **kwargs):
        super().__init__(**kwargs)
        self.service = service or UsuarioService()

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.service.logout(serializer.validated_data['refresh'])
        return Response(
            {'detail': 'Logout realizado com sucesso. Token invalidado.'},
            status=status.HTTP_200_OK
        )


class UsuarioMeView(APIView):
    """
    Endpoint para obtenção do perfil do usuário autenticado.
    GET /api/usuarios/me/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UsuarioResponseSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
