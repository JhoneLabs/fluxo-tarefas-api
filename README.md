# fluxo-tarefas-api

API REST para gerenciamento de fluxo de tarefas desenvolvida com Django REST Framework.

## Stack Utilizada

- **Python 3.12**
- **Django 5.1** & **Django REST Framework**
- **PostgreSQL 16** (Banco de dados relacional)
- **Redis 7** (Cache e mensageria)
- **Docker & Docker Compose** (Containerização do ambiente)
- **django-environ** (Gerenciamento de configurações e variáveis de ambiente)
- **django-cors-headers** (Controle de CORS)

## Estrutura do Projeto

```text
fluxo-tarefas-api/
├── apps/                 # Módulos/aplicações Django do projeto
├── config/               # Configurações do projeto
│   ├── settings/         # Configurações modularizadas
│   │   ├── __init__.py
│   │   ├── base.py       # Configurações base compartilhadas
│   │   ├── dev.py        # Configurações de desenvolvimento
│   │   └── production.py # Configurações de produção
│   ├── asgi.py
│   ├── urls.py
│   └── wsgi.py
├── .dockerignore
├── .env.example          # Modelo de variáveis de ambiente
├── .gitignore
├── docker-compose.yml    # Orquestração dos containers (web, db, redis)
├── Dockerfile            # Imagem multi-stage Python 3.12
├── manage.py
├── README.md
└── requirements.txt      # Dependências do projeto
```

## Instruções de Setup

### 1. Clonar o repositório

```bash
git clone https://github.com/JhoneLabs/fluxo-tarefas-api.git
cd fluxo-tarefas-api
```

### 2. Configurar as variáveis de ambiente

Copie o arquivo de exemplo `.env.example` para `.env`:

```bash
cp .env.example .env
```

### 3. Construir e executar com Docker Compose

Suba os serviços (`web`, `db` e `redis`):

```bash
docker compose up --build
```

A API estará acessível em:
- **API / Página inicial**: [http://localhost:8000](http://localhost:8000)
- **Django Admin**: [http://localhost:8000/admin](http://localhost:8000/admin)
