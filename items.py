from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.db_depends import get_db
from models import Item, Category, Log, ActionType, User
from fastapi.templating import Jinja2Templates
from typing import Optional
from utils.logs import log_action
from auth import get_current_user

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
    category_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    await db.refresh(new_item)

    # Логируем создание
    description_log = f"Пользователь {current_user.name} создал товар '{name}'"
    await log_action(
        db=db,
        user_id=current_user.id,
        action=ActionType.CREATE,
        item_id=new_item.id,
        description=description_log
    )

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
    category_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return HTMLResponse(content="Товар не найден", status_code=404)

    old_values = f"""
    Название - {item.name}
    Описание - {item.description}
    Количество - {item.quantity}
    Цена - {item.price}
    """


    # Обновляем поля
    item.name = name
    item.description = description
    item.quantity = quantity
    item.price = price
    item.category_id = int(category_id) if category_id and category_id.isdigit() else None

    await db.commit()
    await db.refresh(item)

    new_values = f"""
        Название - {name}
        Описание - {description}
        Количество - {quantity}
        Цена - {price}
        """

    description_log = f"Пользователь {current_user.name} обновил товар:\n{old_values}\nИзменён на:\n{new_values}"

    await log_action(
        db=db,
        user_id=current_user.id,
        action=ActionType.UPDATE,
        item_id=item.id,
        description=description_log
    )

    return RedirectResponse(url="/home", status_code=303)

# 📌 POST: удаление товара
@router.post("/delete/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Добавляем лог до удаления
    log = Log(
        user_id=current_user.id,
        item_id=item.id,
        action=ActionType.DELETE,
        description=f"Пользователь {current_user.name} удалил товар: {item.name}"
    )
    db.add(log)

    await db.delete(item)
    await db.commit()
    return RedirectResponse(url="/home", status_code=303)
