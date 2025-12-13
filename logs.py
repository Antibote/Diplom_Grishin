from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi.responses import HTMLResponse
from database.db_depends import get_db
from models import Log
from auth import get_current_user

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/logs", response_class=HTMLResponse)
async def view_logs(request: Request, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    # Загружаем пользователя и товар через selectinload
    result = await db.execute(
        select(Log)
        .options(selectinload(Log.user), selectinload(Log.item))
        .order_by(Log.timestamp.desc())
    )
    logs = result.scalars().all()
    return templates.TemplateResponse("logs.html", {"request": request, "logs": logs, "current_user": current_user})
