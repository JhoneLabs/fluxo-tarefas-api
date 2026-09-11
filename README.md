# fluxo-tarefas-api

API REST para gerenciamento de fluxo de tarefas desenvolvida com Django REST Framework.

## Stack Utilizada

- **Python 3.12**
- **Django 5.1** & **Django REST Framework**
- **SimpleJWT** (Autenticação baseada em JSON Web Tokens com blacklist)
- **django-filter** (Filtragem dinâmica e ordenação de recursos)
- **PostgreSQL 16** (Banco de dados relacional)
- **Redis 7** (Cache e mensageria)
- **Docker & Docker Compose** (Containerização do ambiente)
- **django-environ** (Gerenciamento de configurações e variáveis de ambiente)
- **django-cors-headers** (Controle de CORS)

## Estrutura do Projeto

O projeto adota uma arquitetura em camadas dentro de cada app (`views/controllers` → `services` → `repositories`), mantendo baixo acoplamento e facilidade de testes:

```text
fluxo-tarefas-api/
├── apps/
│   ├── usuarios/         # App de usuários e autenticação
│   │   ├── migrations/
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   └── test_auth.py
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py       # Modelo Usuario (AbstractUser)
│   │   ├── repositories.py # Camada de acesso a dados (ORM)
│   │   ├── serializers.py  # Validação e serialização
│   │   ├── services.py     # Camada de regras de negócio
│   │   ├── urls.py         # Rotas da API de usuários
│   │   └── views.py        # Controllers / Handlers HTTP
│   └── tarefas/          # App de tarefas
│       ├── migrations/
│       ├── tests/
│       │   ├── __init__.py
│       │   └── test_tarefas.py
│       ├── __init__.py
│       ├── apps.py
│       ├── filters.py      # Filtros com django-filter
│       ├── models.py       # Modelo Tarefa (com status e prioridade)
│       ├── pagination.py   # Paginação customizada com page_size
│       ├── repositories.py # Consultas e persistência isoladas por owner
│       ├── serializers.py  # Validação e serialização
│       ├── services.py     # Regras de negócio e proteção 404
│       ├── urls.py         # Rotas da API de tarefas
│       └── views.py        # Controllers / Handlers HTTP
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

### 4. Executar Migrações

Em um novo terminal (com os containers rodando):

```bash
docker compose exec web python manage.py migrate
```

### 5. Executar os Testes Automatizados

```bash
docker compose exec web python manage.py test usuarios tarefas
```

---

## Endpoints de Autenticação e Usuários

Todas as rotas de usuários estão sob o prefixo `/api/usuarios/`.

| Método | Endpoint | Descrição | Autenticação |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/usuarios/cadastro/` | Cria um novo usuário | Pública |
| `POST` | `/api/usuarios/login/` | Autentica e retorna tokens (access e refresh) | Pública |
| `POST` | `/api/usuarios/refresh/` | Renova o token de acesso | Pública |
| `POST` | `/api/usuarios/logout/` | Invalida o token de refresh (blacklist) | `Bearer <access_token>` |
| `GET` | `/api/usuarios/me/` | Retorna o perfil do usuário autenticado | `Bearer <access_token>` |

### Exemplos de Autenticação

#### 1. Cadastro de Usuário (`POST /api/usuarios/cadastro/`)
```json
{
  "username": "jhone_dev",
  "email": "jhone@example.com",
  "password": "SenhaForte123!@#",
  "first_name": "Jhone",
  "last_name": "Rodrigues"
}
```

#### 2. Login (`POST /api/usuarios/login/`)
```json
{
  "username": "jhone_dev",
  "password": "SenhaForte123!@#"
}
```
**Resposta:**
```json
{
  "access": "<JWT_ACCESS_TOKEN>",
  "refresh": "<JWT_REFRESH_TOKEN>"
}
```

#### 3. Obter Perfil (`GET /api/usuarios/me/`)
**Headers:**
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

---

## Endpoints de Tarefas

Todas as rotas de tarefas estão sob o prefixo `/api/tarefas/` e exigem autenticação JWT (`Authorization: Bearer <access_token>`).

> **Isolamento por Proprietário (Owner)**: O usuário autenticado só pode visualizar, alterar ou excluir suas próprias tarefas. Qualquer tentativa de manipular tarefas pertencentes a outro usuário resultará em **HTTP 404 (Not Found)** para evitar o vazamento da existência de registros alheios.

