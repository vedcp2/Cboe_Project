"""
This is the main entrypoint for the FastAPI backend application. It sets up the FastAPI app, configures CORS middleware, and includes all API routers for modular endpoint organization.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from fastapi.responses import StreamingResponse
import time
from backend.routers.upload import router as upload_router
from backend.routers.tables import router as tables_router
from backend.routers.charts import router as charts_router
from backend.routers.agent import router as agent_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(tables_router)
app.include_router(charts_router)
app.include_router(agent_router)

@app.get("/")
def read_root():
    """Health check endpoint. Returns a simple status message to confirm the backend is running."""
    return {"status": "Backend is running"}



