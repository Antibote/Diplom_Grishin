from sqlalchemy.ext.asyncio import AsyncSession
from models import Log, ActionType

async def log_action(db: AsyncSession, user_id: int, action: ActionType, item_id: int = None, description: str = None):
    log_entry = Log(
        user_id=user_id,
        item_id=item_id,
        action=action,
        description=description
    )
    db.add(log_entry)
    await db.commit()
