"""
Application lifespan manager.

Handles startup and shutdown events:
  1. Initialise database connection pool
  2. Initialise LLM providers (Azure OpenAI)
  3. Initialise LlamaIndex services (indexes, retrievers)
  4. Initialise LangGraph checkpointer
  5. Compile and register LangGraph workflows
  6. Begin accepting requests

On shutdown, resources are released in reverse order.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    # TODO: initialise DB, LLM providers, LlamaIndex, checkpointer, graphs
    yield
    # --- shutdown ---
    # TODO: close connections and release resources
