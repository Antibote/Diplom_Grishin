from fastapi import FastAPI, Request, Depends
import uvicorn

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from items import router as item
from categories import router as categ
from auth import router as auth
from users import router as users
from home import router as home
from auth import verify_auth



app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", tags=["Главное Меню"])
async def welcome(request: Request, error: str = None):
    error_message = "Неверный логин или пароль, попробуйте снова" if error == "invalid_credentials" else None
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error_message": error_message})




app.include_router(auth)
app.include_router(users, dependencies=[Depends(verify_auth)])
app.include_router(item, dependencies=[Depends(verify_auth)])
app.include_router(categ, dependencies=[Depends(verify_auth)])
app.include_router(home, dependencies=[Depends(verify_auth)])

if __name__ == '__main__':
    uvicorn.run("main:app", reload=True, port=5220)