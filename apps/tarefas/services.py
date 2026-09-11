from datetime import date, timedelta
from typing import Any, Dict

from django.db.models import QuerySet
from rest_framework.exceptions import NotFound, ValidationError

from tarefas.models import StatusTarefa, Tarefa
from tarefas.repositories import TarefaRepository


class TarefaService:
    """
    Camada de serviço contendo as regras de negócio para gerenciamento de tarefas.
    Aplica regras de isolamento garantindo retorno HTTP 404 quando o recurso não pertencer ao usuário
    e orquestra o disparo de tarefas assíncronas no Celery.
    """

    def __init__(self, repository: TarefaRepository = None):
        self.repository = repository or TarefaRepository()

    def listar_tarefas(self, usuario) -> QuerySet[Tarefa]:
        """Retorna a lista de tarefas associadas exclusivamente ao usuário."""
        return self.repository.listar_por_usuario(usuario)

    def obter_tarefa(self, tarefa_id: int, usuario) -> Tarefa:
        """
        Recupera a tarefa garantindo que pertença ao usuário requisitante.
        Lança NotFound (HTTP 404) caso não exista ou pertença a outro usuário.
        """
        tarefa = self.repository.obter_por_id_e_usuario(tarefa_id, usuario)
        if not tarefa:
            raise NotFound(detail="Tarefa não encontrada.")
        return tarefa

    def criar_tarefa(self, usuario, dados_validados: Dict[str, Any]) -> Tarefa:
        """Valida e cria uma nova tarefa vinculada ao usuário autenticado."""
        titulo = dados_validados.get('titulo')
        if not titulo or not str(titulo).strip():
            raise ValidationError({'titulo': 'O título é obrigatório.'})

        tarefa = self.repository.criar(usuario=usuario, **dados_validados)
        self._verificar_e_disparar_notificacao(tarefa)
        return tarefa

    def atualizar_tarefa(self, tarefa_id: int, usuario, dados_validados: Dict[str, Any]) -> Tarefa:
        """
        Atualiza uma tarefa do usuário autenticado.
        Se a tarefa não pertencer ao usuário, lança NotFound (HTTP 404).
        """
        tarefa = self.obter_tarefa(tarefa_id, usuario)
        tarefa_atualizada = self.repository.atualizar(tarefa, **dados_validados)
        self._verificar_e_disparar_notificacao(tarefa_atualizada)
        return tarefa_atualizada

    def deletar_tarefa(self, tarefa_id: int, usuario) -> None:
        """
        Remove uma tarefa do usuário autenticado.
        Se a tarefa não pertencer ao usuário, lança NotFound (HTTP 404).
        """
        tarefa = self.obter_tarefa(tarefa_id, usuario)
        self.repository.deletar(tarefa)

    def _verificar_e_disparar_notificacao(self, tarefa: Tarefa) -> None:
        """
        Verifica se a tarefa possui data de vencimento dentro das próximas 24h
        e não está concluída, disparando a task assíncrona notificar_tarefa_proxima_vencimento no Celery.
        """
        if not tarefa.data_vencimento or tarefa.status_tarefa in [StatusTarefa.CONCLUIDA, StatusTarefa.VENCIDA]:
            return

        hoje = date.today()
        # Vencimento hoje ou amanhã (próximas 24 horas)
        if hoje <= tarefa.data_vencimento <= hoje + timedelta(days=1):
            from tarefas.tasks import notificar_tarefa_proxima_vencimento
            notificar_tarefa_proxima_vencimento.delay(tarefa.id)
