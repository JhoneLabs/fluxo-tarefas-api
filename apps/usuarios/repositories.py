from typing import Optional

from django.contrib.auth import get_user_model

Usuario = get_user_model()


class UsuarioRepository:
    """
    Camada de repositório responsável pelo acesso e persistência de dados de usuários.
    Isola consultas ao ORM do Django das regras de negócio.
    """

    @staticmethod
    def criar(username: str, email: str, password: str, **extra_fields) -> Usuario:
        """Cria e persiste um novo usuário utilizando o helper seguro create_user."""
        return Usuario.objects.create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields
        )

    @staticmethod
    def obter_por_id(user_id: int) -> Optional[Usuario]:
        """Recupera um usuário pelo seu ID primário."""
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None

    @staticmethod
    def obter_por_username(username: str) -> Optional[Usuario]:
        """Recupera um usuário pelo nome de usuário."""
        try:
            return Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            return None

    @staticmethod
    def obter_por_email(email: str) -> Optional[Usuario]:
        """Recupera um usuário pelo e-mail."""
        try:
            return Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return None

    @staticmethod
    def existe_username(username: str) -> bool:
        """Verifica se já existe um usuário com o username fornecido."""
        return Usuario.objects.filter(username=username).exists()

    @staticmethod
    def existe_email(email: str) -> bool:
        """Verifica se já existe um usuário com o e-mail fornecido."""
        return Usuario.objects.filter(email=email).exists()
