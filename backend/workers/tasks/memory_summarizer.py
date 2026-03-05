import asyncio
import logging
from datetime import datetime, timedelta, timezone

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.memory_summarizer.monthly_memory_summarizer")
def monthly_memory_summarizer():
    """Monthly cron: compress old vector documents into summaries."""
    asyncio.run(_run_summarizer())


async def _run_summarizer():
    from collections import defaultdict

    from sqlalchemy import select

    from core.database import get_db_context
    from models.household import Household
    from models.vector import VectorDocument
    from services.ai.ai_utils import AICallError, call_claude
    from services.vector.embeddings import generate_embedding

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    async with get_db_context() as db:
        # Get all households with vector documents
        result = await db.execute(
            select(VectorDocument.household_id).where(
                VectorDocument.created_at < cutoff,
                VectorDocument.is_summary == False,
            ).distinct()
        )
        household_ids = [row[0] for row in result.fetchall()]

        for hid in household_ids:
            docs_result = await db.execute(
                select(VectorDocument).where(
                    VectorDocument.household_id == hid,
                    VectorDocument.created_at < cutoff,
                    VectorDocument.is_summary == False,
                )
            )
            old_docs = docs_result.scalars().all()

            if len(old_docs) < 20:
                continue

            # Cluster by source type
            clusters = defaultdict(list)
            for doc in old_docs:
                clusters[doc.source_type].append(doc)

            for source_type, docs in clusters.items():
                content_block = "\n".join([d.content for d in docs[:50]])

                try:
                    summary_text = await call_claude(
                        system="Je vat gezinsactiviteiten samen. Bewaar patronen en frequenties. Max 300 woorden. Nederlands.",
                        user_message=f"Maak een beknopte samenvatting van de volgende {source_type} activiteit:\n\n{content_block}",
                        max_tokens=500,
                    )
                except AICallError as e:
                    logger.error(f"Memory summarizer failed for {hid}, {source_type}: {e}")
                    continue

                embedding = await generate_embedding(summary_text)

                summary_doc = VectorDocument(
                    household_id=hid,
                    source_type="summary",
                    content=summary_text,
                    embedding=embedding,
                    is_summary=True,
                    summarizes_before=cutoff,
                    metadata_={"original_source_type": str(source_type), "doc_count": len(docs)},
                )
                db.add(summary_doc)

                for doc in docs:
                    await db.delete(doc)

            await db.commit()
            logger.info(f"Memory summarizer completed for household {hid}")
