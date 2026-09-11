import pytest
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from usuarios.repositories import UsuarioRepository
from usuarios.services import UsuarioService


@pytest.mark.django_db
class TestUsuarioService:
    """Testes unitários para a camada UsuarioService."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = UsuarioService()
        self.repo = UsuarioRepository()

    def test_cadastrar_usuario_sucesso(self):
        dados = {
            'username': 'novo_usuario',
            'email': 'novo@example.com',
            'password': 'SenhaForte123!@#',
        }
        usuario = self.service.cadastrar_usuario(dados)
        assert usuario.id is not None
        assert usuario.username == 'novo_usuario'
        assert usuario.email == 'novo@example.com'
        assert usuario.check_password('SenhaForte123!@#')

    def test_cadastrar_usuario_com_campos_extras(self):
        dados = {
            'username': 'usuario_completo',
            'email': 'completo@example.com',
            'password': 'SenhaForte123!@#',
            'first_name': '  Maria  ',
            'last_name': '  Silva  ',
        }
        usuario = self.service.cadastrar_usuario(dados)
        assert usuario.first_name == 'Maria'
        assert usuario.last_name == 'Silva'

    def test_cadastrar_usuario_username_vazio(self):
        dados = {
            'username': '   ',
            'email': 'teste@example.com',
            'password': 'SenhaForte123!@#',
        }
        with pytest.raises(ValidationError) as exc_info:
            self.service.cadastrar_usuario(dados)
        assert 'username' in exc_info.value.detail

    def test_cadastrar_usuario_email_vazio(self):
        dados = {
            'username': 'usuario1',
            'email': '',
            'password': 'SenhaForte123!@#',
        }
        with pytest.raises(ValidationError) as exc_info:
            self.service.cadastrar_usuario(dados)
        assert 'email' in exc_info.value.detail

    def test_cadastrar_usuario_password_vazio(self):
        dados = {
            'username': 'usuario1',
            'email': 'teste@example.com',
            'password': '',
        }
        with pytest.raises(ValidationError) as exc_info:
            self.service.cadastrar_usuario(dados)
        assert 'password' in exc_info.value.detail

    def test_cadastrar_usuario_username_duplicado(self, usuario):
        dados = {
            'username': usuario.username,
            'email': 'outro_email@example.com',
            'password': 'SenhaForte123!@#',
        }
        with pytest.raises(ValidationError) as exc_info:
            self.service.cadastrar_usuario(dados)
        assert 'username' in exc_info.value.detail
        assert 'já está em uso' in str(exc_info.value.detail['username'])

    def test_cadastrar_usuario_email_duplicado(self, usuario):
        dados = {
            'username': 'outro_username',
            'email': usuario.email,
            'password': 'SenhaForte123!@#',
        }
        with pytest.raises(ValidationError) as exc_info:
            self.service.cadastrar_usuario(dados)
        assert 'email' in exc_info.value.detail
        assert 'já está cadastrado' in str(exc_info.value.detail['email'])

    def test_logout_sucesso(self, usuario):
        refresh = str(RefreshToken.for_user(usuario))
        # Não deve lançar exceção
        self.service.logout(refresh)

    def test_logout_refresh_token_vazio(self):
        with pytest.raises(ValidationError) as exc_info:
            self.service.logout('')
        assert 'refresh' in exc_info.value.detail

    def test_logout_token_invalido(self):
        with pytest.raises(ValidationError) as exc_info:
            self.service.logout('token_completamente_invalido')
        assert 'refresh' in exc_info.value.detail

    def test_logout_duplo_token_ja_na_blacklist(self, usuario):
        refresh = str(RefreshToken.for_user(usuario))
        self.service.logout(refresh)
        with pytest.raises(ValidationError) as exc_info:
            self.service.logout(refresh)
        assert 'refresh' in exc_info.value.detail

    def test_usuario_str(self, usuario):
        assert str(usuario) == usuario.username



@pytest.mark.django_db
class TestUsuarioRepository:
    """Testes para a camada UsuarioRepository."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.repo = UsuarioRepository()

    def test_obter_por_id_existente_e_inexistente(self, usuario):
        encontrado = self.repo.obter_por_id(usuario.id)
        assert encontrado == usuario

        nao_encontrado = self.repo.obter_por_id(999999)
        assert nao_encontrado is None

    def test_obter_por_username_existente_e_inexistente(self, usuario):
        encontrado = self.repo.obter_por_username(usuario.username)
        assert encontrado == usuario

        nao_encontrado = self.repo.obter_por_username('inexistente_123')
        assert nao_encontrado is None

    def test_obter_por_email_existente_e_inexistente(self, usuario):
        encontrado = self.repo.obter_por_email(usuario.email)
        assert encontrado == usuario

        nao_encontrado = self.repo.obter_por_email('naoexiste@example.com')
        assert nao_encontrado is None

    def test_existe_username(self, usuario):
        assert self.repo.existe_username(usuario.username) is True
        assert self.repo.existe_username('usuario_nao_existente') is False

    def test_existe_email(self, usuario):
        assert self.repo.existe_email(usuario.email) is True
        assert self.repo.existe_email('email_nao_existente@example.com') is False
