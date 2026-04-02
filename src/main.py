"""
Jumpstart V2
Used for the Dashboard seen upon entering DSP Floor 3
Authors: Eli Mares,Nikolai Strong, Will Hellinger,
V1 Authors: Beckett Jenen
"""

import os
import asyncio

from logging import getLogger, Logger

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from contextlib import asynccontextmanager

from config import BASE_DIR

from api import endpoints
from core import wikithoughts, cshcalendar

logger: Logger = getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
	logger.info("Starting up the Jumpstart application!")
	async with asyncio.TaskGroup() as tg:
		tg.create_task(cshcalendar.rebuild_calendar())
	await wikithoughts.auth_bot()
	
	yield
	logger.info("Shutting down the Jumpstart application!")
	await cshcalendar.close_client()

	logger.info("Succesfully shut down the Jumpstart application!")


app: FastAPI = FastAPI(docs_url="/swag", lifespan=lifespan)

logger.info("Mounting static files and templates!")
app.mount(
	"/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static"
)

templates: Jinja2Templates = Jinja2Templates(
	directory=os.path.join(BASE_DIR, "templates")
)

if os.path.exists(os.path.join(BASE_DIR, "docs")):
	logger.info("Documentation directory found, setting up documentation endpoint!")

	app.mount(
		"/docs", StaticFiles(directory=os.path.join(BASE_DIR, "docs")), name="docs"
	)

	@app.get("/docs", include_in_schema=False)
	async def docs_redirect():
		# Mkdocs links dynamically and not being on the direct index.html causes issues
		return RedirectResponse(url="/docs/index.html")

else:
	logger.warning("Documentation directory not found, skipping documentation setup!")

logger.info("Importing API endpoints!")
# app.include_router(endpoints.router, prefix="/api")
app.include_router(endpoints.router)

logger.info("Finished setting up the application!")


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
	return templates.TemplateResponse(name="index.html", request=request)
