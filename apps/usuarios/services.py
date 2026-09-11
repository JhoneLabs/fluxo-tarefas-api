from typing import Any, Dict

from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from usuarios.repositories import UsuarioRepository


class UsuarioService:
    """
    Camada de serviço contendo as regras de negócio para gerenciamento de usuários e sessão.
    """

    def __init__(self, repository: UsuarioRepository = None):
        self.repository = repository or UsuarioRepository()

    def cadastrar_usuario(self, dados: Dict[str, Any]):
        """
        Executa as validações de negócio e persiste o novo usuário.
        """
        username = dados.get('username', '').strip()
        email = dados.get('email', '').strip().lower()
        password = dados.get('password')

        if not username:
            raise ValidationError({'username': 'O nome de usuário é obrigatório.'})

        if not email:
            raise ValidationError({'email': 'O e-mail é obrigatório.'})

        if not password:
            raise ValidationError({'password': 'A senha é obrigatória.'})

        if self.repository.existe_username(username):
            raise ValidationError({'username': 'Este nome de usuário já está em uso.'})

        if self.repository.existe_email(email):
            raise ValidationError({'email': 'Este e-mail já está cadastrado.'})

        extra_fields = {}
        if 'first_name' in dados:
            extra_fields['first_name'] = dados['first_name'].strip()
        if 'last_name' in dados:
            extra_fields['last_name'] = dados['last_name'].strip()

        return self.repository.criar(
            username=username,
            email=email,
            password=password,
            **extra_fields
        )

    def logout(self, refresh_token_str: str) -> None:
        """
        Invalida o refresh token inserindo-o na blacklist do SimpleJWT.
        """
        if not refresh_token_str:
            raise ValidationError({'refresh': 'O refresh token é obrigatório.'})

        try:
            token = RefreshToken(refresh_token_str)
            token.blacklist()
        except TokenError as exc:
            raise ValidationError({'refresh': f'Token inválido ou expirado: {str(exc)}'})
