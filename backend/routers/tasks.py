from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from models.member import Member, MemberRole
from models.task import Task, TaskCategory, TaskCompletion, TaskStatus
from schemas.task import (
    TaskCompleteRequest,
    TaskCreate,
    TaskDistributionItem,
    TaskResponse,
    TaskUpdate,
)

router = APIRouter()


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Create a new task."""
    # Caregivers can only create baby_care tasks
    if member.role == MemberRole.caregiver and payload.category != "baby_care":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Als zorgverlener kun je alleen babytaken aanmaken.",
        )

    task = Task(
        household_id=member.household_id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        task_type=payload.task_type,
        assigned_to=payload.assigned_to,
        due_date=payload.due_date,
        recurrence_rule=payload.recurrence_rule,
        estimated_minutes=payload.estimated_minutes,
        dependencies=payload.dependencies,
        created_by=member.id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # TODO: trigger embedding update async (step 6)

    return task


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    category: str | None = Query(None),
    task_status: str | None = Query(None, alias="status"),
    assigned_to: UUID | None = Query(None),
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """List tasks for the current household with optional filters."""
    query = select(Task).where(Task.household_id == member.household_id)

    # Caregivers only see baby_care tasks
    if member.role == MemberRole.caregiver:
        query = query.where(Task.category == TaskCategory.baby_care)

    # Partners don't see other people's private tasks
    if member.role == MemberRole.partner:
        query = query.where(
            (Task.category != TaskCategory.private) | (Task.assigned_to == member.id)
        )

    if category:
        query = query.where(Task.category == category)
    if task_status:
        query = query.where(Task.status == task_status)
    if assigned_to:
        query = query.where(Task.assigned_to == assigned_to)

    query = query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/distribution", response_model=list[TaskDistributionItem])
async def get_distribution(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Get task distribution overview per member."""
    members_result = await db.execute(
        select(Member).where(Member.household_id == member.household_id)
    )
    members = members_result.scalars().all()

    distribution = []
    for m in members:
        if m.role == MemberRole.daycare:
            continue

        completed_count = await db.scalar(
            select(func.count()).select_from(TaskCompletion).where(
                TaskCompletion.completed_by == m.id,
                TaskCompletion.household_id == member.household_id,
            )
        )
        open_count = await db.scalar(
            select(func.count()).select_from(Task).where(
                Task.assigned_to == m.id,
                Task.household_id == member.household_id,
                Task.status.in_(["open", "in_progress"]),
            )
        )

        # Count by category
        cat_result = await db.execute(
            select(Task.category, func.count()).where(
                Task.assigned_to == m.id,
                Task.household_id == member.household_id,
            ).group_by(Task.category)
        )
        categories = {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in cat_result}

        distribution.append(TaskDistributionItem(
            member_id=m.id,
            display_name=m.display_name,
            total_completed=completed_count or 0,
            total_open=open_count or 0,
            categories=categories,
        ))

    return distribution


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Get a single task by ID."""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.household_id == member.household_id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Update a task with optimistic locking."""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.household_id == member.household_id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Optimistic locking check
    if payload.version != task.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "VERSION_CONFLICT",
                "message": "Deze taak is zojuist bijgewerkt door iemand anders.",
                "current_version": task.version,
            },
        )

    for field, value in payload.model_dump(exclude={"version"}, exclude_unset=True).items():
        setattr(task, field, value)
    task.version += 1
    task.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(task)

    # TODO: trigger embedding update async (step 6)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Delete a task."""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.household_id == member.household_id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await db.delete(task)
    await db.commit()


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    payload: TaskCompleteRequest | None = None,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Mark a task as completed and log the completion."""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.household_id == member.household_id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    task.status = TaskStatus.done
    task.version += 1
    task.updated_at = datetime.now(timezone.utc)

    completion = TaskCompletion(
        task_id=task.id,
        household_id=member.household_id,
        completed_by=member.id,
        duration_minutes=payload.duration_minutes if payload else None,
    )
    db.add(completion)

    await db.commit()
    await db.refresh(task)

    # TODO: trigger embedding for completion (step 6)

    return task


@router.post("/{task_id}/snooze", response_model=TaskResponse)
async def snooze_task(
    task_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Snooze a task (increment snooze counter)."""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.household_id == member.household_id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    task.status = TaskStatus.snoozed
    task.snooze_count += 1
    task.version += 1
    task.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(task)
    return task
