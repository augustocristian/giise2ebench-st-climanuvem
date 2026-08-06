import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.infrastructure.database.database import engine
from app.infrastructure.database.bootstrap import bootstrap_database
from app.infrastructure.logging_config import configure_logging
from app.infrastructure.config import get_settings
from app.presentation.error_handlers import register_exception_handlers
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
        # Wait for the task to finish cleanly without propagating its cancellation exception
        await asyncio.gather(worker_task, return_exceptions=True)

app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)

# Uploads are served only through the authenticated /api/v1/analyses/{id}/image endpoint
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(uploads_dir, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_v1 = APIRouter(prefix="/api/v1")


@api_v1.get("/ping")
def ping():
    return {"ping": "pong"}


@api_v1.get("/", include_in_schema=False)
@api_v1.get("")
def read_root():
    return {"service": "ClimaNuvem API", "status": "ok"}


if get_settings().test_mode:
    api_v1.include_router(test_routes.router)
api_v1.include_router(analysis_routes.router, prefix="/analyses", tags=["Analyses"])
app.include_router(api_v1)
