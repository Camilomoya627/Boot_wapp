"""
database/firebase.py - Inicialización y conexión única a Firebase Firestore.
"""

import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Forzar la carga de variables de entorno antes de inicializar cualquier componente
load_dotenv()

logger = logging.getLogger(__name__)

class FirebaseClient:
    """Clase Singleton para asegurar una única instancia de conexión a Firestore."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
            cls._instance._initialize_db()
        return cls._instance

    def _initialize_db(self):
        try:
            # 1. Comprobar que no esté inicializada previamente
            if not firebase_admin._apps:
                
                # REVISIÓN EN NUBE: ¿Existe el JSON de texto completo en el entorno (Render)?
                firebase_json_env = os.getenv("FIREBASE_CREDENTIALS_JSON")
                
                if firebase_json_env:
                    logger.info("🔥 Cargando credenciales de Firebase desde variable de entorno (JSON string)...")
                    # Convertimos el string de texto nuevamente a un diccionario JSON válido
                    cred_dict = json.loads(firebase_json_env)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                
                # REVISIÓN LOCAL: Si no está en Render, buscará el archivo físico en tu PC
                else:
                    cred_path = os.getenv("FIREBASE_CREDENTIALS")
                    
                    if not cred_path:
                        raise ValueError("❌ Ni FIREBASE_CREDENTIALS_JSON ni FIREBASE_CREDENTIALS están definidas.")

                    # Verificar físicamente si el archivo existe en la ruta dada
                    if not os.path.exists(cred_path):
                        raise FileNotFoundError(f"❌ No se encontró el archivo JSON de Firebase en la ruta: '{cred_path}'")

                    logger.info(f"💻 Cargando credenciales de Firebase desde archivo local: {cred_path}")
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                
            self.db = firestore.client()
            logger.info("🔥 Conexión exitosa a Firebase Firestore establecida.")
            
        except Exception as e:
            logger.critical(f"❌ Error crítico al inicializar Firebase: {e}")
            raise e


def get_db():
    """Función expuesta para obtener el cliente de la base de datos."""
    return FirebaseClient().db