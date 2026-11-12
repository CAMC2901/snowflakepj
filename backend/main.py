import os
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.core.config import settings
from backend.app.core.database import init_db, SessionLocal, CuratedDocument
from backend.app.core.seed_data import seed_database
from backend.app.rag.ingest_all import run_ingestion
from backend.app.api.routes_agent import router as agent_router
from backend.app.api.routes_cases import router as cases_router
from backend.app.api.routes_analytics import router as analytics_router
from backend.app.api.routes_knowledge import router as knowledge_router
from backend.app.api.routes_snowflake import router as snowflake_router

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"--> Iniciando {settings.APP_NAME}...")
    init_db()
    seed_database()
    
    # Comprobar si hay documentos indexados
    db = SessionLocal()
    try:
        if db.query(CuratedDocument).count() == 0:
            print("--> Indexando documentos oficiales para el RAG...")
            run_ingestion()
    finally:
        db.close()
        
    print("--> Backend listo y operativo en el puerto", settings.PORT)
    yield
    print("--> Apagando servicios backend...")

app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema Multiagente de IA para Gestión Ciudadana y PQRSD - Alcaldía Distrital de Barranquilla",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar Routers de la API
app.include_router(agent_router, prefix="/api")
app.include_router(cases_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(snowflake_router, prefix="/api")

@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "database": "CONNECTED",
        "rag_service": "OPERATIONAL",
        "agent_engine": "LANGGRAPH_READY"
    }

# Montar Frontend estático si existe el build
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Ruta de API no encontrada.")
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "app": settings.APP_NAME,
            "entity": "Alcaldía Distrital de Barranquilla",
            "status": "ONLINE",
            "docs_url": "/docs",
        }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
