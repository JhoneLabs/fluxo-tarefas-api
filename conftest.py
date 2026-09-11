import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from tests.factories import TarefaFactory, UsuarioFactory


@pytest.fixture
def api_client():
    """Retorna uma instância limpa de APIClient não autenticado."""
    return APIClient()


@pytest.fixture
def usuario_factory():
    """Retorna a classe de fábrica de usuários."""
    return UsuarioFactory


@pytest.fixture
def tarefa_factory():
    """Retorna a classe de fábrica de tarefas."""
    return TarefaFactory


@pytest.fixture
def usuario(db):
    """Cria e retorna um usuário padrão para testes."""
    return UsuarioFactory.create()


@pytest.fixture
def outro_usuario(db):
    """Cria e retorna um segundo usuário para testes de isolamento de dados."""
    return UsuarioFactory.create()


@pytest.fixture
def auth_client(api_client, usuario):
    """Retorna um APIClient autenticado com o token JWT Bearer do usuário principal."""
    token = str(RefreshToken.for_user(usuario).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client


@pytest.fixture
def outro_auth_client(outro_usuario):
    """Retorna um APIClient autenticado com o token JWT Bearer do outro usuário."""
    client = APIClient()
    token = str(RefreshToken.for_user(outro_usuario).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


@pytest.fixture
def tarefa(db, usuario):
    """Cria e retorna uma tarefa pertencente ao usuário principal."""
    return TarefaFactory.create(usuario=usuario)


@pytest.fixture
def outra_tarefa(db, outro_usuario):
    """Cria e retorna uma tarefa pertencente ao outro usuário."""
    return TarefaFactory.create(usuario=outro_usuario)
