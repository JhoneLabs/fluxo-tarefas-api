from typing import Any, Dict, Optional
from django.db.models import QuerySet
from tarefas.models import Tarefa


class TarefaRepository:
    """
    Camada de repositório responsável pelo acesso e persistência de dados do modelo Tarefa.
    Garante o isolamento estrito de consultas pelo usuário proprietário.
    """

    @staticmethod
    def listar_por_usuario(usuario) -> QuerySet[Tarefa]:
        """Retorna apenas as tarefas pertencentes ao usuário informado."""
        return Tarefa.objects.filter(usuario=usuario)

    @staticmethod
    def obter_por_id_e_usuario(tarefa_id: int, usuario) -> Optional[Tarefa]:
        """
        Busca uma tarefa pelo seu ID assegurando que pertença ao usuário.
        Retorna None se a tarefa não existir ou pertencer a outro usuário.
        """
        try:
            return Tarefa.objects.get(pk=tarefa_id, usuario=usuario)
        except Tarefa.DoesNotExist:
            return None

    @staticmethod
    def criar(usuario, **dados) -> Tarefa:
        """Cria e persiste uma nova tarefa associada ao usuário autenticado."""
        return Tarefa.objects.create(usuario=usuario, **dados)

    @staticmethod
    def atualizar(tarefa: Tarefa, **dados: Dict[str, Any]) -> Tarefa:
        """Atualiza os campos fornecidos de uma instância de Tarefa existente."""
        for campo, valor in dados.items():
            setattr(tarefa, campo, valor)
        tarefa.save()
        return tarefa

    @staticmethod
    def deletar(tarefa: Tarefa) -> None:
        """Remove a tarefa do banco de dados."""
        tarefa.delete()
