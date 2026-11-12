# =====================================================================
# DOCKERFILE MULTI-STAGE: AGENTE DE GESTIÓN CIUDADANA BARRANQUILLA
# Contenedor Unificado: Frontend React + Backend FastAPI + RAG + MCP
# Alcaldía Distrital de Barranquilla — Distrito Especial, Industrial y Portuario
# =====================================================================

# ---------------------------------------------------------------------
# ETAPA 1: Construcción del Frontend con Node.js 22 Alpine
# ---------------------------------------------------------------------
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

# Copiar manifiestos de dependencias
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund

# Copiar código fuente del frontend y compilar bundle de producción
COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------
# ETAPA 2: Runtime Backend y Servidor de Aplicación con Python 3.12 Slim
# ---------------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema operativo requeridas para librerías C/C++ y SSL
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libffi-dev \
    libssl-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Actualizar gestor de paquetes pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copiar e instalar dependencias de Python (LangGraph, FastAPI, PyMuPDF, Groq, Snowflake, MCP, NumPy)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copiar código fuente del backend, datos oficiales y documentación
COPY backend /app/backend
COPY docs /app/docs

# Copiar el frontend compilado (dist) desde la Etapa 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Configuración de variables de entorno del contenedor
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000
ENV APP_ENV=production
ENV DATABASE_URL=sqlite:////app/data_barranquilla.db

# Exponer puerto 8000 (Ventanilla Virtual + Consola + API REST)
EXPOSE 8000

# Verificación de estado de salud del contenedor
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de arranque del servidor unificado (FastAPI sirve API y Frontend React)
CMD ["python", "-u", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
