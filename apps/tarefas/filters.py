import django_filters

from tarefas.models import Tarefa


class TarefaFilter(django_filters.FilterSet):
    """
    Filtros para listagem de tarefas:
    - status_tarefa: correspondência exata (pendente, em_andamento, concluida)
    - prioridade: correspondência exata (baixa, media, alta)
    - data_vencimento_inicio: data de vencimento maior ou igual (gte)
    - data_vencimento_fim: data de vencimento menor ou igual (lte)
    """
    status_tarefa = django_filters.CharFilter(field_name='status_tarefa', lookup_expr='exact')
    prioridade = django_filters.CharFilter(field_name='prioridade', lookup_expr='exact')
    data_vencimento_inicio = django_filters.DateFilter(field_name='data_vencimento', lookup_expr='gte')
    data_vencimento_fim = django_filters.DateFilter(field_name='data_vencimento', lookup_expr='lte')

    class Meta:
        model = Tarefa
        fields = [
            'status_tarefa',
            'prioridade',
            'data_vencimento_inicio',
            'data_vencimento_fim',
        ]
