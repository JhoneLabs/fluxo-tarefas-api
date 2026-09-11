import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
class TestUsuariosViewsEdgeCases:
    """Testes de integração para cenários de borda nos endpoints de autenticação e usuários."""

    @pytest.fixture(autouse=True)
    def setup_urls(self):
        self.cadastro_url = reverse('usuario-cadastro')
        self.login_url = reverse('usuario-login')
        self.refresh_url = reverse('usuario-refresh')
        self.logout_url = reverse('usuario-logout')
        self.me_url = reverse('usuario-me')

    def test_cadastro_senha_fraca_rejeitada(self, api_client):
        """Deve rejeitar senhas muito fracas/curtas via validação de senhas do Django."""
        payload = {
            'username': 'usuario_fraco',
            'email': 'fraco@example.com',
            'password': '123',
        }
        response = api_client.post(self.cadastro_url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_cadastro_campos_obrigatorios_ausentes(self, api_client):
        """Deve retornar 400 quando campos obrigatórios estiverem ausentes."""
        response = api_client.post(self.cadastro_url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data
        assert 'email' in response.data
        assert 'password' in response.data

    def test_cadastro_email_formato_invalido(self, api_client):
        """Deve retornar 400 quando o email for inválido."""
        payload = {
            'username': 'usuario_email_invalido',
            'email': 'formato-invalido',
            'password': 'SenhaForte123!@#',
        }
        response = api_client.post(self.cadastro_url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_login_usuario_inexistente(self, api_client):
        """Deve retornar 401 para usuário não cadastrado."""
        payload = {
            'username': 'usuario_que_nao_existe',
            'password': 'QualquerSenha123!@#',
        }
        response = api_client.post(self.login_url, payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_sem_credenciais(self, api_client):
        """Deve retornar 400 se o payload de login for vazio."""
        response = api_client.post(self.login_url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_refresh_token_invalido_retorna_401(self, api_client):
        """Deve retornar 401 para token refresh inválido ou malformado."""
        response = api_client.post(self.refresh_url, {'refresh': 'token_falso_invalido'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_ausente_retorna_400(self, api_client):
        """Deve retornar 400 se o campo refresh não for enviado."""
        response = api_client.post(self.refresh_url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_duplo_retorna_400(self, auth_client, usuario):
        """Após logout bem-sucedido, o mesmo refresh token deve ser rejeitado no segundo logout."""
        refresh = str(RefreshToken.for_user(usuario))

        # Primeiro logout - sucesso
        res1 = auth_client.post(self.logout_url, {'refresh': refresh})
        assert res1.status_code == status.HTTP_200_OK

        # Segundo logout com mesmo token - token já na blacklist
        res2 = auth_client.post(self.logout_url, {'refresh': refresh})
        assert res2.status_code == status.HTTP_400_BAD_REQUEST
        assert 'refresh' in res2.data

    def test_logout_sem_corpo_retorna_400(self, auth_client):
        """Logout sem fornecer o refresh token deve retornar 400."""
        response = auth_client.post(self.logout_url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_sem_autenticacao_retorna_401(self, api_client, usuario):
        """Tentativa de logout sem token Bearer de autenticação deve retornar 401."""
        refresh = str(RefreshToken.for_user(usuario))
        response = api_client.post(self.logout_url, {'refresh': refresh})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_sem_token_retorna_401(self, api_client):
        """Acesso ao endpoint /me sem header de autorização deve retornar 401."""
        response = api_client.get(self.me_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_token_malformado_retorna_401(self, api_client):
        """Acesso com Bearer inválido deve retornar 401."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer token_invalido_xyz')
        response = api_client.get(self.me_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_autenticado_retorna_dados(self, auth_client, usuario):
        """Acesso com Bearer válido retorna os dados cadastrais do usuário."""
        response = auth_client.get(self.me_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == usuario.username
        assert response.data['email'] == usuario.email
