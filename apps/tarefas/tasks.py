import logging
from datetime import date

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='tarefas.tasks.notificar_tarefa_proxima_vencimento')
def notificar_tarefa_proxima_vencimento(tarefa_id: int):
    """
    Task assíncrona para notificar o usuário quando uma tarefa estiver a menos de 24h do vencimento.
    Atualmente simula o envio registrando logs estruturados.
    """
    from tarefas.models import Tarefa

    try:
        tarefa = Tarefa.objects.select_related('usuario').get(pk=tarefa_id)
    except Tarefa.DoesNotExist:
        logger.warning(f"[CELERY] Tarefa ID {tarefa_id} não encontrada para disparo de notificação.")
        return None

    mensagem = (
        f"[NOTIFICACAO VENCIMENTO] Usuário '{tarefa.usuario.username}' ({tarefa.usuario.email}): "
        f"A tarefa '{tarefa.titulo}' (ID: {tarefa.id}) vence em breve na data {tarefa.data_vencimento}. "
        f"Status atual: '{tarefa.status_tarefa}', Prioridade: '{tarefa.prioridade}'."
    )
    logger.info(mensagem)

    # =========================================================================
    # PONTO DE EXTENSÃO PARA ENVIO REAL DE E-MAIL / NOTIFICAÇÃO PUSH:
    # -------------------------------------------------------------------------
    # from django.core.mail import send_mail
    # from django.conf import settings
    #
    # send_mail(
    #     subject=f"Lembrete: Tarefa '{tarefa.titulo}' próxima do vencimento!",
    #     message=mensagem,
    #     from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@fluxotarefas.com'),
    #     recipient_list=[tarefa.usuario.email],
    #     fail_silently=False,
    # )
    # =========================================================================

    return mensagem


@shared_task(name='tarefas.tasks.verificar_tarefas_vencidas')
def verificar_tarefas_vencidas():
    """
    Task periódica agendada via Celery Beat para execução diária.
    Localiza todas as tarefas com data_vencimento anterior à data atual (hoje)
    cujo status não seja 'concluida' nem 'vencida', e atualiza-as em lote para 'vencida'.
    """
    from tarefas.models import StatusTarefa, Tarefa

    hoje = date.today()
    tarefas_vencidas_qs = Tarefa.objects.filter(
        data_vencimento__lt=hoje
    ).exclude(
        status_tarefa__in=[StatusTarefa.CONCLUIDA, StatusTarefa.VENCIDA]
    )

    total_atualizadas = tarefas_vencidas_qs.update(status_tarefa=StatusTarefa.VENCIDA)

    logger.info(
        f"[CELERY BEAT] Verificação diária de tarefas vencidas concluída. "
        f"{total_atualizadas} tarefa(s) foram atualizadas para o status 'vencida'."
    )
    return total_atualizadas
