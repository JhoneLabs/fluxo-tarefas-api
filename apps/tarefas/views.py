from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tarefas.filters import TarefaFilter
from tarefas.models import Tarefa
from tarefas.pagination import TarefaPagination
from tarefas.serializers import TarefaSerializer
from tarefas.services import TarefaService



@extend_schema_view(
    get=extend_schema(
        tags=['Tarefas'],
        summary='Listar tarefas',
        description=(
            'Retorna a lista paginada de tarefas do usuário autenticado. '
            'Suporta filtros por status_tarefa, prioridade, data_vencimento_inicio e data_vencimento_fim, '
            'além de ordenação (data_vencimento, data_criacao, prioridade).'
        ),
        responses={status.HTTP_200_OK: TarefaSerializer(many=True)},
    ),
    post=extend_schema(
        tags=['Tarefas'],
        summary='Criar tarefa',
        description='Cria uma nova tarefa associada ao usuário autenticado.',
        request=TarefaSerializer,
        responses={
            status.HTTP_201_CREATED: TarefaSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(description='Erro de validação dos dados da tarefa.'),
        },
    ),
)
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
    queryset = Tarefa.objects.none()

    def __init__(self, service: TarefaService = None, **kwargs):
        super().__init__(**kwargs)
        self.service = service or TarefaService()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Tarefa.objects.none()
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


@extend_schema_view(
    get=extend_schema(
        tags=['Tarefas'],
        summary='Obter detalhes de uma tarefa',
        description='Retorna os detalhes de uma tarefa específica do usuário autenticado pelo ID.',
        responses={
            status.HTTP_200_OK: TarefaSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description='Tarefa não encontrada ou não pertence ao usuário.'),
        },
    ),
    patch=extend_schema(
        tags=['Tarefas'],
        summary='Atualizar tarefa parcialmente',
        description='Atualiza parcialmente os campos informados de uma tarefa específica pertencente ao usuário.',
        request=TarefaSerializer,
        responses={
            status.HTTP_200_OK: TarefaSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(description='Erro de validação dos dados informados.'),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description='Tarefa não encontrada ou não pertence ao usuário.'),
        },
    ),
    put=extend_schema(
        tags=['Tarefas'],
        summary='Atualizar tarefa completamente',
        description='Atualiza todos os campos de uma tarefa específica pertencente ao usuário autenticado.',
        request=TarefaSerializer,
        responses={
            status.HTTP_200_OK: TarefaSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(description='Erro de validação dos dados informados.'),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description='Tarefa não encontrada ou não pertence ao usuário.'),
        },
    ),
    delete=extend_schema(
        tags=['Tarefas'],
        summary='Excluir tarefa',
        description='Remove uma tarefa específica pertencente ao usuário autenticado.',
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(description='Tarefa removida com sucesso.'),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description='Tarefa não encontrada ou não pertence ao usuário.'),
        },
    ),
)
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

