from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, Depends, Request, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.db_depends import get_db
from models import Item, Category
from fastapi.templating import Jinja2Templates
from typing import Optional

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix='/items', tags=['Items'])


# 📌 форма создания товара
@router.get("/create", response_class=HTMLResponse)
async def create_item_form(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    return templates.TemplateResponse("create_item.html", {"request": request, "categories": categories})


# 📌 POST: создание товара
@router.post("/create")
async def create_item(
    name: str = Form(...),
    description: str = Form(""),
    quantity: int = Form(...),
    price: float = Form(...),
    category_id: Optional[str] = Form(None),   # принимаем строку
    db: AsyncSession = Depends(get_db)
):
    # преобразуем в int или None
    cat_id = int(category_id) if category_id and category_id.isdigit() else None

    new_item = Item(
        name=name,
        description=description,
        quantity=quantity,
        price=price,
        category_id=cat_id
    )
    db.add(new_item)
    await db.commit()
    return RedirectResponse(url="/home", status_code=303)




# 📌 Страница редактирования
@router.get("/edit/{item_id}", response_class=HTMLResponse)
async def edit_item_form(item_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return HTMLResponse(content="Товар не найден", status_code=404)
    return templates.TemplateResponse("edit_item.html", {"request": request, "item": item})


# 📌 POST: обновление товара
@router.post("/edit/{item_id}")
async def update_item(
    item_id: int,
    name: str = Form(...),
    description: str = Form(""),
    quantity: int = Form(...),
    price: float = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return HTMLResponse(content="Товар не найден", status_code=404)

    # обновляем поля
    item.name = name
    item.description = description
    item.quantity = quantity
    item.price = price

    await db.commit()
    return RedirectResponse(url="/home", status_code=303)

# 📌 POST: удаление товара
@router.post("/delete/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return HTMLResponse(content="Товар не найден", status_code=404)

    await db.delete(item)
    await db.commit()
    return RedirectResponse(url="/home", status_code=303)
