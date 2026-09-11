from datetime import date, timedelta

import factory
from django.contrib.auth import get_user_model
from tarefas.models import PrioridadeTarefa, StatusTarefa, Tarefa

Usuario = get_user_model()


class UsuarioFactory(factory.django.DjangoModelFactory):
    """Fábrica para criação de instâncias do modelo Usuario."""

    class Meta:
        model = Usuario
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    first_name = 'Nome'
    last_name = 'Sobrenome'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Utiliza create_user para que a senha seja hashada corretamente."""
        password = kwargs.pop('password', 'SenhaForte123!@#')
        return model_class.objects.create_user(*args, password=password, **kwargs)



class TarefaFactory(factory.django.DjangoModelFactory):
    """Fábrica para criação de instâncias do modelo Tarefa."""

    class Meta:
        model = Tarefa

    titulo = factory.Sequence(lambda n: f'Tarefa {n}')
    descricao = factory.Sequence(lambda n: f'Descrição detalhada da tarefa {n}')
    status_tarefa = StatusTarefa.PENDENTE
    prioridade = PrioridadeTarefa.MEDIA
    data_vencimento = factory.LazyFunction(lambda: date.today() + timedelta(days=5))
    usuario = factory.SubFactory(UsuarioFactory)

