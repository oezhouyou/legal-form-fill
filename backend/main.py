import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from routers import upload, extract, form_fill

app = FastAPI(
    title="Legal Form Fill",
    description="Automated document extraction and form filling",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.upload_dir, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(upload.router, prefix="/api")
app.include_router(extract.router, prefix="/api")
app.include_router(form_fill.router, prefix="/api")
app.include_router(form_fill.ws_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
