from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Admin


async def ensure_owner(session: AsyncSession, owner_id: int) -> Admin:
    """Make sure the configured OWNER_ID exists in admins as is_owner=True."""
    existing = await session.get(Admin, owner_id)
    if existing is None:
        admin = Admin(user_id=owner_id, is_owner=True, receive_ideas=True)
        session.add(admin)
        await session.commit()
        return admin

    if not existing.is_owner:
        existing.is_owner = True
        await session.commit()
    return existing


async def is_admin(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(
        select(Admin.user_id).where(Admin.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None


async def get_idea_recipients(session: AsyncSession) -> list[int]:
    """All admins that opted in to receive ideas."""
    result = await session.execute(
        select(Admin.user_id).where(Admin.receive_ideas.is_(True))
    )
    return [row[0] for row in result.all()]
