from typing import Any, Dict
from django.db.models import QuerySet
from rest_framework.exceptions import NotFound, ValidationError
from tarefas.models import Tarefa
from tarefas.repositories import TarefaRepository


class TarefaService:
    """
    Camada de serviço contendo as regras de negócio para gerenciamento de tarefas.
    Aplica regras de isolamento garantindo retorno HTTP 404 quando o recurso não pertencer ao usuário.
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

        return self.repository.criar(usuario=usuario, **dados_validados)

    def atualizar_tarefa(self, tarefa_id: int, usuario, dados_validados: Dict[str, Any]) -> Tarefa:
        """
        Atualiza uma tarefa do usuário autenticado.
        Se a tarefa não pertencer ao usuário, lança NotFound (HTTP 404).
        """
        tarefa = self.obter_tarefa(tarefa_id, usuario)
        return self.repository.atualizar(tarefa, **dados_validados)

    def deletar_tarefa(self, tarefa_id: int, usuario) -> None:
        """
        Remove uma tarefa do usuário autenticado.
        Se a tarefa não pertencer ao usuário, lança NotFound (HTTP 404).
        """
        tarefa = self.obter_tarefa(tarefa_id, usuario)
        self.repository.deletar(tarefa)
