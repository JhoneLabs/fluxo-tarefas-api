from rest_framework.pagination import PageNumberPagination


class TarefaPagination(PageNumberPagination):
    """
    Paginação personalizada para listagem de tarefas:
    - 10 itens por página por padrão
    - Parâmetro 'page_size' customizável pelo cliente
    - Limite máximo de 50 itens por página
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
