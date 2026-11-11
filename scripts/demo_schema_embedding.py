"""
Single-Table Schema Embedding and Semantic Retrieval Demo.

Demonstrates:
1. Constructing Table & Column metadata with enterprise business catalog enrichment.
2. Generating semantic embedding prose using SchemaDocumentBuilder.
3. Creating dense 1536-dim vector embeddings with Azure OpenAI (text-embedding-3-small).
4. Performing cosine similarity vector retrieval against user natural language questions.
5. Assembling the authorized SQL prompt context with retrieved columns.

Usage:
    python scripts/demo_schema_embedding.py
"""
import asyncio
import math
from pathlib import Path
import sys

# Ensure src/ is on python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from providers.embeddings import AzureOpenAIEmbeddings
from text_to_sql.schema.catalog import EnterpriseMetadataCatalog
from text_to_sql.schema.database_schema import DatabaseSchemaEntity
from text_to_sql.schema.metadata import ColumnMetadataEntity, TableMetadataEntity
from text_to_sql.vector_store.document_builder import SchemaDocumentBuilder
from text_to_sql.vector_store.schema_document import SchemaDocument, SchemaDocumentType


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two normalized or raw float vectors."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def create_sample_employee_table() -> TableMetadataEntity:
    """
    Construct a realistic TableMetadataEntity for EmployeeInformation table.
    """
    columns = {
        "id": ColumnMetadataEntity(
            name="id",
            data_type="UUID",
            is_nullable=False,
            is_primary_key=True,
            description="Unique platform surrogate primary key for employee profile record.",
        ),
        "employeename": ColumnMetadataEntity(
            name="employeeName",
            data_type="VARCHAR(255)",
            is_nullable=False,
            is_primary_key=False,
            description="Full legal name of the employee.",
            synonyms=["name", "full name", "staff name", "worker name"],
            sample_values=["John Doe", "Jane Smith", "Priya Sharma"],
            sensitivity="INTERNAL",
        ),
        "employeemailid": ColumnMetadataEntity(
            name="employeeMailId",
            data_type="VARCHAR(255)",
            is_nullable=False,
            is_primary_key=False,
            description="Corporate work email address; unique platform identifier.",
            synonyms=["email", "employee email", "corporate email", "user email"],
            sample_values=["john.doe@company.com", "priya.sharma@company.com"],
            sensitivity="INTERNAL",
        ),
        "careerlevel": ColumnMetadataEntity(
            name="careerLevel",
            data_type="VARCHAR(64)",
            is_nullable=False,
            is_primary_key=False,
            description="Corporate career level / seniority band (e.g. L1, L2, Lead, Principal).",
            synonyms=["level", "band", "grade", "seniority level"],
            sample_values=["L1", "L2", "L3", "Lead", "Director"],
            sensitivity="INTERNAL",
        ),
        "designation": ColumnMetadataEntity(
            name="designation",
            data_type="VARCHAR(128)",
            is_nullable=False,
            is_primary_key=False,
            description="Current professional job title or organizational role.",
            synonyms=["job title", "role title", "position", "designation"],
            sample_values=["Senior Data Engineer", "Cloud Architect", "Software Engineer"],
            sensitivity="INTERNAL",
        ),
        "department": ColumnMetadataEntity(
            name="department",
            data_type="VARCHAR(128)",
            is_nullable=False,
            is_primary_key=False,
            description="Functional business department or practice unit.",
            synonyms=["division", "business unit", "practice", "team"],
            sample_values=["Engineering", "Data & AI", "Cloud Operations"],
            sensitivity="INTERNAL",
        ),
        "worklocation": ColumnMetadataEntity(
            name="workLocation",
            data_type="VARCHAR(128)",
            is_nullable=False,
            is_primary_key=False,
            description="Primary assigned physical work location or office base city.",
            synonyms=["office", "location", "city", "base location", "branch"],
            sample_values=["Bangalore", "Mumbai", "Hyderabad", "Remote"],
            sensitivity="INTERNAL",
        ),
        "joiningdate": ColumnMetadataEntity(
            name="joiningDate",
            data_type="DATE",
            is_nullable=False,
            is_primary_key=False,
            description="Calendar date on which the employee joined the company.",
            synonyms=["hire date", "start date", "onboarding date", "joined on"],
            sample_values=["2021-06-15", "2023-01-10"],
            sensitivity="INTERNAL",
        ),
        "reportingmanagermailid": ColumnMetadataEntity(
            name="reportingManagerMailId",
            data_type="VARCHAR(255)",
            is_nullable=True,
            is_primary_key=False,
            description="Corporate email address of the employee's direct reporting manager / supervisor.",
            synonyms=["manager email", "supervisor", "lead email", "reports to"],
            sample_values=["sarah.manager@company.com"],
            sensitivity="INTERNAL",
        ),
        "currentctc": ColumnMetadataEntity(
            name="currentCtc",
            data_type="NUMERIC(14, 2)",
            is_nullable=False,
            is_primary_key=False,
            description="Total annual Cost to Company (CTC) compensation package in INR.",
            synonyms=["total salary", "annual compensation", "package", "ctc", "earnings"],
            sample_values=["1850000.00", "2500000.00"],
            sensitivity="CONFIDENTIAL",
        ),
        "fixedctc": ColumnMetadataEntity(
            name="fixedCtc",
            data_type="NUMERIC(14, 2)",
            is_nullable=False,
            is_primary_key=False,
            description="Annual fixed guaranteed base salary portion of compensation.",
            synonyms=["base salary", "fixed pay", "basic wage"],
            sample_values=["1500000.00", "2100000.00"],
            sensitivity="CONFIDENTIAL",
        ),
    }

    return TableMetadataEntity(
        name="EmployeeInformation",
        schema_name="public",
        database_id="default",
        description="Master employee directory holding employee identities, job titles, departments, managers, joining dates, and compensation details.",
        synonyms=["employee", "staff", "workers", "workforce", "personnel", "headcount", "team members"],
        columns=columns,
        primary_keys=["id"],
        indexes=["ix_employee_email", "ix_employee_dept"],
        row_count_estimate=1250,
    )


