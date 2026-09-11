from rest_framework import serializers

from tarefas.models import Tarefa


class TarefaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Tarefa.
    O vínculo com o usuário autenticado é gerenciado na camada de serviço.
    """

    class Meta:
        model = Tarefa
        fields = (
            'id',
            'titulo',
            'descricao',
            'status_tarefa',
            'prioridade',
            'data_vencimento',
            'data_criacao',
            'data_atualizacao',
        )
        read_only_fields = ('id', 'data_criacao', 'data_atualizacao')
