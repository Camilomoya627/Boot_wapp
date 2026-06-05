"""
main.py - Punto de entrada principal de la aplicación FastAPI.

Este archivo inicializa la app, registra los routers y configura
middlewares. Sigue el principio de responsabilidad única (SRP).
"""

import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# CORRECCIÓN: Importamos tanto FastAPI como la clase para la anotación de tipos
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importación limpia sin el prefijo 'app.'
from routes.whatsapp import router as whatsapp_router

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de logging para producción
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


# Definición del ciclo de vida (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que se ejecuta al arrancar el servidor
    logger.info("🚀 Medical Chatbot API started successfully.")
    yield
    # Código que se ejecuta al apagar el servidor
    logger.info("🛑 Medical Chatbot API shutting down.")


# Instancia principal de FastAPI
app = FastAPI(
    title="Medical Chatbot API",
    description="Chatbot médico integrado con WhatsApp Business API",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS (ajustar origins específicos en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar router de WhatsApp
app.include_router(whatsapp_router, prefix="/webhook", tags=["WhatsApp"])


@app.get("/", tags=["Health"])
async def root():
    """Endpoint de verificación de salud del servidor."""
    return {"status": "ok", "message": "Medical Chatbot API running"}