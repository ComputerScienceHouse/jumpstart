"""
Jumpstart V2
Used for the Dashboard seen upon entering DSP Floor 3
Authors: Eli Mares,Nikolai Strong, Will Hellinger,
V1 Authors: Beckett Jenen
"""

import os

from logging import getLogger, Logger

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse

from config import BASE_DIR

from api import endpoints

logger: Logger = getLogger(__name__)


logger.info("Starting up the Jumpstart application!")
app: FastAPI = FastAPI(docs_url="/swag")

logger.info("Mounting static files and templates!")
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

templates: Jinja2Templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

if os.path.exists(os.path.join(BASE_DIR, "docs")):
    logger.info("Documentation directory found, setting up documentation endpoint!")

    app.mount(
        "/docs",
        StaticFiles(directory=os.path.join(BASE_DIR, "docs")),
        name="docs"
    )

    @app.get("/docs", include_in_schema=False)
    async def docs_redirect():
        # Mkdocs links dynamically and not being on the direct index.html causes issues
        return RedirectResponse(url="/docs/index.html")
    
else:
    logger.warning("Documentation directory not found, skipping documentation setup!")

logger.info("Importing API endpoints!")
app.include_router(endpoints.router, prefix="/api")

logger.info("Finished setting up the application!")
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})