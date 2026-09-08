from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

Usuario = get_user_model()


class AutenticacaoIntegrationTestCase(APITestCase):
    """
    Testes de integração para o fluxo completo de autenticação e gerenciamento de usuários:
    - Cadastro
    - Login (JWT)
    - Renovação de Token (Refresh)
    - Encerramento de Sessão (Logout / Blacklist)
    - Consulta de Perfil (/me) com e sem token
    """

    def setUp(self):
        self.cadastro_url = reverse('usuario-cadastro')
        self.login_url = reverse('usuario-login')
        self.refresh_url = reverse('usuario-refresh')
        self.logout_url = reverse('usuario-logout')
        self.me_url = reverse('usuario-me')

        self.user_data = {
            'username': 'usuario_teste',
            'email': 'usuario@teste.com',
            'password': 'SenhaForte123!@#',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
        }

    def test_cadastro_usuario_sucesso(self):
        """Deve criar um novo usuário e retornar HTTP 201 com dados sem expor a senha."""
        response = self.client.post(self.cadastro_url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], self.user_data['username'])
        self.assertEqual(response.data['email'], self.user_data['email'])
        self.assertEqual(response.data['first_name'], self.user_data['first_name'])
        self.assertNotIn('password', response.data)
        self.assertIn('data_criacao', response.data)
        self.assertIn('data_atualizacao', response.data)

        # Valida que o usuário foi gravado no banco com senha criptografada
        usuario = Usuario.objects.get(username=self.user_data['username'])
        self.assertTrue(usuario.check_password(self.user_data['password']))

    def test_cadastro_usuario_username_duplicado(self):
        """Não deve permitir cadastro com nome de usuário já existente."""
        Usuario.objects.create_user(
            username=self.user_data['username'],
            email='outro@teste.com',
            password='outrasenha123'
        )
        response = self.client.post(self.cadastro_url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_cadastro_usuario_email_duplicado(self):
        """Não deve permitir cadastro com e-mail já existente."""
        Usuario.objects.create_user(
            username='outro_usuario',
            email=self.user_data['email'],
            password='outrasenha123'
        )
        response = self.client.post(self.cadastro_url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_login_sucesso(self):
        """Deve autenticar com sucesso e retornar tokens access e refresh."""
        Usuario.objects.create_user(**self.user_data)

        payload = {
            'username': self.user_data['username'],
            'password': self.user_data['password'],
        }
        response = self.client.post(self.login_url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_credenciais_invalidas(self):
        """Deve rejeitar autenticação com senha incorreta retornando HTTP 401."""
        Usuario.objects.create_user(**self.user_data)

        payload = {
            'username': self.user_data['username'],
            'password': 'SenhaErrada123',
        }
        response = self.client.post(self.login_url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_sucesso(self):
        """Deve renovar o access token utilizando um refresh token válido."""
        Usuario.objects.create_user(**self.user_data)

        login_res = self.client.post(self.login_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password'],
        })
        refresh_token = login_res.data['refresh']

        response = self.client.post(self.refresh_url, {'refresh': refresh_token})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_token_invalido(self):
        """Deve rejeitar renovação com token inválido retornando HTTP 401."""
        response = self.client.post(self.refresh_url, {'refresh': 'token_invalido_123'})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_sucesso_e_blacklist(self):
        """Deve invalidar o refresh token e adicioná-lo à blacklist."""
        Usuario.objects.create_user(**self.user_data)

        login_res = self.client.post(self.login_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password'],
        })
        access_token = login_res.data['access']
        refresh_token = login_res.data['refresh']

        # Efetua o logout com autenticação Bearer
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_res = self.client.post(self.logout_url, {'refresh': refresh_token})

        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

        # Tentar usar o mesmo refresh token deve falhar pois está na blacklist
        refresh_res = self.client.post(self.refresh_url, {'refresh': refresh_token})
        self.assertEqual(refresh_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_com_token_valido(self):
        """Deve retornar os dados do usuário logado ao fornecer Bearer token válido."""
        Usuario.objects.create_user(**self.user_data)

        login_res = self.client.post(self.login_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password'],
        })
        access_token = login_res.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user_data['username'])
        self.assertEqual(response.data['email'], self.user_data['email'])

    def test_me_sem_token(self):
        """Deve rejeitar acesso ao endpoint /me sem token retornando HTTP 401."""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_com_token_invalido(self):
        """Deve rejeitar acesso ao endpoint /me com token inválido retornando HTTP 401."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token_falso_invalido')
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
