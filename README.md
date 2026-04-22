# Agendamentos Nagini

## Sobre o projeto

Este projeto é um **protótipo funcional** para um sistema de conexão entre **clientes** e **prestadores de serviços a domicílio**.

A implementação segue princípios de:
- **Clean Architecture**
- **DDD (Domain-Driven Design)**
- **TDD (Test-Driven Development)**

---

## Tecnologias utilizadas

- **Python 3.9+**
- **FastAPI**
- **Uvicorn**
- **SQLAlchemy**
- **PostgreSQL**
- **PgAdmin**
- **Pydantic**
- **Pytest**
- **HTTPX**
- **Strawberry GraphQL**
- **python-jose** (JWT)
- **passlib**
- **slowapi**
- **Docker**
- **Docker Compose**
- **debugpy**

---

## Árvore arquitetural (pastas)

```text
Agendamentos_Nagini/
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
├── README.md
└── src/
    ├── domain/
    │   ├── __seedwork/
    │   ├── logistics/
    │   ├── notification/
    │   ├── payment/
    │   ├── security/
    │   ├── service/
    │   ├── service_request/
    │   ├── travel/
    │   └── user/
    ├── usecases/
    │   ├── service/
    │   ├── service_request/
    │   └── user/
    ├── infrastructure/
    │   ├── api/
    │   ├── logistics/
    │   ├── notification/
    │   ├── payment/
    │   ├── presenters/
    │   ├── security/
    │   ├── service/
    │   ├── service_request/
    │   ├── travel/
    │   └── user/
    ├── tests/
    │   ├── domain/
    │   ├── fakes/
    │   ├── infrastructure/
    │   ├── payment/
    │   └── usecases/
    └── pytest.ini
```

---

## Como executar o projeto

### 1) Pré-requisitos

- Docker e Docker Compose
- (Opcional para execução local) Python 3.9+

---

### 2) Executando com Docker (recomendado)

1. No diretório raiz do projeto, configure as variáveis de ambiente necessárias (exemplo em `.env`):

```env
CONNECTION=postgresql+psycopg2://postgres:postgres@postgres:5432/db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=db
EMAIL_SENDER_ADDRESS=seu_email@provedor.com
EMAIL_SENDER_PASSWORD=sua_senha
CHAVE_SECRETA=uma_chave_secreta_forte
ALGORITMO=HS256
TEMPO_DE_EXPIRACAO_SOLICITACAO=60
TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO=30
```

2. Suba os containers:

```bash
docker compose up --build
```

3. A API ficará disponível em:

- `http://localhost:8000`

4. PgAdmin (quando necessário):

- `http://localhost:16543`
- Usuário padrão: `admin@admin.com`
- Senha padrão: `123456`

---

### 3) Executando localmente (sem Docker)

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Exporte as variáveis de ambiente obrigatórias:

```bash
export CONNECTION='sqlite://'
export CHAVE_SECRETA='test-secret-key'
export ALGORITMO='HS256'
export TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO='30'
export TEMPO_DE_EXPIRACAO_SOLICITACAO='60'
```

3. Inicie a API a partir da raiz do repositório:

```bash
uvicorn infrastructure.api.main:app --app-dir src --host 0.0.0.0 --port 8000 --reload
```

---

### 4) Executando os testes

Com as variáveis de ambiente configuradas:

```bash
CONNECTION='sqlite://' \
CHAVE_SECRETA='test-secret-key' \
ALGORITMO='HS256' \
TEMPO_DE_EXPIRACAO_TOKEN_DE_ACESSO='30' \
TEMPO_DE_EXPIRACAO_SOLICITACAO='60' \
python -m pytest -q
```

---

## Status

Projeto em evolução contínua, estruturado para crescimento incremental com foco em separação de responsabilidades, testabilidade e domínio de negócio.