| Método | Endpoint | Descrição | Autenticação |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/tarefas/` | Lista tarefas do usuário (com paginação, filtros e ordenação) | `Bearer <access_token>` |
| `POST` | `/api/tarefas/` | Cria uma nova tarefa vinculada ao usuário | `Bearer <access_token>` |
| `GET` | `/api/tarefas/{id}/` | Detalhes de uma tarefa específica do usuário | `Bearer <access_token>` |
| `PATCH` | `/api/tarefas/{id}/` | Atualização parcial de tarefa | `Bearer <access_token>` |
| `PUT` | `/api/tarefas/{id}/` | Atualização completa de tarefa | `Bearer <access_token>` |
| `DELETE` | `/api/tarefas/{id}/` | Exclusão de tarefa | `Bearer <access_token>` |

### Valores Válidos para Campos

- **`status_tarefa`**: `pendente` *(padrão)*, `em_andamento`, `concluida`
- **`prioridade`**: `baixa`, `media` *(padrão)*, `alta`

---

### Filtros, Ordenação e Paginação (`GET /api/tarefas/`)

O endpoint de listagem conta com suporte a filtros combináveis, ordenação e paginação padrão do Django REST Framework:

#### 1. Filtros Disponíveis (via Query Params)
- **`status_tarefa`**: Filtro exato (`pendente`, `em_andamento`, `concluida`).
- **`prioridade`**: Filtro exato (`baixa`, `media`, `alta`).
- **`data_vencimento_inicio`**: Filtra tarefas com data de vencimento maior ou igual à data fornecida (`YYYY-MM-DD`).
- **`data_vencimento_fim`**: Filtra tarefas com data de vencimento menor ou igual à data fornecida (`YYYY-MM-DD`).

*Todos os filtros podem ser combinados livremente entre si.*

#### 2. Ordenação (`ordering`)
Permite ordenar de forma ascendente ou descendente (prefixando com `-`) pelos seguintes campos:
- `data_vencimento` / `-data_vencimento`
- `data_criacao` / `-data_criacao`
- `prioridade` / `-prioridade`

*Ordenação padrão*: `-data_criacao` (tarefas mais recentes primeiro).

#### 3. Paginação (`page` e `page_size`)
- Tamanho de página padrão: **10** itens.
- Parâmetro `page`: Número da página solicitada (ex: `?page=2`).
- Parâmetro `page_size`: Permite que o cliente altere a quantidade de itens por página (ex: `?page_size=20`).
- **Limite Máximo**: O parâmetro `page_size` é limitado a no máximo **50** itens por página.

#### Exemplos de Consultas:

- **Filtrar apenas por status:**
  ```http
  GET /api/tarefas/?status_tarefa=pendente
  ```

- **Filtrar por prioridade e ordenar por vencimento:**
  ```http
  GET /api/tarefas/?prioridade=alta&ordering=data_vencimento
  ```

- **Filtro combinado (status + prioridade) com ordenação mais recente:**
  ```http
  GET /api/tarefas/?status_tarefa=em_andamento&prioridade=alta&ordering=-data_criacao
  ```

- **Filtrar por intervalo de vencimento com paginação customizada:**
  ```http
  GET /api/tarefas/?data_vencimento_inicio=2026-09-01&data_vencimento_fim=2026-09-30&page=1&page_size=25
  ```

---

### Exemplos de Requisição de Tarefas

#### 1. Criar Tarefa (`POST /api/tarefas/`)
**Headers:**
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
Content-Type: application/json
```
**Payload:**
```json
{
  "titulo": "Finalizar módulo de autenticação",
  "descricao": "Configurar expiração e rotação de JWT no settings",
  "status_tarefa": "pendente",
  "prioridade": "alta",
  "data_vencimento": "2026-09-15"
}
```
**Resposta (HTTP 201 Created):**
```json
{
  "id": 1,
  "titulo": "Finalizar módulo de autenticação",
  "descricao": "Configurar expiração e rotação de JWT no settings",
  "status_tarefa": "pendente",
  "prioridade": "alta",
  "data_vencimento": "2026-09-15",
  "data_criacao": "2026-09-08T09:40:24.189658-03:00",
  "data_atualizacao": "2026-09-08T09:40:24.189665-03:00"
}
```

#### 2. Listar Tarefas Paginadas (`GET /api/tarefas/?page=1&page_size=10`)
**Resposta (HTTP 200 OK):**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "titulo": "Finalizar módulo de autenticação",
      "descricao": "Configurar expiração e rotação de JWT no settings",
      "status_tarefa": "pendente",
      "prioridade": "alta",
      "data_vencimento": "2026-09-15",
      "data_criacao": "2026-09-08T09:40:24.189658-03:00",
      "data_atualizacao": "2026-09-08T09:40:24.189665-03:00"
    }
  ]
}
```

#### 3. Atualizar Status (`PATCH /api/tarefas/{id}/`)
**Payload:**
```json
{
  "status_tarefa": "concluida"
}
```
**Resposta (HTTP 200 OK):**
```json
{
  "id": 1,
  "titulo": "Finalizar módulo de autenticação",
  "descricao": "Configurar expiração e rotação de JWT no settings",
  "status_tarefa": "concluida",
  "prioridade": "alta",
  "data_vencimento": "2026-09-15",
  "data_criacao": "2026-09-08T09:40:24.189658-03:00",
  "data_atualizacao": "2026-09-08T09:45:10.123456-03:00"
}
```

#### 4. Deletar Tarefa (`DELETE /api/tarefas/{id}/`)
**Resposta (HTTP 204 No Content)**
