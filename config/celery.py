import os
from celery import Celery

# Define as configurações padrão do Django para o Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('fluxo_tarefas')

# Lê as configurações com namespace 'CELERY' do settings.py do Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Carrega automaticamente as tasks registradas em tasks.py de todos os apps instalados
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
