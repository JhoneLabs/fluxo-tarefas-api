# Fluxo Tarefas API

[![CI/CD Build](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square)](https://github.com/JhoneLabs/fluxo-tarefas-api)
[![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen?style=flat-square)](https://github.com/JhoneLabs/fluxo-tarefas-api)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg?style=flat-square)](https://www.python.org/downloads/release/python-3120/)
[![Django 5.1](https://img.shields.io/badge/django-5.1-092E20.svg?style=flat-square&logo=django)](https://docs.djangoproject.com/en/5.1/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.15-red.svg?style=flat-square)](https://www.django-rest-framework.org/)
[![Celery](https://img.shields.io/badge/celery-5.4-37814A.svg?style=flat-square&logo=celery)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/redis-7.0-DC382D.svg?style=flat-square&logo=redis)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/postgres-16-336791.svg?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg?style=flat-square&logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg?style=flat-square)](LICENSE)

API RESTful robusta e escalável para gerenciamento de fluxo de tarefas e produtividade pessoal, desenvolvida com Python 3.12 e Django REST Framework. O projeto implementa autenticação segura stateless baseada em tokens JWT (com blacklist), isolamento estrito de dados por proprietário (*multi-tenant* por usuário), filtros dinâmicos, ordenação e paginação, além de processamento assíncrono e tarefas periódicas com Celery, Celery Beat e Redis.

A aplicação conta com documentação interativa OpenAPI 3.0 via Swagger UI e ReDoc, além de uma suíte de 102 testes automatizados com Pytest atingindo **98% de cobertura de código**.

---

## Sumário

- [Visão Geral e Arquitetura](#visão-geral-e-arquitetura)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Como Rodar Localmente (Docker)](#como-rodar-localmente-docker)
- [Documentação Interativa (Swagger / OpenAPI)](#documentação-interativa-swagger--openapi)
- [Endpoints da API](#endpoints-da-api)
  - [Autenticação e Usuários](#1-autenticação-e-usuários)
  - [Tarefas](#2-tarefas)
- [Processamento Assíncrono com Celery](#processamento-assíncrono-com-celery)
  - [Tasks Implementadas](#tasks-implementadas)
  - [Como Testar e Acompanhar o Celery](#como-testar-e-acompanhar-o-celery)
- [Testes Automatizados e Cobertura](#testes-automatizados-e-cobertura)
- [Licença](#licença)

---

## Visão Geral e Arquitetura

O projeto adota uma arquitetura limpa e desacoplada em três camadas principais dentro de cada aplicação de domínio:

```text
[HTTP Request]
       │
       ▼
┌──────────────┐     Recebe requisições HTTP, validação preliminar de entrada
│    Views     │ ──► e serialização de saída (Serializers / ViewSets).
└──────┬───────┘
       │
       ▼
┌──────────────┐     Contém as regras de negócio puras, validações de domínio,
│   Services   │ ──► controle de isolamento por proprietário e despacho de Celery.
└──────┬───────┘
       │
       ▼
┌──────────────┐     Encapsula o acesso a dados e consultas ORM do Django,
│ Repositories │ ──► isolando a persistência das regras de negócio.
└──────┬───────┘
       │
       ▼
[PostgreSQL / ORM]
```

### Benefícios dessa abordagem:
1. **Baixo Acoplamento**: Views cuidam apenas de protocolos HTTP (status codes, headers, parsing).
2. **Alta Testabilidade**: Services e Repositories podem ser testados de forma unitária isolada ou mockada com facilidade.
3. **Segurança por Padrão**: As operações de consulta e mutação de tarefas forçam a cláusula `usuario=request.user` em nível de repositório, impossibilitando acessos indevidos entre contas (*IDOR prevention*).

---

## Tecnologias Utilizadas

- **Linguagem & Framework Core**:
  - [Python 3.12](https://www.python.org/)
  - [Django 5.1](https://www.djangoproject.com/)
  - [Django REST Framework 3.15](https://www.django-rest-framework.org/)
- **Autenticação & Segurança**:
  - [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/) (JWT com rotação e blacklist de tokens)
  - [django-cors-headers](https://github.com/adamchainz/django-cors-headers) (Controle de CORS)
- **Mensageria & Filas Assíncronas**:
  - [Celery 5.4](https://docs.celeryq.dev/)
  - [django-celery-beat 2.7](https://django-celery-beat.readthedocs.io/) (Agendador dinâmico no banco de dados)
  - [Redis 7.0](https://redis.io/) (Message Broker & Result Backend)
- **Persistência de Dados**:
  - [PostgreSQL 16](https://www.postgresql.org/)
  - [psycopg 3](https://www.psycopg.org/) (Driver nativo moderno)
- **Filtros & Documentação**:
  - [django-filter 24.3](https://django-filter.readthedocs.io/) (Filtros declarativos)
  - [drf-spectacular 0.28](https://drf-spectacular.readthedocs.io/) (OpenAPI 3.0, Swagger UI e ReDoc)
- **Qualidade, Testes & Linter**:
  - [Pytest 8](https://docs.pytest.org/)
  - [pytest-django](https://pytest-django.readthedocs.io/) & [pytest-cov](https://pytest-cov.readthedocs.io/)
  - [factory-boy](https://factoryboy.readthedocs.io/) (Geração de fábricas de teste dinâmicas)
  - [ruff](https://beta.ruff.rs/docs/) (Linter e formatador ultrarrápido PEP 8)
- **Containerização & DevOps**:
  - [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/) (Build multi-stage otimizado)

---

## Estrutura de Pastas

```text
fluxo-tarefas-api/
├── apps/                         # Domínios de negócio da aplicação
│   ├── tarefas/                  # App de tarefas
│   │   ├── migrations/           # Migrações do banco de dados
│   │   ├── tests/                # Testes unitários e de integração
│   │   │   ├── test_docs.py      # Testes dos endpoints OpenAPI/Swagger
│   │   │   ├── test_services.py  # Testes unitários do TarefaService e TarefaRepository
│   │   │   ├── test_tarefas.py   # Testes de integração do CRUD de tarefas
│   │   │   ├── test_tasks.py     # Testes das tarefas do Celery (eager mode)
│   │   │   └── test_views_adicionais.py # Cenários de borda, filtros e paginação
│   │   ├── filters.py            # Filtros dinâmicos (TarefaFilter)
│   │   ├── models.py             # Modelos Tarefa, StatusTarefa e PrioridadeTarefa
│   │   ├── pagination.py         # Paginação customizada com controle de page_size
│   │   ├── repositories.py       # Camada de acesso a dados (ORM)
│   │   ├── serializers.py        # Serializadores e validações
│   │   ├── services.py           # Regras de negócio e disparo de tasks
│   │   ├── tasks.py              # Tasks assíncronas e periódicas do Celery
│   │   ├── urls.py               # Rotas HTTP do app
│   │   └── views.py              # Controllers DRF enriquecidos com OpenAPI
│   └── usuarios/                 # App de usuários e autenticação
│       ├── migrations/
│       ├── tests/
│       │   ├── test_auth.py      # Testes do fluxo de autenticação JWT
│       │   ├── test_services.py  # Testes unitários do UsuarioService e UsuarioRepository
│       │   └── test_views_edge_cases.py # Casos de borda, senhas fracas, blacklist
│       ├── models.py             # Modelo Usuario customizado (AbstractUser)
│       ├── repositories.py       # Consultas e criação de usuários
│       ├── serializers.py        # Validação de cadastro e resposta de perfil
│       ├── services.py           # Regras de cadastro, unicidade e logout
│       ├── urls.py               # Rotas de cadastro, login, refresh, logout, me
│       └── views.py              # Handlers HTTP
├── config/                       # Módulo de configuração do Django
│   ├── settings/
│   │   ├── base.py               # Configurações compartilhadas
│   │   ├── dev.py                # Configurações de desenvolvimento
│   │   ├── production.py         # Configurações de produção
│   │   └── test.py               # Configurações para suíte de testes (Celery eager)
│   ├── asgi.py
│   ├── celery.py                 # Instância e autodiscover do Celery
│   ├── urls.py                   # Roteamento global da aplicação
│   └── wsgi.py
├── tests/                        # Recursos globais de teste
│   ├── conftest.py               # Fixtures reutilizáveis (auth_client, factories)
│   └── factories.py              # Fábricas factory_boy (UsuarioFactory, TarefaFactory)
├── .env.example                  # Modelo de variáveis de ambiente
├── .gitignore                    # Arquivos ignorados pelo Git
├── conftest.py                   # Ponto de entrada de fixtures do Pytest
├── docker-compose.yml            # Orquestração (web, db, redis, celery_worker, celery_beat)
├── Dockerfile                    # Multi-stage build Python 3.12
├── manage.py                     # Utilitário de linha de comando do Django
├── pyproject.toml                # Configurações do linter ruff
├── pytest.ini                    # Configurações de execução e cobertura do Pytest
└── requirements.txt              # Dependências do projeto com versões fixadas
```

---

## Como Rodar Localmente (Docker)

### Pré-requisitos
- [Docker](https://docs.docker.com/get-docker/) (versão 24.0 ou superior)
- [Docker Compose](https://docs.docker.com/compose/) (versão 2.20 ou superior)
- Git

### 1. Clonar o Repositório
```bash
git clone https://github.com/JhoneLabs/fluxo-tarefas-api.git
cd fluxo-tarefas-api
```

### 2. Configurar as Variáveis de Ambiente
Copie o modelo pré-configurado `.env.example` para `.env`:
```bash
cp .env.example .env
```

### 3. Subir o Ambiente com Docker Compose
O comando a seguir constrói as imagens e inicializa os cinco serviços (`web`, `db`, `redis`, `celery_worker`, `celery_beat`):

```bash
docker compose up --build -d
```

### 4. Aplicar as Migrações do Banco de Dados
```bash
docker compose exec web python manage.py migrate
```

### 5. Verificar o Status dos Contêineres
```bash
docker compose ps
```

A API estará pronta e respondendo em:
- **Página Inicial / API**: [http://localhost:8000](http://localhost:8000)
- **Swagger UI**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **ReDoc**: [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)
- **OpenAPI Schema (YAML)**: [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)
- **Django Admin**: [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

## Documentação Interativa (Swagger / OpenAPI)

A especificação da API segue rigorosamente o padrão **OpenAPI 3.0**:

- **Swagger UI** (`/api/docs/`): Interface gráfica onde você pode autenticar via token JWT (`Authorize` -> `Bearer <access_token>`) e executar chamadas interativas diretamente no navegador.
- **ReDoc** (`/api/redoc/`): Navegação visual limpa e estruturada com documentação aprofundada de esquemas, payloads e respostas.
- **Schema Bruto** (`/api/schema/`): Download da especificação OpenAPI completa em formato YAML ou JSON para importação no Postman, Insomnia ou geração de SDKs clientes.

---

## Endpoints da API

### 1. Autenticação e Usuários

| Método | Rota | Descrição | Autenticação |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/usuarios/cadastro/` | Cadastra novo usuário | Pública |
| `POST` | `/api/usuarios/login/` | Autentica e gera par de tokens JWT | Pública |
| `POST` | `/api/usuarios/refresh/` | Renova access token expirado | Pública |
| `POST` | `/api/usuarios/logout/` | Invalida refresh token (blacklist) | `Bearer <token>` |
| `GET` | `/api/usuarios/me/` | Retorna o perfil do usuário logado | `Bearer <token>` |

#### Exemplo de Cadastro (`POST /api/usuarios/cadastro/`)
**Request Body:**
```json
{
  "username": "jhone_dev",
  "email": "jhone@example.com",
  "password": "SenhaForte123!@#",
  "first_name": "Jhone",
  "last_name": "Silva"
}
```
**Response (HTTP 201 Created):**
```json
{
  "id": 1,
  "username": "jhone_dev",
  "email": "jhone@example.com",
  "first_name": "Jhone",
  "last_name": "Silva",
  "data_criacao": "2026-09-11T10:00:00-03:00",
  "data_atualizacao": "2026-09-11T10:00:00-03:00"
}
```

#### Exemplo de Login (`POST /api/usuarios/login/`)
**Request Body:**
```json
{
  "username": "jhone_dev",
  "password": "SenhaForte123!@#"
}
```
**Response (HTTP 200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 2. Tarefas

Todos os endpoints de tarefas requerem o header:
```http
Authorization: Bearer <access_token>
```

| Método | Rota | Descrição | Autenticação |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/tarefas/` | Lista tarefas (filtros, ordenação e paginação) | `Bearer <token>` |
| `POST` | `/api/tarefas/` | Cria nova tarefa vinculada ao usuário | `Bearer <token>` |
| `GET` | `/api/tarefas/{id}/` | Detalhes de uma tarefa | `Bearer <token>` |
| `PATCH` | `/api/tarefas/{id}/` | Atualização parcial de campos | `Bearer <token>` |
| `PUT` | `/api/tarefas/{id}/` | Atualização completa de tarefa | `Bearer <token>` |
| `DELETE`| `/api/tarefas/{id}/` | Exclusão de tarefa | `Bearer <token>` |

#### Exemplo de Criação de Tarefa (`POST /api/tarefas/`)
**Request Body:**
```json
{
  "titulo": "Preparar apresentação do portfólio",
  "descricao": "Gravar vídeo demonstrando arquitetura e testes do projeto",
  "status_tarefa": "pendente",
  "prioridade": "alta",
  "data_vencimento": "2026-09-15"
}
```
**Response (HTTP 201 Created):**
```json
{
  "id": 1,
  "titulo": "Preparar apresentação do portfólio",
  "descricao": "Gravar vídeo demonstrando arquitetura e testes do projeto",
  "status_tarefa": "pendente",
  "prioridade": "alta",
  "data_vencimento": "2026-09-15",
  "data_criacao": "2026-09-11T10:05:00-03:00",
  "data_atualizacao": "2026-09-11T10:05:00-03:00"
}
```

#### Filtros, Ordenação e Paginação (`GET /api/tarefas/`)
- **Filtros por Query Params**:
  - `status_tarefa`: `pendente`, `em_andamento`, `concluida`, `vencida`
  - `prioridade`: `baixa`, `media`, `alta`
  - `data_vencimento_inicio`: Data mínima de vencimento (`YYYY-MM-DD`)
  - `data_vencimento_fim`: Data máxima de vencimento (`YYYY-MM-DD`)
- **Ordenação** (`ordering`):
  - `data_vencimento`, `-data_vencimento`, `data_criacao`, `-data_criacao`, `prioridade`, `-prioridade`
- **Paginação** (`page` e `page_size`):
  - `page`: Número da página (padrão: 1)
  - `page_size`: Itens por página (padrão: 10, máximo: 50)

**Exemplo de Consulta Combinada:**
```http
GET /api/tarefas/?status_tarefa=pendente&prioridade=alta&ordering=data_vencimento&page=1&page_size=20
```

---

## Processamento Assíncrono com Celery

O projeto emprega o **Celery** orquestrado com **Redis** para tarefas que exigem execução fora do ciclo de vida da requisição HTTP.

### Tasks Implementadas

#### 1. Notificação de Vencimento Próximo (`tarefas.tasks.notificar_tarefa_proxima_vencimento`)
- **Tipo**: Task Assíncrona.
- **Gatilho**: Disparada automaticamente no `TarefaService` quando uma tarefa é criada ou atualizada com `data_vencimento` dentro das próximas 24 horas (hoje ou amanhã) e status diferente de `concluida` ou `vencida`.
- **Ação**: Executa em background, registra log formatado e conta com ponto de extensão preparado para envio de e-mails transacionais (SMTP/SendGrid/SES).

#### 2. Rotina Diária de Tarefas Vencidas (`tarefas.tasks.verificar_tarefas_vencidas`)
- **Tipo**: Task Periódica agendada via Celery Beat.
- **Frequência**: Executada diariamente às `00:05` (meia-noite e cinco).
- **Ação**: Localiza tarefas com data de vencimento anterior ao dia atual (`data_vencimento < hoje`) que não estejam concluídas e atualiza seus status em lote para **`vencida`**.

### Como Testar e Acompanhar o Celery

1. **Acompanhar os logs do Celery Worker em tempo real:**
   ```bash
   docker compose logs -f celery_worker
   ```
2. **Acompanhar o Celery Beat:**
   ```bash
   docker compose logs -f celery_beat
   ```
3. **Disparo Manual via Django Shell:**
   ```bash
   docker compose exec web python manage.py shell -c "
   from tarefas.tasks import verificar_tarefas_vencidas
   print('Tarefas vencidas atualizadas:', verificar_tarefas_vencidas())
   "
   ```

---

## Testes Automatizados e Cobertura

A suíte de testes utiliza **Pytest**, **pytest-django**, **pytest-cov** e **factory_boy**, alcançando **98% de cobertura geral** e **100% de cobertura nas regras de negócio**.

### Como Executar os Testes

```bash
# Executa todos os 102 testes e exibe relatório de cobertura no terminal
docker compose exec web pytest

# Gerar relatório HTML de cobertura (em htmlcov/)
docker compose exec web pytest --cov-report=html

# Executar testes apenas do módulo de usuários
docker compose exec web pytest apps/usuarios/

# Executar testes apenas do módulo de tarefas
docker compose exec web pytest apps/tarefas/

# Executar com o runner nativo do Django
docker compose exec web python manage.py test usuarios tarefas
```

### Relatório de Cobertura de Código (`pytest --cov`)

```text
================================ tests coverage ================================
Name                                                         Stmts   Miss  Cover
--------------------------------------------------------------------------------
apps/tarefas/filters.py                                         10      0   100%
apps/tarefas/models.py                                          26      0   100%
apps/tarefas/pagination.py                                       5      0   100%
apps/tarefas/repositories.py                                    25      0   100%
apps/tarefas/serializers.py                                      7      0   100%
apps/tarefas/services.py                                        38      0   100%
apps/tarefas/tasks.py (Celery)                                  23      0   100%
apps/tarefas/views.py                                           68      3    96%
apps/usuarios/models.py                                         12      0   100%
apps/usuarios/repositories.py                                   31      0   100%
apps/usuarios/serializers.py                                    20      0   100%
apps/usuarios/services.py                                       36      0   100%
apps/usuarios/views.py                                          43      0   100%
--------------------------------------------------------------------------------
TOTAL                                                         1076     22    98%
============================= 102 passed in 6.67s ==============================
```

### Linter e Padronização PEP 8
O projeto utiliza o **Ruff** para garantir conformidade estrita com o PEP 8:
```bash
docker compose exec web ruff check .
```

---

## Licença

Distribuído sob a licença **MIT**. Consulte o arquivo `LICENSE` para mais informações.

---

Desenvolvido por **[Jhone](https://github.com/JhoneLabs)**.
