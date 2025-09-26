from fastapi import Request, Form
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from fastapi.responses import RedirectResponse, HTMLResponse

from auth import get_current_user
from database.db_depends import get_db
from models import User


from fastapi.templating import Jinja2Templates

async def require_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    return user

templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix='/admin-panel',
                   tags=['Admin-panel'],)

@router.get("/create-user", response_class=HTMLResponse)
async def show_create_user_form(request: Request,
                                db: AsyncSession = Depends(get_db),
                                current_user: User = Depends(require_admin)):
    return templates.TemplateResponse(
        "create_user.html",
        {"request": request}
    )


@router.post("/create-user", status_code=201)
async def create_user(
        request: Request,
        name: str = Form(...),  # Используем Form() для данных формы
        post: str = Form(...),
        password: str = Form(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    result = await db.execute(select(User).where(User.name == name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = pwd_context.hash(password)
    new_user = User(
        name=name,
        post=post,
        hashed_password=hashed_password,
        is_active=True
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return RedirectResponse(url="/home", status_code=303)