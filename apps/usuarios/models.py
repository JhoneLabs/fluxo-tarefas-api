from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Modelo customizado de Usuário estendendo AbstractUser.
    Inclui campos adicionais e rastreamento temporal com nomenclatura em português.
    """
    email = models.EmailField(unique=True, verbose_name='E-mail')
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data de atualização')

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-data_criacao']

    def __str__(self):
        return self.username
