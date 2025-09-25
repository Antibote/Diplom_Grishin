from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.db_depends import get_db
from models import Category
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/categories", tags=["Categories"])


# 📌 Список категорий
@router.get("/list", response_class=HTMLResponse)
async def list_categories(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    return templates.TemplateResponse("categories_list.html", {"request": request, "categories": categories})


# 📌 Страница создания
@router.get("/create", response_class=HTMLResponse)
async def create_category_form(request: Request):
    return templates.TemplateResponse("create_category.html", {"request": request})


# 📌 POST: создание
@router.post("/create")
async def create_category(
    name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    new_category = Category(name=name)
    db.add(new_category)
    await db.commit()
    return RedirectResponse(url="/categories/list", status_code=303)


# 📌 Страница редактирования
@router.get("/edit/{category_id}", response_class=HTMLResponse)
async def edit_category_form(category_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        return HTMLResponse(content="Категория не найдена", status_code=404)
    return templates.TemplateResponse("edit_category.html", {"request": request, "category": category})


# 📌 POST: обновление
@router.post("/edit/{category_id}")
async def update_category(
    category_id: int,
    name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        return HTMLResponse(content="Категория не найдена", status_code=404)

    category.name = name
    await db.commit()
    return RedirectResponse(url="/categories/list", status_code=303)


# 📌 POST: удаление
@router.post("/delete/{category_id}")
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        return HTMLResponse(content="Категория не найдена", status_code=404)

    await db.delete(category)
    await db.commit()
    return RedirectResponse(url="/categories/list", status_code=303)
