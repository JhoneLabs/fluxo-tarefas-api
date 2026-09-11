from datetime import date, timedelta
from unittest.mock import patch

import pytest
from rest_framework.exceptions import NotFound, ValidationError

from tarefas.models import PrioridadeTarefa, StatusTarefa, Tarefa
from tarefas.repositories import TarefaRepository
from tarefas.services import TarefaService


@pytest.mark.django_db
class TestTarefaService:
    """Testes unitários para a camada TarefaService."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = TarefaService()
        self.repo = TarefaRepository()

    def test_listar_tarefas_isola_por_usuario(self, usuario, outro_usuario, tarefa_factory):
        tarefa_factory.create(usuario=usuario, titulo='T1')
        tarefa_factory.create(usuario=usuario, titulo='T2')
        tarefa_factory.create(usuario=outro_usuario, titulo='T_Outro')

        tarefas = self.service.listar_tarefas(usuario)
        assert tarefas.count() == 2
        assert all(t.usuario == usuario for t in tarefas)

    def test_obter_tarefa_sucesso(self, usuario, tarefa_factory):
        t = tarefa_factory.create(usuario=usuario)
        encontrada = self.service.obter_tarefa(t.id, usuario)
        assert encontrada.id == t.id

    def test_obter_tarefa_inexistente_lanca_not_found(self, usuario):
        with pytest.raises(NotFound) as exc_info:
            self.service.obter_tarefa(999999, usuario)
        assert 'Tarefa não encontrada' in str(exc_info.value.detail)

    def test_obter_tarefa_outro_usuario_lanca_not_found(self, usuario, outro_usuario, tarefa_factory):
        t_outro = tarefa_factory.create(usuario=outro_usuario)
        with pytest.raises(NotFound) as exc_info:
            self.service.obter_tarefa(t_outro.id, usuario)
        assert 'Tarefa não encontrada' in str(exc_info.value.detail)

    def test_criar_tarefa_sucesso(self, usuario):
        dados = {
            'titulo': 'Nova Tarefa Service',
            'descricao': 'Descrição da tarefa',
            'prioridade': PrioridadeTarefa.ALTA,
            'status_tarefa': StatusTarefa.PENDENTE,
        }
        tarefa = self.service.criar_tarefa(usuario, dados)
        assert tarefa.id is not None
        assert tarefa.titulo == 'Nova Tarefa Service'
        assert tarefa.usuario == usuario


    def test_criar_tarefa_titulo_vazio_lanca_validation_error(self, usuario):
        with pytest.raises(ValidationError) as exc_info:
            self.service.criar_tarefa(usuario, {'titulo': '   '})
        assert 'titulo' in exc_info.value.detail

    def test_criar_tarefa_titulo_ausente_lanca_validation_error(self, usuario):
        with pytest.raises(ValidationError) as exc_info:
            self.service.criar_tarefa(usuario, {})
        assert 'titulo' in exc_info.value.detail

    @patch('tarefas.tasks.notificar_tarefa_proxima_vencimento.delay')
    def test_criar_tarefa_com_vencimento_proximo_dispara_celery(self, mock_delay, usuario):
        dados = {
            'titulo': 'Tarefa Vence Amanhã',
            'data_vencimento': date.today() + timedelta(days=1),
            'status_tarefa': StatusTarefa.PENDENTE,
        }
        tarefa = self.service.criar_tarefa(usuario, dados)
        mock_delay.assert_called_once_with(tarefa.id)

    @patch('tarefas.tasks.notificar_tarefa_proxima_vencimento.delay')
    def test_criar_tarefa_com_vencimento_hoje_dispara_celery(self, mock_delay, usuario):
        dados = {
            'titulo': 'Tarefa Vence Hoje',
            'data_vencimento': date.today(),
            'status_tarefa': StatusTarefa.EM_ANDAMENTO,
        }
        tarefa = self.service.criar_tarefa(usuario, dados)
        mock_delay.assert_called_once_with(tarefa.id)

    @patch('tarefas.tasks.notificar_tarefa_proxima_vencimento.delay')
    def test_criar_tarefa_sem_vencimento_nao_dispara_celery(self, mock_delay, usuario):
        dados = {
            'titulo': 'Tarefa Sem Vencimento',
            'data_vencimento': None,
        }
        self.service.criar_tarefa(usuario, dados)
        mock_delay.assert_not_called()

    @patch('tarefas.tasks.notificar_tarefa_proxima_vencimento.delay')
    def test_criar_tarefa_concluida_nao_dispara_celery(self, mock_delay, usuario):
        dados = {
            'titulo': 'Tarefa Já Concluída',
            'data_vencimento': date.today(),
            'status_tarefa': StatusTarefa.CONCLUIDA,
        }
        self.service.criar_tarefa(usuario, dados)
        mock_delay.assert_not_called()

    @patch('tarefas.tasks.notificar_tarefa_proxima_vencimento.delay')
    def test_criar_tarefa_vencida_nao_dispara_celery(self, mock_delay, usuario):
        dados = {
            'titulo': 'Tarefa Vencida',
            'data_vencimento': date.today(),
            'status_tarefa': StatusTarefa.VENCIDA,
        }
        self.service.criar_tarefa(usuario, dados)
        mock_delay.assert_not_called()

    def test_atualizar_tarefa_sucesso(self, usuario, tarefa_factory):
        t = tarefa_factory.create(usuario=usuario, titulo='Original')
        atualizada = self.service.atualizar_tarefa(t.id, usuario, {'titulo': 'Modificado'})
        assert atualizada.titulo == 'Modificado'

    def test_atualizar_tarefa_outro_usuario_lanca_not_found(self, usuario, outro_usuario, tarefa_factory):
        t_outro = tarefa_factory.create(usuario=outro_usuario)
        with pytest.raises(NotFound):
            self.service.atualizar_tarefa(t_outro.id, usuario, {'titulo': 'Tentativa'})

    def test_deletar_tarefa_sucesso(self, usuario, tarefa_factory):
        t = tarefa_factory.create(usuario=usuario)
        self.service.deletar_tarefa(t.id, usuario)
        assert not Tarefa.objects.filter(id=t.id).exists()

    def test_deletar_tarefa_outro_usuario_lanca_not_found(self, usuario, outro_usuario, tarefa_factory):
        t_outro = tarefa_factory.create(usuario=outro_usuario)
        with pytest.raises(NotFound):
            self.service.deletar_tarefa(t_outro.id, usuario)
        assert Tarefa.objects.filter(id=t_outro.id).exists()

    def test_tarefa_str(self, tarefa):
        assert str(tarefa) == f"{tarefa.titulo} ({tarefa.get_status_tarefa_display()})"



@pytest.mark.django_db
class TestTarefaRepository:
    """Testes unitários para a camada TarefaRepository."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.repo = TarefaRepository()

    def test_obter_por_id_e_usuario_retorna_none_para_outro_usuario(self, usuario, outro_usuario, tarefa_factory):
        t = tarefa_factory.create(usuario=usuario)
        assert self.repo.obter_por_id_e_usuario(t.id, outro_usuario) is None

    def test_obter_por_id_e_usuario_retorna_none_para_id_inexistente(self, usuario):
        assert self.repo.obter_por_id_e_usuario(999999, usuario) is None
