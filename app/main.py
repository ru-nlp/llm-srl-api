from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import multiprocessing
import logging

from .config import settings
from .srl import router as srl_router

# Get module logger
logger = logging.getLogger("app.main")

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include SRL router with API prefix
app.include_router(srl_router, prefix=settings.API_PREFIX)

@app.on_event("startup")
async def startup_event():
    workers = settings.WORKERS if settings.WORKERS > 1 else "single process"
    logger.info(f"Started server process [{multiprocessing.current_process().pid}]")
    logger.info(f"Running {settings.API_TITLE} v{settings.API_VERSION} - {workers}")
    logger.info(f"URL: http://{settings.HOST}:{settings.PORT}")
    if settings.DEBUG:
        logger.warning("Running in debug mode")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Stopping server process [{multiprocessing.current_process().pid}]")

# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {duration:.3f}s with status {response.status_code}"
    )
    return response

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    logger.info("Health check endpoint called")
    return {"status": "healthy"} 