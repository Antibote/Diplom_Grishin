from fastapi import FastAPI, Request, Depends
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from logs import router as logs
from items import router as item
from categories import router as category
from auth import router as auth
from users import router as users
from home import router as home
from inventory import  router as inv
from auth import verify_auth
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == HTTP_401_UNAUTHORIZED:
        return templates.TemplateResponse("errors/401.html", {"request": request}, status_code=401)
    if exc.status_code == HTTP_403_FORBIDDEN:
        return templates.TemplateResponse("errors/403.html", {"request": request}, status_code=403)
    if exc.status_code == HTTP_404_NOT_FOUND:
        return templates.TemplateResponse("errors/404.html", {"request": request}, status_code=404)
    return templates.TemplateResponse("errors/500.html", {"request": request}, status_code=exc.status_code)

@app.get("/", tags=["Главное Меню"])
async def welcome(request: Request, error: str = None):
    error_message = "Неверный логин или пароль, попробуйте снова" if error == "invalid_credentials" else None
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error_message": error_message})




app.include_router(auth)
app.include_router(users, dependencies=[Depends(verify_auth)])
app.include_router(item, dependencies=[Depends(verify_auth)])
app.include_router(category, dependencies=[Depends(verify_auth)])
app.include_router(home, dependencies=[Depends(verify_auth)])
app.include_router(logs, dependencies=[Depends(verify_auth)])
app.include_router(inv, dependencies=[Depends(verify_auth)])

if __name__ == '__main__':
    uvicorn.run("main:app", reload=True, port=5220)