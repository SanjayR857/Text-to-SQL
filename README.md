# Enterprise AI Platform

A production-grade, enterprise-ready AI platform built on **FastAPI**, **LangGraph**, and **LlamaIndex**. It enables secure, governed, multi-modal question answering over both structured databases (Text-to-SQL) and unstructured document repositories (Document RAG), with full support for Microsoft Entra ID authentication, role-based access control, and row-level security.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Framework Responsibility Table](#3-framework-responsibility-table)
4. [Layer Descriptions](#4-layer-descriptions)
5. [Authorization Model](#5-authorization-model)
6. [API Endpoint Reference](#6-api-endpoint-reference)
7. [Application Startup Lifecycle](#7-application-startup-lifecycle)
8. [Getting Started](#8-getting-started)
9. [Configuration](#9-configuration)
10. [Testing](#10-testing)
11. [Directory Structure](#11-directory-structure)

---

## 1. Project Overview

The Enterprise AI Platform provides a unified API for:

| Capability | Description |
|---|---|
| **Text-to-SQL** | Translate natural-language questions into SQL, execute against registered databases, and return governed results |
| **Document RAG** | Ingest, chunk, embed, and semantically retrieve enterprise documents (PDF, DOCX, XLSX) |
| **Hybrid RAG** | Combine structured and unstructured retrieval within a single query |
| **Conversational AI** | Stateful, multi-turn chat with persistent conversation history (LangGraph checkpoints) |
| **Security & Governance** | Entra ID authentication, RBAC, vertical access control, row-level security, PII detection, prompt-injection defence |

---

## 2. Architecture Diagram

```mermaid
flowchart TD
    Client([Client / Frontend]) -->|HTTPS| API[FastAPI Presentation Layer]

    API --> Auth[Auth Middleware\nEntra ID / JWT]
    API --> RID[Request ID Middleware]
    API --> LOG[Request Logging Middleware]
    API --> SEC[Security Headers Middleware]

    API -->|Dependency Injection| UC[Application Layer\nUse Cases]

    UC --> ORCH[Orchestration Layer\nLangGraph Graphs]

    ORCH --> NODES[Graph Nodes]
    NODES --> ROUT[Intent Classifier\nQuery Router]
    NODES --> AUTHZ[Identity Node\nPermission Node]
    NODES --> SQL[Text-to-SQL Nodes]
    NODES --> DOCRAG[Document RAG Nodes]
    NODES --> COMMON[Response Node\nError Node]

    ORCH --> CP[Checkpoint Store\nPostgreSQL]

    UC --> INT[Integration Layer]
    INT --> LGI[LangGraph\nGraph Factory / Runtime]
    INT --> LLI[LlamaIndex\nReaders / Indexes / Retrievers]
    INT --> LCI[LangChain\nLLM / Embedding Adapters]

    INT --> INFRA[Infrastructure Layer]
    INFRA --> DB[(PostgreSQL\npgvector)]
    INFRA --> AIS[(Azure AI Search)]
    INFRA --> AOI[Azure OpenAI\nChat + Embeddings]
    INFRA --> BLOB[Azure Blob Storage]
    INFRA --> REDIS[(Redis Cache)]
    INFRA --> EVENTS[Event Publisher\nBackground Workers]

    UC --> SEC2[Security Layer]
    SEC2 --> RBAC[RBAC Engine]
    SEC2 --> RLS[Row-Level Security]
    SEC2 --> GR[Guardrails\nSQL / PII / PromptInject]
```

---

## 3. Framework Responsibility Table

| Framework | Version | Responsibility |
|---|---|---|
| **FastAPI** | ≥ 0.115 | HTTP API layer: routing, middleware, dependency injection, OpenAPI documentation |
| **LangGraph** | ≥ 0.2 | Stateful, multi-step AI workflow orchestration with persistent checkpointing |
| **LlamaIndex** | ≥ 0.11 (core) | Document ingestion, chunking, vector indexing, and semantic retrieval |
| **LangChain OpenAI** | ≥ 0.2 | Adapters for Azure OpenAI chat models and embedding models |
| **SQLAlchemy** | ≥ 2.0 | Async ORM and connection pooling for PostgreSQL |
| **pgvector** | ≥ 0.3 | PostgreSQL vector similarity search extension |
| **Azure AI Search** | SDK ≥ 12 | Managed vector and hybrid search at scale |
| **Pydantic v2** | ≥ 2.7 | Request/response schema validation and settings management |
| **structlog** | ≥ 24 | Structured, context-rich JSON logging |
| **OpenTelemetry** | ≥ 1.25 | Distributed tracing and metrics for observability |
| **Redis** | ≥ 5.0 | Token caching, query result caching, schema metadata caching |
| **Alembic** | ≥ 1.13 | Database schema migrations |

---

## 4. Layer Descriptions

### Presentation Layer (`api/`)

The FastAPI presentation layer is responsible for:

- **Routing** – Seven routers covering health, auth, chat, documents, databases, conversations, and admin endpoints.
- **Middleware** – Request ID propagation, structured logging, and security header injection applied in ASGI order.
- **Schemas** – Pydantic v2 models for all request/response bodies; strict validation at the API boundary.
- **Dependencies** – FastAPI `Depends()` providers for authentication context, database sessions, and service instances.
- **Exception Handlers** – Global handlers mapping domain exceptions to RFC 7807 Problem Details responses.

### Application Layer (`application/`)

Implements the **hexagonal architecture** (ports and adapters) pattern:

- **Use Cases** – Single-responsibility orchestrators that express business workflows in framework-agnostic code.
- **Services** – Reusable business logic building blocks consumed by use cases (e.g., SQL generation, schema retrieval).
- **Interfaces (Ports)** – Abstract base classes defining contracts for every external dependency (LLM, embeddings, vector store, SQL executor, checkpoint store, etc.).

No framework-specific code lives in this layer. All external dependencies are injected via their interface contracts.

### Orchestration Layer (`orchestration/`)

Implements multi-step AI workflows using **LangGraph**:

- **State** – Typed `TypedDict` state definitions for each workflow (chat, text-to-SQL, document RAG).
- **Graphs** – Compiled `StateGraph` instances for each workflow variant.
- **Nodes** – Individual computation units grouped by domain: routing, authorization, text-to-SQL, document RAG, and shared response/error handling.
- **Edges** – Conditional and static edge functions that control workflow routing.
- **Checkpoint** – PostgreSQL-backed checkpointer enabling durable, resumable conversation state.
- **Registry** – A runtime registry that holds compiled graph instances and resolves them by workflow type.

### Integration Layer (`integrations/`)

Bridges the application layer to specific frameworks:

- **LangGraph** – Graph factory, runtime invocation, and callback hooks for telemetry.
- **LlamaIndex** – Document readers (PDF, DOCX, XLSX), transformation pipeline, vector index management, and retriever adapters.
- **LangChain** – Thin adapters wrapping `AzureChatOpenAI` and `AzureOpenAIEmbeddings` to satisfy application interface contracts.

### Infrastructure Layer (`infrastructure/`)

Concrete adapter implementations for all external technologies:

| Sub-package | Technology | Purpose |
|---|---|---|
| `database/` | PostgreSQL + SQLAlchemy | ORM models, repositories, session factory |
| `retrieval/pgvector/` | pgvector | Vector similarity search repository |
| `retrieval/azure_ai_search/` | Azure AI Search | Managed search index client |
| `llm/azure_openai/` | Azure OpenAI | Chat completion and embedding API calls |
| `document_processing/` | Docling / OCR | File parsing and text extraction |
| `storage/` | Azure Blob / Local FS | Binary document persistence |
| `cache/` | Redis | Key-value caching |
| `messaging/` | Event Publisher | Background job dispatch |

### Security Layer (`security/`)

Cross-cutting security concerns applied at multiple layers:

- **Authentication** – Microsoft Entra ID token validation; JWT signature verification and claims extraction.
- **Authorization** – RBAC engine for role-based resource access; policy engine for attribute-based decisions.
- **Row-Level Security** – RLS context propagation and predicate injection into SQL queries.
- **Guardrails** – SQL injection detection, PII identification and redaction, prompt injection defence.

---

## 5. Authorization Model

The platform implements a four-tier authorization model:

| Tier | Actors | Scope | Description |
|---|---|---|---|
| **Self** | End users | Own data only | Users can read and modify their own conversations, uploaded documents, and preferences |
| **Vertical** | Business unit members | Column/attribute level | Access to specific columns or attributes within a dataset, enforced by the vertical access service |
| **Chief** | Data stewards, managers | Row-level filtered | Full table access with row-level security filters applied based on group membership |
| **Admin** | Platform administrators | Unrestricted | Full platform access including user management, system configuration, and audit logs |

Authorization decisions are enforced at every layer:
1. **API** – JWT claims validated in middleware; role membership checked in route dependencies.
2. **Application** – Use cases invoke the `AuthorizeDataAccess` use case before executing queries.
3. **Orchestration** – The `PermissionNode` in every graph enforces RBAC and injects RLS context.
4. **Infrastructure** – RLS predicates are appended to all SQL queries via the `RlsContext`.

---

## 6. API Endpoint Reference

All endpoints are prefixed with `/api/v1`.

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/health/live` | Kubernetes liveness probe |
| `GET` | `/api/v1/health/ready` | Kubernetes readiness probe (checks DB, Redis, Azure) |

### Authentication

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/token` | Exchange Entra ID token for platform session token |
| `POST` | `/api/v1/auth/refresh` | Refresh an expiring session token |
| `DELETE` | `/api/v1/auth/logout` | Invalidate the current session token |

### Chat

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/chat` | Execute a single-turn chat request; returns a complete response |
| `POST` | `/api/v1/chat/stream` | Execute a streaming chat request; returns an SSE stream of token deltas |

### Conversations

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/conversations` | List all conversations for the authenticated user |
| `GET` | `/api/v1/conversations/{id}` | Retrieve a conversation and its full message history |
| `DELETE` | `/api/v1/conversations/{id}` | Delete a conversation and all associated state |

### Documents

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/documents` | Upload and ingest a new document (PDF, DOCX, XLSX) |
| `GET` | `/api/v1/documents` | List all documents accessible to the authenticated user |
| `GET` | `/api/v1/documents/{id}` | Retrieve document metadata and status |
| `DELETE` | `/api/v1/documents/{id}` | Delete a document and remove it from all indexes |
| `POST` | `/api/v1/documents/search` | Semantic search across the document knowledge base |

### Databases (Text-to-SQL)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/databases` | Register a new structured data source |
| `GET` | `/api/v1/databases` | List all registered databases accessible to the user |
| `GET` | `/api/v1/databases/{id}` | Retrieve database metadata and schema summary |
| `DELETE` | `/api/v1/databases/{id}` | Deregister a data source |
| `POST` | `/api/v1/databases/{id}/query` | Execute a natural-language query against a registered database |

### Admin

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/admin/users` | List platform users |
| `POST` | `/api/v1/admin/users` | Create a new platform user |
| `PATCH` | `/api/v1/admin/users/{id}` | Update user role assignments |
| `DELETE` | `/api/v1/admin/users/{id}` | Deactivate a user account |
| `GET` | `/api/v1/admin/stats` | Platform usage statistics |

---

## 7. Application Startup Lifecycle

The platform follows a deterministic startup sequence managed by the FastAPI lifespan context manager (`lifespan.py`):

```
1. Load Settings (pydantic-settings / .env)
        │
2. Configure Structured Logging (structlog)
        │
3. Initialise OpenTelemetry Tracing & Metrics
        │
4. Create SQLAlchemy Async Engine & Connection Pool
        │
5. Run Alembic Migrations (if configured)
        │
6. Connect to Redis Cache
        │
7. Initialise Azure OpenAI Client (Chat + Embeddings)
        │
8. Configure LlamaIndex Settings (LLM, embed model, service context)
        │
9. Load / Build LlamaIndex Indexes (pgvector / Azure AI Search)
        │
10. Initialise LangGraph PostgreSQL Checkpointer
        │
11. Compile LangGraph Workflow Graphs
            ├── ChatGraph
            ├── TextToSQLGraph
            ├── DocumentRAGGraph
            └── HybridRAGGraph
        │
12. Register Graphs in GraphRegistry
        │
13. ✅ Begin accepting HTTP requests
```

**Shutdown** (reverse order):

```
1. Stop accepting new requests
2. Wait for in-flight requests to complete (graceful drain)
3. Close LangGraph checkpointer connection
4. Close Redis connection pool
5. Dispose SQLAlchemy engine
6. Flush OpenTelemetry spans
```

---

## 8. Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Access to an Azure subscription with:
  - Azure OpenAI (GPT-4o + text-embedding-3-large deployments)
  - Azure AI Search
  - Azure Blob Storage
  - Microsoft Entra ID application registration

### Installation

#### With `uv` (recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install all dependencies
uv pip install -e ".[dev]"
```

#### With `pip`

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env with your Azure credentials and connection strings
```

### Run Locally

```bash
# Start infrastructure (PostgreSQL + Redis)
docker compose up postgres redis -d

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn enterprise_ai_platform.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### Run with Docker

```bash
# Build and start all services
docker compose up --build

# Run migrations inside the container
docker compose exec api alembic upgrade head
```

---

## 9. Configuration

### Environment Variables

All settings are defined in `src/enterprise_ai_platform/core/config.py` and loaded from environment variables or `.env`.

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `Enterprise AI Platform` | Application display name |
| `APP_VERSION` | `0.1.0` | Application version |
| `DEBUG` | `false` | Enable debug mode |
| `DATABASE_URL` | — | PostgreSQL connection string |
| `AZURE_OPENAI_ENDPOINT` | — | Azure OpenAI resource endpoint |
| `AZURE_OPENAI_API_KEY` | — | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | — | Chat model deployment name |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | — | Embedding model deployment name |
| `AZURE_SEARCH_ENDPOINT` | — | Azure AI Search endpoint |
| `AZURE_SEARCH_API_KEY` | — | Azure AI Search admin key |
| `AZURE_SEARCH_INDEX_NAME` | — | Default search index name |
| `AZURE_BLOB_CONNECTION_STRING` | — | Azure Blob Storage connection string |
| `AZURE_BLOB_CONTAINER` | `documents` | Blob container name |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `ENTRA_TENANT_ID` | — | Microsoft Entra ID tenant ID |
| `ENTRA_CLIENT_ID` | — | Entra application (client) ID |
| `ENTRA_CLIENT_SECRET` | — | Entra client secret |

### YAML Configuration Files

Environment-specific YAML files in `config/` override defaults at runtime:

| File | Environment | Key Settings |
|---|---|---|
| `development.yaml` | Local development | `debug: true`, small pool sizes, low concurrency |
| `staging.yaml` | Staging / QA | `debug: false`, medium pool sizes |
| `production.yaml` | Production | `debug: false`, large pool sizes, max concurrency |

---

## 10. Testing

### Run All Tests

```bash
pytest
```

### Run Specific Suites

```bash
# Unit tests only
pytest tests/unit -v

# Integration tests (requires running PostgreSQL and Redis)
pytest tests/integration -v

# Architecture tests (dependency rule enforcement)
pytest tests/architecture -v

# Security tests
pytest tests/security -v

# Orchestration / LangGraph tests
pytest tests/orchestration -v

# End-to-end tests (requires full stack)
pytest tests/e2e -v
```

### Coverage Report

```bash
pytest --cov=src/enterprise_ai_platform --cov-report=html
open htmlcov/index.html
```

### Linting and Type Checking

```bash
# Lint and format
ruff check src/ tests/
ruff format src/ tests/

# Static type checking
mypy src/
```

---

## 11. Directory Structure

```
Text-to-SQL/                               # Project root
├── src/
│   └── enterprise_ai_platform/            # Python package root
│       ├── main.py                        # FastAPI app entry point
│       ├── lifespan.py                    # Startup / shutdown lifecycle
│       │
│       ├── api/                           # Presentation layer
│       │   ├── dependencies.py            # FastAPI DI providers
│       │   ├── exception_handlers.py      # Global error handling
│       │   ├── middleware/                # ASGI middleware
│       │   │   ├── request_id.py          #   Request ID propagation
│       │   │   ├── logging.py             #   Structured request logging
│       │   │   └── security_headers.py    #   Security response headers
│       │   ├── routes/                    # API routers
│       │   │   ├── health.py              #   Liveness / readiness probes
│       │   │   ├── chat.py                #   Chat & streaming endpoints
│       │   │   ├── auth.py                #   Token exchange & logout
│       │   │   ├── documents.py           #   Document CRUD & search
│       │   │   ├── databases.py           #   Database registration & query
│       │   │   ├── conversations.py       #   Conversation management
│       │   │   └── admin.py               #   Admin / user management
│       │   └── schemas/                   # Pydantic request/response models
│       │       ├── common.py              #   Shared primitives & pagination
│       │       ├── chat.py                #   Chat payloads
│       │       ├── document.py            #   Document payloads
│       │       ├── database.py            #   Database payloads
│       │       ├── conversation.py        #   Conversation payloads
│       │       └── auth.py                #   Auth token payloads
│       │
│       ├── core/                          # Cross-cutting concerns
│       │   ├── config.py                  #   pydantic-settings configuration
│       │   ├── logging.py                 #   structlog setup
│       │   ├── exceptions.py              #   Exception hierarchy
│       │   ├── constants.py               #   Platform constants
│       │   └── telemetry.py               #   OpenTelemetry setup
│       │
│       ├── domain/                        # Domain model (framework-free)
│       │   ├── common/                    #   Shared primitives
│       │   │   ├── entities.py            #     Base entity
│       │   │   └── value_objects.py       #     Base value object
│       │   ├── identity/                  #   User, Role, Permission
│       │   │   ├── user.py
│       │   │   ├── role.py
│       │   │   └── permission.py
│       │   ├── documents/                 #   Document + Chunk entities
│       │   │   ├── document.py
│       │   │   └── chunk.py
│       │   ├── conversations/             #   Conversation + Message entities
│       │   │   ├── conversation.py
│       │   │   └── message.py
│       │   ├── retrieval/                 #   Search value objects
│       │   │   ├── search_result.py
│       │   │   └── retrieval_filter.py
│       │   └── structured_data/           #   Schema, table, SQL entities
│       │       ├── database_schema.py
│       │       ├── table_metadata.py
│       │       └── sql_query.py
│       │
│       ├── application/                   # Use cases & ports (hexagonal)
│       │   ├── interfaces/                #   Abstract ports (8 contracts)
│       │   │   ├── llm_provider.py
│       │   │   ├── embedding_provider.py
│       │   │   ├── vector_store.py
│       │   │   ├── document_parser.py
│       │   │   ├── document_storage.py
│       │   │   ├── retriever.py
│       │   │   ├── sql_executor.py
│       │   │   └── checkpoint_store.py
│       │   ├── chat/
│       │   │   ├── services/              #   Chat business services
│       │   │   └── use_cases/
│       │   │       ├── execute_chat.py
│       │   │       ├── stream_chat.py
│       │   │       └── manage_conversation.py
│       │   ├── structured_data/
│       │   │   ├── services/
│       │   │   │   ├── schema_retrieval.py
│       │   │   │   ├── entity_retrieval.py
│       │   │   │   ├── sql_generation.py
│       │   │   │   └── sql_validation.py
│       │   │   └── use_cases/
│       │   │       ├── execute_text_to_sql.py
│       │   │       └── retrieve_structured_data.py
│       │   ├── document_intelligence/
│       │   │   ├── services/
│       │   │   │   ├── document_ingestion.py
│       │   │   │   ├── document_chunking.py
│       │   │   │   └── document_retrieval.py
│       │   │   └── use_cases/
│       │   │       ├── ingest_document.py
│       │   │       └── search_documents.py
│       │   └── authorization/
│       │       ├── services/
│       │       │   ├── access_policy.py
│       │       │   ├── vertical_access.py
│       │       │   └── row_access.py
│       │       └── use_cases/
│       │           └── authorize_data_access.py
│       │
│       ├── orchestration/                 # LangGraph workflows
│       │   ├── state/
│       │   │   ├── chat_state.py
│       │   │   ├── research_state.py
│       │   │   └── sql_state.py
│       │   ├── graphs/
│       │   │   ├── chat_graph.py
│       │   │   ├── text_to_sql_graph.py
│       │   │   ├── document_rag_graph.py
│       │   │   └── hybrid_rag_graph.py
│       │   ├── nodes/
│       │   │   ├── routing/
│       │   │   │   ├── intent_classifier.py
│       │   │   │   └── query_router.py
│       │   │   ├── authorization/
│       │   │   │   ├── identity_node.py
│       │   │   │   └── permission_node.py
│       │   │   ├── structured_data/
│       │   │   │   ├── schema_retrieval_node.py
│       │   │   │   ├── entity_retrieval_node.py
│       │   │   │   ├── sql_generation_node.py
│       │   │   │   ├── sql_validation_node.py
│       │   │   │   └── sql_execution_node.py
│       │   │   ├── document_rag/
│       │   │   │   ├── document_retrieval_node.py
│       │   │   │   ├── reranking_node.py
│       │   │   │   └── answer_generation_node.py
│       │   │   └── common/
│       │   │       ├── response_node.py
│       │   │       └── error_node.py
│       │   ├── edges/
│       │   │   ├── conditional_edges.py
│       │   │   └── routing_edges.py
│       │   ├── checkpoint/
│       │   │   ├── postgres_checkpointer.py
│       │   │   └── checkpoint_factory.py
│       │   └── registry/
│       │       └── graph_registry.py
│       │
│       ├── integrations/                  # Framework adapters
│       │   ├── langgraph/
│       │   │   ├── graph_factory.py
│       │   │   ├── runtime.py
│       │   │   └── callbacks.py
│       │   ├── llamaindex/
│       │   │   ├── settings.py
│       │   │   ├── readers/
│       │   │   │   ├── pdf_reader.py
│       │   │   │   ├── excel_reader.py
│       │   │   │   └── docx_reader.py
│       │   │   ├── transformations/
│       │   │   │   ├── chunking.py
│       │   │   │   └── metadata_extraction.py
│       │   │   ├── indexes/
│       │   │   │   ├── vector_index.py
│       │   │   │   └── index_manager.py
│       │   │   ├── retrievers/
│       │   │   │   ├── document_retriever.py
│       │   │   │   ├── schema_retriever.py
│       │   │   │   └── hybrid_retriever.py
│       │   │   ├── query_engines/
│       │   │   │   └── document_query_engine.py
│       │   │   └── adapters/
│       │   │       ├── retriever_adapter.py
│       │   │       └── ingestion_adapter.py
│       │   └── langchain/
│       │       ├── llm_adapter.py
│       │       └── embedding_adapter.py
│       │
│       ├── infrastructure/                # Technology adapters
│       │   ├── database/
│       │   │   ├── session.py
│       │   │   ├── models/               #   SQLAlchemy ORM models
│       │   │   ├── repositories/         #   Repository implementations
│       │   │   └── connection_manager.py
│       │   ├── retrieval/
│       │   │   ├── pgvector/
│       │   │   │   ├── vector_store.py
│       │   │   │   └── search_repository.py
│       │   │   └── azure_ai_search/
│       │   │       ├── search_client.py
│       │   │       └── index_manager.py
│       │   ├── llm/
│       │   │   └── azure_openai/
│       │   │       ├── chat_model.py
│       │   │       └── embeddings.py
│       │   ├── document_processing/
│       │   │   ├── docling_parser.py
│       │   │   └── ocr_parser.py
│       │   ├── storage/
│       │   │   ├── azure_blob.py
│       │   │   └── local_storage.py
│       │   ├── cache/
│       │   │   └── redis_cache.py
│       │   └── messaging/
│       │       └── event_publisher.py
│       │
│       ├── security/                      # Security subsystems
│       │   ├── authentication/
│       │   │   ├── entra_id.py
│       │   │   └── jwt_validator.py
│       │   ├── authorization/
│       │   │   ├── rbac_engine.py
│       │   │   └── policy_engine.py
│       │   ├── row_level_security/
│       │   │   ├── rls_context.py
│       │   │   └── rls_policy.py
│       │   └── guardrails/
│       │       ├── sql_guardrails.py
│       │       ├── pii_detection.py
│       │       └── prompt_injection.py
│       │
│       └── workers/                       # Background workers
│           ├── document_worker.py
│           ├── indexing_worker.py
│           └── embedding_worker.py
│
├── frontend/
│   ├── chainlit/                          # Chainlit chat UI
│   └── react/                             # React web application
│
├── migrations/                            # Alembic migration scripts
├── scripts/                               # Utility and deployment scripts
│
├── tests/
│   ├── unit/                              # Isolated unit tests
│   ├── integration/                       # Component integration tests
│   ├── architecture/                      # Dependency rule tests
│   ├── security/                          # Security validation tests
│   ├── orchestration/                     # LangGraph workflow tests
│   └── e2e/                               # End-to-end API tests
│
├── config/
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
│
├── docs/                                  # Extended documentation
├── docker/                                # Dockerfiles
├── docker-compose.yml                     # Local dev stack
├── pyproject.toml                         # Build system & tooling config
├── requirements.txt                       # Pinned dependency list
└── .env.example                           # Environment variable template
```

---

## License

Proprietary — All rights reserved.
