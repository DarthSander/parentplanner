from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.vector.embeddings import generate_embedding


async def retrieve_context(
    db: AsyncSession,
    household_id: UUID,
    query: str,
    top_k: int = 12,
    source_types: list[str] | None = None,
) -> list[str]:
    """Retrieve relevant context documents using vector similarity search."""
    embedding = await generate_embedding(query)
    embedding_str = f"[{','.join(map(str, embedding))}]"

    filter_clause = "WHERE household_id = :household_id"
    params: dict = {"embedding": embedding_str, "household_id": str(household_id), "top_k": top_k}

    if source_types:
        placeholders = ", ".join(f":st_{i}" for i in range(len(source_types)))
        filter_clause += f" AND source_type IN ({placeholders})"
        for i, st in enumerate(source_types):
            params[f"st_{i}"] = st

    result = await db.execute(
        text(f"""
            SELECT content, 1 - (embedding <=> :embedding::vector) AS similarity
            FROM vector_documents
            {filter_clause}
            ORDER BY embedding <=> :embedding::vector
            LIMIT :top_k
        """),
        params,
    )
    rows = result.fetchall()
    return [row.content for row in rows if row.similarity > 0.4]
