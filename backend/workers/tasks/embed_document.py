import asyncio
import logging

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def embed_document(self, source_id: str, source_type: str):
    """Generate and store embedding for a document asynchronously."""
    asyncio.run(_embed(source_id, source_type))


async def _embed(source_id: str, source_type: str):
    from uuid import UUID

    from sqlalchemy import select

    from core.database import get_db_context
    from models.vector import VectorDocument
    from services.vector.embeddings import (
        build_calendar_document,
        build_completion_document,
        build_inventory_document,
        build_task_document,
        generate_embedding,
    )

    async with get_db_context() as db:
        # Build document text based on source type
        content = await _build_content(db, UUID(source_id), source_type)
        if not content:
            logger.warning(f"No content built for {source_type}:{source_id}")
            return

        # Generate embedding
        embedding = await generate_embedding(content)

        # Check if document already exists
        result = await db.execute(
            select(VectorDocument).where(
                VectorDocument.source_type == source_type,
                VectorDocument.source_id == UUID(source_id),
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.content = content
            existing.embedding = embedding
        else:
            # Get household_id and member_id from source
            household_id, member_id = await _get_ids(db, UUID(source_id), source_type)
            doc = VectorDocument(
                household_id=household_id,
                member_id=member_id,
                source_type=source_type,
                source_id=UUID(source_id),
                content=content,
                embedding=embedding,
            )
            db.add(doc)

        await db.commit()
        logger.info(f"Embedded {source_type}:{source_id}")


async def _build_content(db, source_id, source_type: str) -> str | None:
    from sqlalchemy import select

    from models.member import Member
    from models.task import Task, TaskCompletion
    from models.calendar import CalendarEvent
    from models.inventory import InventoryItem
    from models.chat import ChatMessage
    from services.vector.embeddings import (
        build_task_document,
        build_completion_document,
        build_calendar_document,
        build_inventory_document,
    )

    if source_type == "task":
        result = await db.execute(select(Task).where(Task.id == source_id))
        task = result.scalar_one_or_none()
        if not task:
            return None
        member = None
        if task.assigned_to:
            m_result = await db.execute(select(Member).where(Member.id == task.assigned_to))
            member = m_result.scalar_one_or_none()
        return build_task_document(task, member)

    elif source_type == "task_completion":
        result = await db.execute(select(TaskCompletion).where(TaskCompletion.id == source_id))
        completion = result.scalar_one_or_none()
        if not completion:
            return None
        t_result = await db.execute(select(Task).where(Task.id == completion.task_id))
        task = t_result.scalar_one_or_none()
        m_result = await db.execute(select(Member).where(Member.id == completion.completed_by))
        member = m_result.scalar_one_or_none()
        if not task or not member:
            return None
        return build_completion_document(completion, task, member)

    elif source_type == "calendar_event":
        result = await db.execute(select(CalendarEvent).where(CalendarEvent.id == source_id))
        event = result.scalar_one_or_none()
        if not event:
            return None
        member = None
        if event.member_id:
            m_result = await db.execute(select(Member).where(Member.id == event.member_id))
            member = m_result.scalar_one_or_none()
        return build_calendar_document(event, member)

    elif source_type == "inventory":
        result = await db.execute(select(InventoryItem).where(InventoryItem.id == source_id))
        item = result.scalar_one_or_none()
        if not item:
            return None
        return build_inventory_document(item)

    elif source_type == "chat_message":
        result = await db.execute(select(ChatMessage).where(ChatMessage.id == source_id))
        msg = result.scalar_one_or_none()
        if not msg:
            return None
        return f"Chat ({msg.role}): {msg.content}"

    return None


async def _get_ids(db, source_id, source_type: str):
    from sqlalchemy import select

    from models.task import Task, TaskCompletion
    from models.calendar import CalendarEvent
    from models.inventory import InventoryItem
    from models.chat import ChatMessage

    model_map = {
        "task": Task,
        "task_completion": TaskCompletion,
        "calendar_event": CalendarEvent,
        "inventory": InventoryItem,
        "chat_message": ChatMessage,
    }
    model = model_map.get(source_type)
    if not model:
        return None, None

    result = await db.execute(select(model).where(model.id == source_id))
    obj = result.scalar_one_or_none()
    if not obj:
        return None, None

    household_id = getattr(obj, "household_id", None)
    member_id = getattr(obj, "member_id", None)
    if not member_id:
        member_id = getattr(obj, "completed_by", None)
    if not member_id:
        member_id = getattr(obj, "assigned_to", None)

    return household_id, member_id
