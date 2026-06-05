"""
models/appointment.py - Modelos Pydantic para validación de datos de Citas.

Define los esquemas de datos para crear, actualizar y responder
información sobre citas médicas.
"""

from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import date, datetime
import re


# Tipo para el estado de una cita (restricción estricta de valores válidos)
AppointmentStatus = Literal["scheduled", "cancelled", "completed", "rescheduled"]


class AppointmentCreate(BaseModel):
    """
    Modelo para crear una nueva cita médica.
    Usado por la API REST (si se expone un endpoint directo).
    """
    patient_phone: str
    patient_name: str
    doctor_id: str = "doctor_001"
    date: str          # Formato: YYYY-MM-DD
    time: str          # Formato: HH:MM

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            parsed = datetime.strptime(v, "%Y-%m-%d").date()
            if parsed < date.today():
                raise ValueError("La fecha debe ser en el futuro")
            return v
        except ValueError as e:
            raise ValueError(f"Fecha inválida: {e}")

    @field_validator("time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Formato de hora inválido. Usa HH:MM")
        hour = int(v.split(":")[0])
        if not (8 <= hour < 18):
            raise ValueError("La hora debe estar entre 08:00 y 17:30")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "patient_phone": "3001112233",
                "patient_name": "Juan Pérez",
                "doctor_id": "doctor_001",
                "date": "2026-07-15",
                "time": "09:00"
            }
        }
    }


class AppointmentResponse(BaseModel):
    """
    Modelo de respuesta al consultar o crear una cita.
    """
    id: str
    patient_phone: str
    patient_name: str
    doctor_id: str
    date: str
    time: str
    status: AppointmentStatus

    model_config = {"from_attributes": True}


class AppointmentUpdate(BaseModel):
    """
    Modelo para actualizar una cita existente (reprogramar o cancelar).
    """
    date: Optional[str] = None
    time: Optional[str] = None
    status: Optional[AppointmentStatus] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "date": "2026-08-01",
                "time": "14:00",
                "status": "scheduled"
            }
        }
    }
