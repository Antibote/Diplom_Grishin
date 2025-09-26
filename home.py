from fastapi import APIRouter, Request, Depends

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_depends import get_db
from sqlalchemy.future import select
from sqlalchemy import desc
from models import Item, Category
from fastapi import Query
from typing import Optional
from models import User
from auth import get_current_user


router = APIRouter(prefix='/home',
                   tags=['Home'],)
router.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None)   # <- строка
):
    query = select(Item).order_by(desc(Item.id))

    if search:
        query = query.where(Item.name.ilike(f"%{search}%"))

    if category_id and category_id.isdigit():  # <- проверяем, что это число
        query = query.where(Item.category_id == int(category_id))

    result = await db.execute(query)
    items = result.scalars().all()

    cat_result = await db.execute(select(Category))
    categories = cat_result.scalars().all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "items": items,
        "categories": categories,
        "selected_category": int(category_id) if category_id and category_id.isdigit() else None,
        "search": search,
        "current_user": current_user
    })