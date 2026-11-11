"""
CLI utility script to synchronize schema embeddings and row-level entity embeddings into pgvector.

Usage:
    python scripts/sync_embeddings.py --all
    python scripts/sync_embeddings.py --schema
    python scripts/sync_embeddings.py --entities
    python scripts/sync_embeddings.py --purge-orphans
"""
import argparse
import asyncio
from pathlib import Path
import sys

# Ensure src/ is on python path for standalone execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy.ext.asyncio import AsyncEngine
import structlog

from core.observability import setup_logging
from core.database import (
    close_engine,
    get_async_engine,
)
from providers.embeddings import AzureOpenAIEmbeddings
from text_to_sql.vector_store.entity_vector_store import (
    EntityVectorStore,
)
from text_to_sql.vector_store.schema_vector_store import (
    SchemaVectorStore,
)
from text_to_sql.workers.embedding_worker import SchemaEmbeddingWorker
from text_to_sql.workers.entity_worker import EntityEmbeddingWorker

logger = structlog.get_logger(__name__)


async def run_sync(
    sync_schema: bool,
    sync_entities: bool,
    purge_orphans: bool,
    database_id: str,
    schema_name: str,
    batch_size: int,
    table_name: str | None = None,
) -> None:
    """Execute embedding synchronization workflows."""
    engine: AsyncEngine = get_async_engine()
    embeddings = AzureOpenAIEmbeddings()

    try:
        if sync_schema:
            schema_store = SchemaVectorStore(engine=engine, embeddings=embeddings)
            schema_worker = SchemaEmbeddingWorker(vector_store=schema_store, engine=engine)
            if table_name:
                logger.info("Starting schema embedding synchronization for single table...", table=table_name)
                synced_schema_docs = await schema_worker.sync_table(
                    table_name=table_name,
                    database_id=database_id,
                    schema_name=schema_name,
                )
            else:
                logger.info("Starting full schema embeddings synchronization...")
                synced_schema_docs = await schema_worker.sync_all_schemas(
                    database_id=database_id,
                    schema_name=schema_name,
                )
            logger.info("Schema embeddings synchronization complete", updated_documents=synced_schema_docs)

        if sync_entities:
            entity_store = EntityVectorStore(engine=engine, embeddings=embeddings)
            entity_worker = EntityEmbeddingWorker(vector_store=entity_store, engine=engine)
            if table_name:
                logger.info("Starting entity value embedding synchronization for single table...", table=table_name)
                synced_entities = await entity_worker.sync_table(
                    table_name=table_name,
                    database_id=database_id,
                    schema_name=schema_name,
                    batch_size=batch_size,
                )
                logger.info("Entity value embedding synchronization complete", table=table_name, updated=synced_entities)
            else:
                logger.info("Starting full entity value embeddings synchronization...")
                results = await entity_worker.sync_all_entities(
                    database_id=database_id,
                    schema_name=schema_name,
                    batch_size=batch_size,
                )
                logger.info("Entity value embeddings synchronization complete", results=results)

                if purge_orphans:
                    logger.info("Checking for orphaned entity records...")
                    for table in results.keys():
                        deleted = await entity_worker.sync_deleted_entities(
                            table_name=table,
                            database_id=database_id,
                            schema_name=schema_name,
                        )
                        if deleted:
                            logger.info("Purged orphaned entity embeddings", table=table, deleted=deleted)

    finally:
        await close_engine()


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize Text-to-SQL vector embeddings.")
    parser.add_argument("--table", default=None, help="Specific table name to synchronize (e.g. EmployeeInformation)")
    parser.add_argument("--all", action="store_true", help="Sync both schema and entity embeddings")
    parser.add_argument("--schema", action="store_true", help="Sync schema embeddings only")
    parser.add_argument("--entities", action="store_true", help="Sync row-level entity embeddings only")
    parser.add_argument("--purge-orphans", action="store_true", help="Purge deleted database rows from vector store")
    parser.add_argument("--database-id", default="default", help="Logical database identifier")
    parser.add_argument("--schema-name", default="public", help="PostgreSQL schema name")
    parser.add_argument("--batch-size", type=int, default=100, help="Embedding batch size")

    args = parser.parse_args()

    setup_logging()

    do_all = args.all or (not args.schema and not args.entities)
    sync_schema = do_all or args.schema
    sync_entities = do_all or args.entities

    asyncio.run(
        run_sync(
            sync_schema=sync_schema,
            sync_entities=sync_entities,
            purge_orphans=args.purge_orphans if args.table is None else False,
            database_id=args.database_id,
            schema_name=args.schema_name,
            batch_size=args.batch_size,
            table_name=args.table,
        )
    )


if __name__ == "__main__":
    main()
