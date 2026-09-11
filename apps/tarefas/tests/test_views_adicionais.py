from datetime import date, timedelta

import pytest
from django.urls import reverse
from rest_framework import status

from tarefas.models import PrioridadeTarefa, StatusTarefa


@pytest.mark.django_db
class TestTarefasViewsAdicionais:
    """Testes de integração complementares para views de tarefas."""

    @pytest.fixture(autouse=True)
    def setup_urls(self):
        self.list_create_url = reverse('tarefa-list-create')

    def detail_url(self, pk):
        return reverse('tarefa-detail', kwargs={'pk': pk})

    # --- Autenticação (401 Unauthorized) ---

    def test_list_tarefas_sem_token_retorna_401(self, api_client):
        response = api_client.get(self.list_create_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_tarefa_sem_token_retorna_401(self, api_client):
        response = api_client.post(self.list_create_url, {'titulo': 'Sem Token'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_detail_tarefa_sem_token_retorna_401(self, api_client, tarefa):
        response = api_client.get(self.detail_url(tarefa.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_tarefa_sem_token_retorna_401(self, api_client, tarefa):
        response = api_client.patch(self.detail_url(tarefa.id), {'status_tarefa': 'concluida'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_put_tarefa_sem_token_retorna_401(self, api_client, tarefa):
        response = api_client.put(self.detail_url(tarefa.id), {'titulo': 'Novo Titulo'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_tarefa_sem_token_retorna_401(self, api_client, tarefa):
        response = api_client.delete(self.detail_url(tarefa.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # --- Operações de Atualização e Exclusão ---

    def test_patch_atualizando_apenas_prioridade(self, auth_client, tarefa):
        url = self.detail_url(tarefa.id)
        response = auth_client.patch(url, {'prioridade': 'alta'})
        assert response.status_code == status.HTTP_200_OK
        tarefa.refresh_from_db()
        assert tarefa.prioridade == PrioridadeTarefa.ALTA

    def test_patch_atualizando_apenas_descricao(self, auth_client, tarefa):
        url = self.detail_url(tarefa.id)
        response = auth_client.patch(url, {'descricao': 'Nova descricao atualizada'})
        assert response.status_code == status.HTTP_200_OK
        tarefa.refresh_from_db()
        assert tarefa.descricao == 'Nova descricao atualizada'

    def test_patch_atualizando_apenas_status(self, auth_client, tarefa):
        url = self.detail_url(tarefa.id)
        response = auth_client.patch(url, {'status_tarefa': 'concluida'})
        assert response.status_code == status.HTTP_200_OK
        tarefa.refresh_from_db()
        assert tarefa.status_tarefa == StatusTarefa.CONCLUIDA

    def test_put_atualizacao_completa_sucesso(self, auth_client, tarefa):
        url = self.detail_url(tarefa.id)
        payload = {
            'titulo': 'Titulo Completamente Atualizado',
            'descricao': 'Descricao PUT',
            'status_tarefa': 'em_andamento',
            'prioridade': 'baixa',
            'data_vencimento': str(date.today() + timedelta(days=20)),
        }
        response = auth_client.put(url, payload)
        assert response.status_code == status.HTTP_200_OK
        tarefa.refresh_from_db()
        assert tarefa.titulo == 'Titulo Completamente Atualizado'
        assert tarefa.status_tarefa == StatusTarefa.EM_ANDAMENTO
        assert tarefa.prioridade == PrioridadeTarefa.BAIXA

    def test_delete_tarefa_inexistente_retorna_404(self, auth_client):
        url = self.detail_url(999999)
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_tarefa_outro_usuario_retorna_404(self, auth_client, outra_tarefa):
        url = self.detail_url(outra_tarefa.id)
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patch_tarefa_outro_usuario_retorna_404(self, auth_client, outra_tarefa):
        url = self.detail_url(outra_tarefa.id)
        response = auth_client.patch(url, {'titulo': 'Tentativa Invasora'})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # --- Filtros Combinados, Ordenação e Paginação ---

    def test_ordenacao_e_paginacao_juntas(self, auth_client, usuario, tarefa_factory):
        hoje = date.today()
        # Cria tarefas com diferentes prioridades e vencimentos
        tarefa_factory.create(usuario=usuario, titulo='T1', prioridade=PrioridadeTarefa.BAIXA, data_vencimento=hoje + timedelta(days=1))
        tarefa_factory.create(usuario=usuario, titulo='T2', prioridade=PrioridadeTarefa.ALTA, data_vencimento=hoje + timedelta(days=2))
        tarefa_factory.create(usuario=usuario, titulo='T3', prioridade=PrioridadeTarefa.MEDIA, data_vencimento=hoje + timedelta(days=3))

        # Ordenar por prioridade e paginar com page_size=2
        response = auth_client.get(f'{self.list_create_url}?ordering=prioridade&page=1&page_size=2')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        assert response.data['count'] == 3
        assert response.data['next'] is not None

        # Página 2
        response_p2 = auth_client.get(f'{self.list_create_url}?ordering=prioridade&page=2&page_size=2')
        assert response_p2.status_code == status.HTTP_200_OK
        assert len(response_p2.data['results']) == 1

    def test_filtros_combinados_status_prioridade_intervalo_vencimento(self, auth_client, usuario, tarefa_factory):
        hoje = date.today()
        # Tarefa alvo que atende todos os critérios
        alvo = tarefa_factory.create(
            usuario=usuario,
            titulo='Alvo',
            status_tarefa=StatusTarefa.PENDENTE,
            prioridade=PrioridadeTarefa.ALTA,
            data_vencimento=hoje + timedelta(days=5)
        )
        # Tarefas que falham em um dos critérios
        tarefa_factory.create(
            usuario=usuario,
            titulo='Status Diferente',
            status_tarefa=StatusTarefa.CONCLUIDA,
            prioridade=PrioridadeTarefa.ALTA,
            data_vencimento=hoje + timedelta(days=5)
        )
        tarefa_factory.create(
            usuario=usuario,
            titulo='Prioridade Diferente',
            status_tarefa=StatusTarefa.PENDENTE,
            prioridade=PrioridadeTarefa.BAIXA,
            data_vencimento=hoje + timedelta(days=5)
        )
        tarefa_factory.create(
            usuario=usuario,
            titulo='Data Fora do Intervalo',
            status_tarefa=StatusTarefa.PENDENTE,
            prioridade=PrioridadeTarefa.ALTA,
            data_vencimento=hoje + timedelta(days=30)
        )

        query = (
            f'?status_tarefa=pendente'
            f'&prioridade=alta'
            f'&data_vencimento_inicio={hoje + timedelta(days=1)}'
            f'&data_vencimento_fim={hoje + timedelta(days=10)}'
        )
        response = auth_client.get(f'{self.list_create_url}{query}')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == alvo.id

    def test_pagina_inexistente_retorna_404(self, auth_client):
        response = auth_client.get(f'{self.list_create_url}?page=9999')
        assert response.status_code == status.HTTP_404_NOT_FOUND

