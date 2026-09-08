from datetime import date
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from tarefas.models import Tarefa

Usuario = get_user_model()


class TarefasIntegrationTestCase(APITestCase):
    """
    Testes de integração para o CRUD de tarefas com isolamento por usuário proprietário.
    """

    def setUp(self):
        self.user_a = Usuario.objects.create_user(
            username='user_a',
            email='user_a@teste.com',
            password='Password123!@#'
        )
        self.user_b = Usuario.objects.create_user(
            username='user_b',
            email='user_b@teste.com',
            password='Password123!@#'
        )

        self.token_a = str(RefreshToken.for_user(self.user_a).access_token)
        self.token_b = str(RefreshToken.for_user(self.user_b).access_token)

        self.list_create_url = reverse('tarefa-list-create')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_a}')

    def test_criar_tarefa_sucesso(self):
        """Deve criar uma nova tarefa vinculada ao usuário autenticado."""
        payload = {
            'titulo': 'Implementar Autenticação',
            'descricao': 'Configurar JWT com blacklist',
            'status_tarefa': 'pendente',
            'prioridade': 'alta',
            'data_vencimento': str(date.today()),
        }
        response = self.client.post(self.list_create_url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['titulo'], payload['titulo'])
        self.assertEqual(response.data['status_tarefa'], 'pendente')
        self.assertEqual(response.data['prioridade'], 'alta')
        self.assertIn('id', response.data)
        self.assertIn('data_criacao', response.data)
        self.assertIn('data_atualizacao', response.data)

        tarefa = Tarefa.objects.get(pk=response.data['id'])
        self.assertEqual(tarefa.usuario, self.user_a)

    def test_criar_tarefa_valores_default(self):
        """Deve criar tarefa com valores padrão de status (pendente) e prioridade (media)."""
        payload = {'titulo': 'Tarefa Básica'}
        response = self.client.post(self.list_create_url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status_tarefa'], 'pendente')
        self.assertEqual(response.data['prioridade'], 'media')
        self.assertIsNone(response.data['descricao'])
        self.assertIsNone(response.data['data_vencimento'])

    def test_criar_tarefa_titulo_obrigatorio(self):
        """Deve rejeitar a criação de tarefa sem título com HTTP 400."""
        response = self.client.post(self.list_create_url, {'descricao': 'Sem título'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('titulo', response.data)

    def test_listar_tarefas_apenas_proprias(self):
        """A listagem deve conter exclusivamente as tarefas pertencentes ao usuário autenticado."""
        Tarefa.objects.create(titulo='Tarefa A1', usuario=self.user_a)
        Tarefa.objects.create(titulo='Tarefa A2', usuario=self.user_a)
        Tarefa.objects.create(titulo='Tarefa B1', usuario=self.user_b)

        response = self.client.get(self.list_create_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        titulos = [item['titulo'] for item in response.data]
        self.assertIn('Tarefa A1', titulos)
        self.assertIn('Tarefa A2', titulos)
        self.assertNotIn('Tarefa B1', titulos)

    def test_detalhe_tarefa_propria(self):
        """Deve retornar os detalhes de uma tarefa do próprio usuário com HTTP 200."""
        tarefa = Tarefa.objects.create(titulo='Minha Tarefa', usuario=self.user_a)
        detail_url = reverse('tarefa-detail', kwargs={'pk': tarefa.id})

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], tarefa.id)
        self.assertEqual(response.data['titulo'], 'Minha Tarefa')

    def test_atualizar_tarefa_propria(self):
        """Deve permitir atualização parcial (PATCH) da tarefa do próprio usuário."""
        tarefa = Tarefa.objects.create(titulo='Tarefa Original', status_tarefa='pendente', usuario=self.user_a)
        detail_url = reverse('tarefa-detail', kwargs={'pk': tarefa.id})

        response = self.client.patch(detail_url, {'status_tarefa': 'concluida'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status_tarefa'], 'concluida')

        tarefa.refresh_from_db()
        self.assertEqual(tarefa.status_tarefa, 'concluida')

    def test_deletar_tarefa_propria(self):
        """Deve excluir tarefa pertencente ao próprio usuário com HTTP 204."""
        tarefa = Tarefa.objects.create(titulo='Para Deletar', usuario=self.user_a)
        detail_url = reverse('tarefa-detail', kwargs={'pk': tarefa.id})

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tarefa.objects.filter(pk=tarefa.id).exists())

    def test_detalhe_tarefa_outro_usuario_retorna_404(self):
        """Tentar acessar tarefa de outro usuário deve retornar 404 (não 403)."""
        tarefa_b = Tarefa.objects.create(titulo='Tarefa de B', usuario=self.user_b)
        detail_url = reverse('tarefa-detail', kwargs={'pk': tarefa_b.id})

        # Autenticado como user_a tentando acessar tarefa de user_b
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_atualizar_tarefa_outro_usuario_retorna_404(self):
        """Tentar atualizar tarefa de outro usuário deve retornar 404 (não 403)."""
        tarefa_b = Tarefa.objects.create(titulo='Tarefa de B', usuario=self.user_b)
        detail_url = reverse('tarefa-detail', kwargs={'pk': tarefa_b.id})

        response = self.client.patch(detail_url, {'titulo': 'Tentativa de alteração'})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        tarefa_b.refresh_from_db()
        self.assertEqual(tarefa_b.titulo, 'Tarefa de B')

    def test_deletar_tarefa_outro_usuario_retorna_404(self):
        """Tentar deletar tarefa de outro usuário deve retornar 404 (não 403)."""
        tarefa_b = Tarefa.objects.create(titulo='Tarefa de B', usuario=self.user_b)
        detail_url = reverse('tarefa-detail', kwargs={'pk': tarefa_b.id})

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Tarefa.objects.filter(pk=tarefa_b.id).exists())

    def test_endpoints_sem_autenticacao_retornam_401(self):
        """Requisições sem cabeçalho Authorization devem ser barradas com HTTP 401."""
        self.client.credentials()  # remove credentials

        tarefa = Tarefa.objects.create(titulo='Tarefa Pública?', usuario=self.user_a)
        detail_url = reverse('tarefa-detail', kwargs={'pk': tarefa.id})

        self.assertEqual(self.client.get(self.list_create_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.post(self.list_create_url, {'titulo': 'Nova'}).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.patch(detail_url, {'titulo': 'Alt'}).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_401_UNAUTHORIZED)
