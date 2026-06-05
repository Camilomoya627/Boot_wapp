"""
models/patient.py - Modelos Pydantic para validación de datos de Pacientes.

Los modelos Pydantic proveen:
  - Validación automática de tipos
  - Serialización/deserialización JSON
  - Documentación automática en Swagger UI
  - Separación clara entre modelos de entrada (Request) y salida (Response)
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import re


class PatientCreate(BaseModel):
    """
    Modelo para crear un nuevo paciente.
    Usado en llamadas a la API REST (si se expone un endpoint de registro).
    """
    name: str
    phone: str
    email: Optional[EmailStr] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        return v.title()  # Normalizar capitalización

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Acepta teléfonos colombianos en formato local (10 dígitos) o internacional."""
        # Eliminar espacios y prefijo +57
        cleaned = re.sub(r"[\s+]", "", v).lstrip("57")
        if not re.match(r"^3\d{9}$", cleaned):
            raise ValueError("Número colombiano inválido. Debe ser un celular de 10 dígitos comenzando con 3")
        return cleaned

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Juan Pérez",
                "phone": "3001112233",
                "email": "juan@gmail.com"
            }
        }
    }


class PatientResponse(BaseModel):
    """
    Modelo de respuesta al consultar o crear un paciente.
    Oculta campos internos como created_at en la respuesta API.
    """
    id: str
    name: str
    phone: str
    email: Optional[str] = None

    model_config = {"from_attributes": True}


class PatientUpdate(BaseModel):
    """
    Modelo para actualizar datos parciales de un paciente.
    Todos los campos son opcionales (PATCH semántico).
    """
    name: Optional[str] = None
    email: Optional[EmailStr] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Juan Alberto Pérez",
                "email": "nuevo_email@gmail.com"
            }
        }
    }
