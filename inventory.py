import pandas as pd
from io import BytesIO
from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.responses import StreamingResponse
from database.db_depends import get_db
from models import Item, Inventory, InventoryItem, User
from fastapi.templating import Jinja2Templates
from auth import get_current_user

router = APIRouter(prefix="/inventory", tags=["Inventory"])
templates = Jinja2Templates(directory="templates")

from sqlalchemy.orm import selectinload

@router.get("/", response_class=HTMLResponse)
async def list_inventories(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Inventory)
        .options(
            selectinload(Inventory.items),           # загружаем товары
            selectinload(Inventory.created_by_user)  # загружаем пользователя
        )
        .order_by(Inventory.created_at.desc())
    )
    inventories = result.scalars().all()

    return templates.TemplateResponse(
        "inventory_list.html",
        {
            "request": request,
            "inventories": inventories
        }
    )


# Создать инвентаризацию
@router.post("/start")
async def start_inventory(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = (await db.execute(select(Item))).scalars().all()

    inv = Inventory(created_by=current_user.id)
    db.add(inv)
    await db.commit()
    await db.refresh(inv)

    for item in items:
        inv_item = InventoryItem(
            inventory_id=inv.id,
            item_id=item.id,
            expected_qty=item.quantity
        )
        db.add(inv_item)

    await db.commit()
    return RedirectResponse(f"/inventory/{inv.id}", status_code=303)

@router.get("/report")
async def inventory_report(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item).options(selectinload(Item.category)))
    items = result.scalars().all()

    report_items = []
    total_quantity = 0
    total_value = 0
    for item in items:
        qty = item.quantity or 0
        price = item.price or 0
        total = qty * price
        total_quantity += qty
        total_value += total
        report_items.append({
            "name": item.name,
            "category": item.category.name if item.category else "-",
            "quantity": qty,
            "price": price,
            "total_value": total
        })

    return templates.TemplateResponse(
        "inventory_report.html",
        {
            "request": request,
            "items": report_items,
            "total_quantity": total_quantity,
            "total_value": total_value
        }
    )

@router.get("/report/download")
async def download_inventory_report(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item).options(selectinload(Item.category)))
    items = result.scalars().all()

    report_items = []
    total_quantity = 0
    total_value = 0
    for item in items:
        qty = item.quantity or 0
        price = item.price or 0
        total = qty * price
        total_quantity += qty
        total_value += total
        report_items.append({
            "Название": item.name,
            "Категория": item.category.name if item.category else "-",
            "Количество": qty,
            "Цена": price,
            "Сумма": total
        })

    # Добавляем итоговую строку
    report_items.append({
        "Название": "Итого",
        "Категория": "",
        "Количество": total_quantity,
        "Цена": "",
        "Сумма": total_value
    })

    def create_excel(data):
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Отчет")
        output.seek(0)
        return output

    import asyncio
    output = await asyncio.to_thread(create_excel, report_items)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventory_report.xlsx"}
    )

@router.get("/{inv_id}")
async def view_inventory(inv_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    inv = await db.get(Inventory, inv_id)
    if not inv:
        return HTMLResponse("Инвентаризация не найдена", status_code=404)

    items = (
        await db.execute(
            select(InventoryItem)
            .where(InventoryItem.inventory_id == inv_id)
            .options(selectinload(InventoryItem.item))
        )
    ).scalars().all()

    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "inventory": inv,
            "items": items
        }
    )



# Ввести фактическое количество
@router.post("/update/{inv_item_id}")
async def update_inventory_item(
    inv_item_id: int,
    actual_qty: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    inv_item = await db.get(InventoryItem, inv_item_id)
    if not inv_item:
        return HTMLResponse("Запись не найдена", status_code=404)

    inv_item.actual_qty = actual_qty
    inv_item.difference = actual_qty - inv_item.expected_qty

    await db.commit()

    return RedirectResponse(f"/inventory/{inv_item.inventory_id}", status_code=303)
