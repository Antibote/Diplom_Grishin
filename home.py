from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.db_depends import get_db
from models import Item, Category, User
from typing import Optional
from auth import get_current_user
from aiocache import cached, Cache



router = APIRouter(prefix='/home',
                   tags=['Home'],)
router.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Асинхронная функция для получения товаров с кэшированием
@cached(ttl=60, cache=Cache.MEMORY)  # Кэш 60 секунд
async def get_items(db: AsyncSession, search: Optional[str] = None, category_id: Optional[int] = None):
    query = select(Item).order_by(desc(Item.id))
    if search:
        query = query.where(Item.name.ilike(f"%{search}%"))
    if category_id:
        query = query.where(Item.category_id == category_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None)
):
    # Получаем категории (не кэшируем — они редко грузятся и мало)
    cat_result = await db.execute(select(Category))
    categories = cat_result.scalars().all()

    # Получаем товары через кэшированную функцию
    items = await get_items(
        db,
        search=search,
        category_id=int(category_id) if category_id and category_id.isdigit() else None
    )

    # Считаем общую стоимость
    total_cost_result = await db.execute(select(func.sum(Item.price * Item.quantity)))
    total_cost = total_cost_result.scalar() or 0

    return templates.TemplateResponse("index.html", {
        "request": request,
        "items": items,
        "categories": categories,
        "selected_category": int(category_id) if category_id and category_id.isdigit() else None,
        "search": search,
        "current_user": current_user,
        "total_cost": total_cost
    })