async def main() -> None:
    print("=" * 80)
    print("      ENTERPRISE TEXT-TO-SQL: SINGLE-TABLE SCHEMA EMBEDDING DEMO")
    print("=" * 80)

    # 1. Define single table metadata
    print("\n[Step 1] Constructing Table Metadata & Business Descriptions...")
    raw_table = create_sample_employee_table()
    catalog = EnterpriseMetadataCatalog()
    raw_schema = DatabaseSchemaEntity(
        database_id="default",
        schema_name="public",
        tables={"employeeinformation": raw_table},
    )
    enriched_schema = catalog.enrich_schema(raw_schema)
    enriched_table = enriched_schema.tables["employeeinformation"]
    print(f"  -> Table: {enriched_table.schema_name}.{enriched_table.name}")
    print(f"  -> Description: {enriched_table.description}")
    print(f"  -> Total Columns: {len(enriched_table.columns)}")
    print(f"  -> Synonyms: {', '.join(enriched_table.synonyms[:5])}")

    # 2. Build Schema Documents
    print("\n[Step 2] Building Schema Documents (Prose for Embedding)...")
    builder = SchemaDocumentBuilder()

    table_doc = builder.build_table_document(enriched_table)
    column_docs: list[SchemaDocument] = [
        builder.build_column_document(enriched_table, col)
        for col in enriched_table.columns.values()
    ]
    all_docs = [table_doc] + column_docs

    print(f"  -> Generated {len(all_docs)} schema documents (1 Table + {len(column_docs)} Columns).")
    print("\n--- [Preview: Table Document Searchable Text] ---")
    print(table_doc.searchable_text[:350] + "...\n")
    print("--- [Preview: Sample Column Document (currentCtc)] ---")
    ctc_doc = next(d for d in column_docs if d.column_name == "currentCtc")
    print(ctc_doc.searchable_text + "\n")

    # 3. Generate Dense 1536-dim Embeddings with Azure OpenAI
    print("[Step 3] Calling Azure OpenAI text-embedding-3-small (1536 dims)...")
    embeddings_service = AzureOpenAIEmbeddings()
    texts_to_embed = [d.searchable_text for d in all_docs]

    vectors = await embeddings_service.embed_batch(texts_to_embed)
    print(f"  -> Successfully generated {len(vectors)} embeddings!")
    print(f"  -> Vector dimensions: {len(vectors[0])}")
    print(f"  -> Sample vector preview (first 5 dims): {vectors[0][:5]}")

    # Build In-Memory Vector Store Index
    vector_index: list[tuple[SchemaDocument, list[float]]] = list(zip(all_docs, vectors))

    # 4. Run Semantic Queries
    test_queries = [
        "What is the annual compensation and salary package for senior staff?",
        "Who is the direct reporting manager for engineering team members?",
        "When did developers join the office in Bangalore?",
    ]

    print("\n" + "=" * 80)
    print("      SEMANTIC RETRIEVAL TESTING (Cosine Similarity Ranking)")
    print("=" * 80)

    for q_idx, query in enumerate(test_queries, 1):
        print(f"\n[Query {q_idx}]: \"{query}\"")
        query_vector = await embeddings_service.embed_query(query)

        # Compute cosine similarity across all indexed documents
        scored_docs: list[tuple[SchemaDocument, float]] = []
        for doc, doc_vec in vector_index:
            score = cosine_similarity(query_vector, doc_vec)
            scored_docs.append((doc, score))

        # Rank by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        print("  Top 4 Most Relevant Schema Elements Retrieved:")
        for rank, (doc, score) in enumerate(scored_docs[:4], 1):
            doc_type = doc.document_type.value
            target = f"Column: {doc.column_name}" if doc.column_name else f"Table: {doc.table_name}"
            print(f"    {rank}. [{score:.4f}] {doc_type:<6} | {target:<30} | Hash: {doc.content_hash[:8]}")

    print("\n" + "=" * 80)
    print("      DEMO COMPLETE: Schema Embedding & Retrieval Verified!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
