# task-flow-api

API REST para gerenciamento de tarefas com autenticação de usuários.

## Sobre o projeto

O task-flow-api é uma API construída com foco em boas práticas de desenvolvimento backend. O objetivo é oferecer uma base sólida para gerenciamento de tarefas, com autenticação segura, documentação completa e cobertura de testes.

## Tecnologias

- Python & Django
- Django REST Framework
- PostgreSQL
- SimpleJWT
- Celery + Redis
- Docker & Docker Compose
- Pytest

## Funcionalidades

- Cadastro e autenticação de usuários com JWT
- Refresh token e controle de sessão
- CRUD completo de tarefas
- Filtros por status, prioridade e data
- Documentação automática via Swagger
- Testes unitários e de integração

## Arquitetura

O projeto segue uma arquitetura em camadas, separando responsabilidades entre Controllers, Services e Repositories. Cada módulo (users, tasks) é isolado dentro da pasta `apps/`.

## Como rodar

```bash
git clone https://github.com/sua-org/task-flow-api
cd task-flow-api
cp .env.example .env
docker compose up --build
```

A API estará disponível em `http://localhost:8000` e a documentação em `http://localhost:8000/api/docs`.
