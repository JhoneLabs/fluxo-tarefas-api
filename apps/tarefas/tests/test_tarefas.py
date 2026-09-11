from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from tarefas.models import Tarefa

Usuario = get_user_model()


class TarefasIntegrationTestCase(APITestCase):
    """
    Testes de integração para o CRUD de tarefas com isolamento por owner,
    além de filtros, ordenação e paginação no endpoint de listagem.
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
        self.assertEqual(response.data['count'], 2)
        titulos = [item['titulo'] for item in response.data['results']]
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
        self.client.credentials()

        tarefa = Tarefa.objects.create(titulo='Tarefa Pública?', usuario=self.user_a)
        detail_url = reverse('tarefa-detail', kwargs={'pk': tarefa.id})

        self.assertEqual(self.client.get(self.list_create_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.post(self.list_create_url, {'titulo': 'Nova'}).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.patch(detail_url, {'titulo': 'Alt'}).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_401_UNAUTHORIZED)

    # ==========================================
    # Novos testes: Filtros, Ordenação e Paginação
    # ==========================================

    def test_filtro_status_tarefa_isolado(self):
        """Deve filtrar tarefas estritamente pelo status_tarefa informado."""
        Tarefa.objects.create(titulo='T1', status_tarefa='pendente', usuario=self.user_a)
        Tarefa.objects.create(titulo='T2', status_tarefa='em_andamento', usuario=self.user_a)
        Tarefa.objects.create(titulo='T3', status_tarefa='concluida', usuario=self.user_a)

        res_pendente = self.client.get(self.list_create_url, {'status_tarefa': 'pendente'})
        self.assertEqual(res_pendente.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pendente.data['count'], 1)
        self.assertEqual(res_pendente.data['results'][0]['titulo'], 'T1')

        res_concluida = self.client.get(self.list_create_url, {'status_tarefa': 'concluida'})
        self.assertEqual(res_concluida.status_code, status.HTTP_200_OK)
        self.assertEqual(res_concluida.data['count'], 1)
        self.assertEqual(res_concluida.data['results'][0]['titulo'], 'T3')

    def test_filtro_prioridade_isolado(self):
        """Deve filtrar tarefas estritamente pela prioridade informada."""
        Tarefa.objects.create(titulo='T_Baixa', prioridade='baixa', usuario=self.user_a)
        Tarefa.objects.create(titulo='T_Media', prioridade='media', usuario=self.user_a)
        Tarefa.objects.create(titulo='T_Alta', prioridade='alta', usuario=self.user_a)

        response = self.client.get(self.list_create_url, {'prioridade': 'alta'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titulo'], 'T_Alta')

    def test_filtros_combinados(self):
        """Deve permitir combinar status_tarefa e prioridade via query params."""
        Tarefa.objects.create(titulo='Alvo', status_tarefa='pendente', prioridade='alta', usuario=self.user_a)
        Tarefa.objects.create(titulo='Outra 1', status_tarefa='pendente', prioridade='baixa', usuario=self.user_a)
        Tarefa.objects.create(titulo='Outra 2', status_tarefa='concluida', prioridade='alta', usuario=self.user_a)

        response = self.client.get(self.list_create_url, {
            'status_tarefa': 'pendente',
            'prioridade': 'alta'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titulo'], 'Alvo')

    def test_filtro_intervalo_data_vencimento(self):
        """Deve filtrar tarefas por data_vencimento_inicio (gte) e data_vencimento_fim (lte)."""
        hoje = date.today()
        ontem = hoje - timedelta(days=1)
        amanha = hoje + timedelta(days=1)
        depois_amanha = hoje + timedelta(days=2)

        Tarefa.objects.create(titulo='Ontem', data_vencimento=ontem, usuario=self.user_a)
        Tarefa.objects.create(titulo='Hoje', data_vencimento=hoje, usuario=self.user_a)
        Tarefa.objects.create(titulo='Amanha', data_vencimento=amanha, usuario=self.user_a)
        Tarefa.objects.create(titulo='Depois', data_vencimento=depois_amanha, usuario=self.user_a)

        # Filtro de hoje até amanhã
        response = self.client.get(self.list_create_url, {
            'data_vencimento_inicio': str(hoje),
            'data_vencimento_fim': str(amanha)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        titulos = [t['titulo'] for t in response.data['results']]
        self.assertIn('Hoje', titulos)
        self.assertIn('Amanha', titulos)

    def test_ordenacao(self):
        """Deve permitir ordenação ascendente e descendente via parâmetro ordering."""
        hoje = date.today()
        Tarefa.objects.create(titulo='T1', data_vencimento=hoje + timedelta(days=10), prioridade='alta', usuario=self.user_a)
        Tarefa.objects.create(titulo='T2', data_vencimento=hoje + timedelta(days=2), prioridade='baixa', usuario=self.user_a)
        Tarefa.objects.create(titulo='T3', data_vencimento=hoje + timedelta(days=5), prioridade='media', usuario=self.user_a)

        # Ordenação por data_vencimento ascendente
        res_asc = self.client.get(self.list_create_url, {'ordering': 'data_vencimento'})
        self.assertEqual(res_asc.status_code, status.HTTP_200_OK)
        titulos_asc = [t['titulo'] for t in res_asc.data['results']]
        self.assertEqual(titulos_asc, ['T2', 'T3', 'T1'])

        # Ordenação por data_vencimento descendente
        res_desc = self.client.get(self.list_create_url, {'ordering': '-data_vencimento'})
        self.assertEqual(res_desc.status_code, status.HTTP_200_OK)
        titulos_desc = [t['titulo'] for t in res_desc.data['results']]
        self.assertEqual(titulos_desc, ['T1', 'T3', 'T2'])

    def test_paginacao_estrutura_e_defaults(self):
        """Deve retornar a estrutura paginada (count, next, previous, results) com page_size padrão de 10."""
        for i in range(15):
            Tarefa.objects.create(titulo=f'Tarefa {i+1}', usuario=self.user_a)

        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])
        self.assertEqual(len(response.data['results']), 10)

        # Segunda página
        res_pag2 = self.client.get(response.data['next'])
        self.assertEqual(res_pag2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_pag2.data['results']), 5)
        self.assertIsNone(res_pag2.data['next'])
        self.assertIsNotNone(res_pag2.data['previous'])

    def test_paginacao_customizada_e_limite_maximo(self):
        """Deve respeitar o parâmetro page_size ajustado pelo cliente e o limite máximo de 50."""
        for i in range(25):
            Tarefa.objects.create(titulo=f'Tarefa {i+1}', usuario=self.user_a)

        # page_size=5 customizado
        res_5 = self.client.get(self.list_create_url, {'page_size': 5})
        self.assertEqual(res_5.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_5.data['results']), 5)

        # Tentativa de solicitar page_size excessivo (ex: 100) deve ser limitada ao max_page_size (50)
        res_100 = self.client.get(self.list_create_url, {'page_size': 100})
        self.assertEqual(res_100.status_code, status.HTTP_200_OK)
        # Como temos 25 tarefas criadas e o teto é 50, retorna as 25 em uma única página
        self.assertEqual(len(res_100.data['results']), 25)
        self.assertIsNone(res_100.data['next'])
