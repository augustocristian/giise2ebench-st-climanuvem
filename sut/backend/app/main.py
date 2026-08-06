import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.infrastructure.database.database import engine
from app.infrastructure.database.bootstrap import bootstrap_database
from app.infrastructure.logging_config import configure_logging
from app.infrastructure.config import get_settings
from app.presentation.routes import test_routes, analysis_routes
from app.business.worker import analysis_worker

configure_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    bootstrap_database(engine)
                
    worker_task = None
    if settings.disable_worker:
        logger.info("Analysis worker disabled by DISABLE_WORKER=true")
    else:
        worker_task = asyncio.create_task(analysis_worker())
    
    yield
    
    if worker_task is not None:
        worker_task.cancel()
        # Esperamos a que la tarea termine limpiamente sin propagar su excepción de cancelación
        await asyncio.gather(worker_task, return_exceptions=True)

app = FastAPI(lifespan=lifespan)

# Mount the static directory for uploads
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if get_settings().test_mode:
    app.include_router(test_routes.router)
app.include_router(analysis_routes.router, prefix="/analysis", tags=["Analysis"])

@app.get("/ping")
def ping():
    return {"ping": "pong"}

@app.get("/")
def read_root():
    return {"service": "ClimaNuvem API", "status": "ok"}
