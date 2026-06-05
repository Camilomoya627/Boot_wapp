"""
services/patient_service.py - Servicio de gestión de pacientes.

Responsabilidades:
  - Registrar nuevos pacientes en Firebase
  - Buscar pacientes por teléfono o ID
  - Actualizar información del paciente
  - Verificar si un paciente ya está registrado (evitar duplicados)
"""

import uuid
import logging
# CORRECCIÓN: Usar el módulo correcto de firestore desde firebase_admin
from firebase_admin import firestore

logger = logging.getLogger(__name__)


class PatientService:
    """
    Servicio de pacientes con operaciones CRUD sobre la colección 'patients'.
    Garantiza la unicidad del paciente basada en el número de teléfono.
    """

    def __init__(self, db):
        self.db = db

    async def get_or_create_patient(self, phone: str, name: str = None, email: str = None) -> dict:
        """
        Retorna el paciente existente o crea uno nuevo si no existe.
        Es el método principal para el registro de pacientes.
        """
        # CORRECCIÓN: Quitamos el await porque get_patient_by_phone es síncrono internamente
        existing = self.get_patient_by_phone(phone)
        if existing:
            logger.info(f"Patient found: {existing['id']}")
            return existing

        # Crear nuevo paciente
        return self.create_patient(phone, name, email)

    def create_patient(self, phone: str, name: str, email: str = None) -> dict:
        """
        Crea un nuevo paciente en Firestore de forma síncrona.
        """
        patient_id = str(uuid.uuid4())
        patient = {
            "id": patient_id,
            "name": name or "Sin nombre",
            "phone": phone,
            "email": email or "",
            "created_at": firestore.SERVER_TIMESTAMP  # CORRECCIÓN: Origen del timestamp
        }
        
        # Operación síncrona nativa
        self.db.collection("patients").document(patient_id).set(patient)
        logger.info(f"New patient created: {patient_id} ({phone})")
        return patient

    def get_patient_by_phone(self, phone: str) -> dict | None:
        """
        Busca un paciente por su número de teléfono.
        """
        # Operación síncrona nativa (.stream())
        docs = (
            self.db.collection("patients")
            .where("phone", "==", phone)
            .limit(1)
            .stream()
        )
        for doc in docs:
            return doc.to_dict()
        return None

    def get_patient_by_id(self, patient_id: str) -> dict | None:
        """
        Busca un paciente por su ID único.
        """
        # Operación síncrona nativa (.get())
        doc = self.db.collection("patients").document(patient_id).get()
        if doc.exists:
            return doc.to_dict()
        return None

    def update_patient(self, patient_id: str, updates: dict) -> bool:
        """
        Actualiza los campos de un paciente.
        """
        try:
            updates["updated_at"] = firestore.SERVER_TIMESTAMP  # CORRECCIÓN: Origen del timestamp
            # Operación síncrona nativa (.update())
            self.db.collection("patients").document(patient_id).update(updates)
            logger.info(f"Patient updated: {patient_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating patient {patient_id}: {e}")
            return False