"""
Jumpstart V2
Used for the Dashboard seen upon entering DSP Floor 3
Authors: Eli Mares,Nikolai Strong, Will Hellinger,
V1 Authors: Beckett Jenen
"""

import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse


from config import BASE_DIR

from api import endpoints

app: FastAPI = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.include_router(endpoints.router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})