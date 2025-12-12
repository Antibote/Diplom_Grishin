from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

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
