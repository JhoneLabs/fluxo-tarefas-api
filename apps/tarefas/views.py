from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tarefas.filters import TarefaFilter
from tarefas.pagination import TarefaPagination
from tarefas.serializers import TarefaSerializer
from tarefas.services import TarefaService


class TarefaListCreateView(generics.GenericAPIView):
    """
    Endpoint para listagem (com filtros, ordenação e paginação) e criação de tarefas do usuário autenticado.
    GET /api/tarefas/
    POST /api/tarefas/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TarefaSerializer
    pagination_class = TarefaPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = TarefaFilter
    ordering_fields = ['data_vencimento', 'data_criacao', 'prioridade']
    ordering = ['-data_criacao']

    def __init__(self, service: TarefaService = None, **kwargs):
        super().__init__(**kwargs)
        self.service = service or TarefaService()

    def get_queryset(self):
        return self.service.listar_tarefas(self.request.user)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tarefa = self.service.criar_tarefa(request.user, serializer.validated_data)
        response_serializer = self.get_serializer(tarefa)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class TarefaDetailView(APIView):
    """
    Endpoint para consulta, atualização e remoção de uma tarefa individual.
    Garante que apenas o proprietário da tarefa consiga acessá-la ou modificá-la (retornando 404 caso contrário).
    GET /api/tarefas/{id}/
    PATCH /api/tarefas/{id}/
    PUT /api/tarefas/{id}/
    DELETE /api/tarefas/{id}/
    """
    permission_classes = [IsAuthenticated]

    def __init__(self, service: TarefaService = None, **kwargs):
        super().__init__(**kwargs)
        self.service = service or TarefaService()

    def get(self, request, pk: int):
        tarefa = self.service.obter_tarefa(pk, request.user)
        serializer = TarefaSerializer(tarefa)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk: int):
        tarefa = self.service.obter_tarefa(pk, request.user)
        serializer = TarefaSerializer(tarefa, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        tarefa_atualizada = self.service.atualizar_tarefa(pk, request.user, serializer.validated_data)
        return Response(TarefaSerializer(tarefa_atualizada).data, status=status.HTTP_200_OK)

    def put(self, request, pk: int):
        tarefa = self.service.obter_tarefa(pk, request.user)
        serializer = TarefaSerializer(tarefa, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        tarefa_atualizada = self.service.atualizar_tarefa(pk, request.user, serializer.validated_data)
        return Response(TarefaSerializer(tarefa_atualizada).data, status=status.HTTP_200_OK)

    def delete(self, request, pk: int):
        self.service.deletar_tarefa(pk, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
