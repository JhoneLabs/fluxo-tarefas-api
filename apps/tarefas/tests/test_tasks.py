from datetime import date, timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from tarefas.models import StatusTarefa, Tarefa
from tarefas.services import TarefaService
from tarefas.tasks import (
    notificar_tarefa_proxima_vencimento,
    verificar_tarefas_vencidas,
)

Usuario = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class CeleryTasksTestCase(TestCase):
    """
    Testes para as tarefas assíncronas e periódicas do Celery.
    Executadas de forma síncrona através de CELERY_TASK_ALWAYS_EAGER=True.
    """

    def setUp(self):
        self.user = Usuario.objects.create_user(
            username='celery_user',
            email='celery@example.com',
            password='Password123!@#'
        )
        self.service = TarefaService()

    def test_notificar_tarefa_proxima_vencimento_sucesso(self):
        """A task notificar_tarefa_proxima_vencimento deve gerar a mensagem de log corretamente."""
        tarefa = Tarefa.objects.create(
            titulo='Tarefa Vencendo Hoje',
            data_vencimento=date.today(),
            status_tarefa=StatusTarefa.PENDENTE,
            usuario=self.user
        )

        resultado = notificar_tarefa_proxima_vencimento.delay(tarefa.id).get()

        self.assertIsNotNone(resultado)
        self.assertIn(str(tarefa.id), resultado)
        self.assertIn('Tarefa Vencendo Hoje', resultado)
        self.assertIn('celery_user', resultado)
        self.assertIn(str(date.today()), resultado)

    def test_notificar_tarefa_proxima_vencimento_tarefa_inexistente(self):
        """A task deve tratar graciosamente IDs inexistentes sem lançar exceção fatal."""
        resultado = notificar_tarefa_proxima_vencimento.delay(99999).get()
        self.assertIsNone(resultado)

    @patch('tarefas.tasks.notificar_tarefa_proxima_vencimento.delay')
    def test_service_dispara_notificacao_quando_vencimento_dentro_24h(self, mock_notificar):
        """Ao criar tarefa com vencimento para amanhã, o serviço deve agendar a notificação."""
        hoje = date.today()
        amanha = hoje + timedelta(days=1)

        self.service.criar_tarefa(self.user, {
            'titulo': 'Tarefa com vencimento em 24h',
            'data_vencimento': amanha,
        })

        self.assertTrue(mock_notificar.called)

    @patch('tarefas.tasks.notificar_tarefa_proxima_vencimento.delay')
    def test_service_nao_dispara_notificacao_quando_vencimento_distante(self, mock_notificar):
        """Ao criar tarefa com vencimento distante (> 24h), não deve disparar notificação."""
        futuro = date.today() + timedelta(days=10)

        self.service.criar_tarefa(self.user, {
            'titulo': 'Tarefa com vencimento distante',
            'data_vencimento': futuro,
        })

        self.assertFalse(mock_notificar.called)

    def test_verificar_tarefas_vencidas_atualiza_apenas_vencidas_nao_concluidas(self):
        """
        A task verificar_tarefas_vencidas deve:
        - Atualizar tarefas com data anterior a hoje de 'pendente'/'em_andamento' para 'vencida'
        - NÃO alterar tarefas com data anterior a hoje que já estejam 'concluida'
        - NÃO alterar tarefas com data igual ou posterior a hoje
        """
        ontem = date.today() - timedelta(days=1)
        cinco_dias_atras = date.today() - timedelta(days=5)
        hoje = date.today()
        amanha = date.today() + timedelta(days=1)

        # Tarefas que DEVEM ser marcadas como vencidas
        t_pendente_vencida = Tarefa.objects.create(
            titulo='Pendente Vencida',
            data_vencimento=ontem,
            status_tarefa=StatusTarefa.PENDENTE,
            usuario=self.user
        )
        t_em_andamento_vencida = Tarefa.objects.create(
            titulo='Em Andamento Vencida',
            data_vencimento=cinco_dias_atras,
            status_tarefa=StatusTarefa.EM_ANDAMENTO,
            usuario=self.user
        )

        # Tarefas que NÃO DEVEM ser alteradas
        t_concluida = Tarefa.objects.create(
            titulo='Concluída no Passado',
            data_vencimento=ontem,
            status_tarefa=StatusTarefa.CONCLUIDA,
            usuario=self.user
        )
        t_hoje = Tarefa.objects.create(
            titulo='Vence Hoje',
            data_vencimento=hoje,
            status_tarefa=StatusTarefa.PENDENTE,
            usuario=self.user
        )
        t_futura = Tarefa.objects.create(
            titulo='Vence Amanhã',
            data_vencimento=amanha,
            status_tarefa=StatusTarefa.PENDENTE,
            usuario=self.user
        )

        # Executa a task periódica
        total_atualizadas = verificar_tarefas_vencidas.delay().get()

        self.assertEqual(total_atualizadas, 2)

        t_pendente_vencida.refresh_from_db()
        t_em_andamento_vencida.refresh_from_db()
        t_concluida.refresh_from_db()
        t_hoje.refresh_from_db()
        t_futura.refresh_from_db()

        self.assertEqual(t_pendente_vencida.status_tarefa, StatusTarefa.VENCIDA)
        self.assertEqual(t_em_andamento_vencida.status_tarefa, StatusTarefa.VENCIDA)
        self.assertEqual(t_concluida.status_tarefa, StatusTarefa.CONCLUIDA)
        self.assertEqual(t_hoje.status_tarefa, StatusTarefa.PENDENTE)
        self.assertEqual(t_futura.status_tarefa, StatusTarefa.PENDENTE)
