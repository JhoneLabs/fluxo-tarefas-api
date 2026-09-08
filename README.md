# fluxo-tarefas-api

API REST para gerenciamento de fluxo de tarefas desenvolvida com Django REST Framework.

## Stack Utilizada

- **Python 3.12**
- **Django 5.1** & **Django REST Framework**
- **SimpleJWT** (Autenticação baseada em JSON Web Tokens com blacklist)
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
│   └── usuarios/         # App de usuários e autenticação
│       ├── migrations/
│       ├── tests/
│       │   ├── __init__.py
│       │   └── test_auth.py
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py       # Modelo Usuario (AbstractUser)
│       ├── repositories.py # Camada de acesso a dados (ORM)
│       ├── serializers.py  # Validação e serialização
│       ├── services.py     # Camada de regras de negócio
│       ├── urls.py         # Rotas da API de usuários
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
docker compose exec web python manage.py test usuarios
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

### Exemplos de Requisição

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
**Resposta:**
```json
{
  "id": 1,
  "username": "jhone_dev",
  "email": "jhone@example.com",
  "first_name": "Jhone",
  "last_name": "Rodrigues",
  "data_criacao": "2026-09-08T09:34:04.189658-03:00",
  "data_atualizacao": "2026-09-08T09:34:04.189665-03:00"
}
```

#### 4. Renovar Access Token (`POST /api/usuarios/refresh/`)
```json
{
  "refresh": "<JWT_REFRESH_TOKEN>"
}
```

#### 5. Logout (`POST /api/usuarios/logout/`)
**Headers:**
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```
**Payload:**
```json
{
  "refresh": "<JWT_REFRESH_TOKEN>"
}
```
