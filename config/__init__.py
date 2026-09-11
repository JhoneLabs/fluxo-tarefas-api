"""Configuration package for fluxo-tarefas-api."""
from .celery import app as celery_app

__all__ = ('celery_app',)
