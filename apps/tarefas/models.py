from django.conf import settings
from django.db import models


class StatusTarefa(models.TextChoices):
    PENDENTE = 'pendente', 'Pendente'
    EM_ANDAMENTO = 'em_andamento', 'Em andamento'
    CONCLUIDA = 'concluida', 'Concluída'


class PrioridadeTarefa(models.TextChoices):
    BAIXA = 'baixa', 'Baixa'
    MEDIA = 'media', 'Média'
    ALTA = 'alta', 'Alta'


class Tarefa(models.Model):
    """
    Modelo de Tarefa com rastreamento de status, prioridade e vínculo com o usuário proprietário.
    """
    titulo = models.CharField(max_length=255, verbose_name='Título')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    status_tarefa = models.CharField(
        max_length=20,
        choices=StatusTarefa.choices,
        default=StatusTarefa.PENDENTE,
        verbose_name='Status da tarefa'
    )
    prioridade = models.CharField(
        max_length=10,
        choices=PrioridadeTarefa.choices,
        default=PrioridadeTarefa.MEDIA,
        verbose_name='Prioridade'
    )
    data_vencimento = models.DateField(blank=True, null=True, verbose_name='Data de vencimento')
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data de atualização')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tarefas',
        verbose_name='Usuário'
    )

    class Meta:
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'
        ordering = ['-data_criacao']

    def __str__(self):
        return f'{self.titulo} ({self.get_status_tarefa_display()})'
