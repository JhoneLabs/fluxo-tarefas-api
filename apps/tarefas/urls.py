from django.urls import path
from tarefas.views import TarefaDetailView, TarefaListCreateView

urlpatterns = [
    path('', TarefaListCreateView.as_view(), name='tarefa-list-create'),
    path('<int:pk>/', TarefaDetailView.as_view(), name='tarefa-detail'),
]
