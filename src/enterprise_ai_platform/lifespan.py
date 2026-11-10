"""
Application lifespan manager.

Handles startup and shutdown events:
  1. Initialise structured logging
  2. Initialise database connection pool
  3. Initialise LLM providers (Azure OpenAI)
  4. Initialise LlamaIndex services (indexes, retrievers)
  5. Initialise LangGraph checkpointer
  6. Compile and register LangGraph workflows
  7. Begin accepting requests

On shutdown, resources are released in reverse order.
"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI

from enterprise_ai_platform.core.logging import setup_logging
from enterprise_ai_platform.core.telemetry import setup_telemetry
from enterprise_ai_platform.infrastructure.database.connection_manager import close_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # --- startup ---
    setup_logging()
    setup_telemetry(app)
    yield
    # --- shutdown ---
    await close_engine()
