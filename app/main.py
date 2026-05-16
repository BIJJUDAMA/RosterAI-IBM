import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

from .database.connection import init_db
from .core.status import status_tracker
from .core.websocket import manager
from .logging_config import setup_logging, logger
from .exceptions import AppError
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


setup_logging()

# Lifespan for Startup/Shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[bold green]Backend Startup Initiated[/bold green]")
    init_db()
    status_tracker.reset()
    
    #  Backend Validation & Warmup
    async def warmup():
        try:
            from .intelligence.llm_client import LLMClient
            client = LLMClient()
            
            # Monitor Proxy Status (Circuit Breaker)
            # The Proxy handles the actual LLM load and joke generation internally
            max_wait = 60 # 5 minutes max wait for model load
            for _ in range(max_wait):
                if client.check_connectivity():
                    status_tracker.set_status(is_llm_ready=True)
                    manager.thread_safe_broadcast(status_tracker.get_status())
                    return
                await asyncio.sleep(5)
            
            logger.error("❌ [bold red]Intelligence Proxy Timeout.[/bold red] AI engine failed to initialize.")
            status_tracker.set_status(is_llm_ready=False, current_task="AI Offline")
        except Exception as e:
            logger.error(f"❌ AI Warmup Failed: {e}")
            status_tracker.set_status(is_llm_ready=False, current_task="AI Error")

    asyncio.create_task(warmup())
    
    logger.info("[bold green]Backend is ready to serve requests[/bold green]")
    yield
    logger.info("[bold red]Backend Shutdown Initiated[/bold red]")
    from .intelligence.agent_service import agent_brain
    agent_brain.shutdown()

# App Initialization
app = FastAPI(title="Roster Backend", lifespan=lifespan)

# Global Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Global Exception Handlers
@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    logger.error(f"Application Error: {exc.message} | Detail: {exc.detail}")
    return JSONResponse(status_code=400, content={"error": exc.message, "detail": exc.detail})

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.exception(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(status_code=500, content={"error": "An internal server error occurred", "detail": str(exc)})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    logger.warning(f"Validation Error: {exc.errors()}")
    return JSONResponse(status_code=422, content={"error": "Validation failed", "detail": exc.errors()})

# WebSocket Endpoint (Kept in main to avoid circular manager/app imports)
@app.websocket("/api/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json(status_tracker.get_status())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Routers
from .api.routers import members, projects, ingestion, matching, analytics

app.include_router(members.router)
app.include_router(projects.router)
app.include_router(ingestion.router)
app.include_router(matching.router)
app.include_router(analytics.router)

# 8. Legacy/Core Status
@app.get("/api/status")
def get_system_status():
    return status_tracker.get_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
