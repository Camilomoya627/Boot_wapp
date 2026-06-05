"""
services/appointment_service.py - Servicio de gestión de citas médicas.

Responsabilidades:
  - Crear citas (con detección de duplicados)
  - Cancelar citas
  - Reprogramar citas
  - Consultar disponibilidad de horarios
  - Manejar flujos conversacionales de agendamiento
"""

import uuid
import logging
from datetime import datetime, date
# CORRECCIÓN: Usar la librería oficial administrada para el marcador de tiempo
from firebase_admin import firestore

# CORRECCIÓN: Se remueve el prefijo 'app.' porque utils está en la raíz
from utils.validators import validate_colombian_phone, validate_future_date, validate_working_hours

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración de horarios y slots disponibles
# ---------------------------------------------------------------------------
DOCTOR_ID = "doctor_001"          # Médico por defecto

AVAILABLE_SLOTS = [
    "08:00", "08:30", "09:00", "09:30",
    "10:00", "10:30", "11:00", "11:30",
    "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30", "17:00", "17:30"
]

BOOKING_STEPS = ["name", "phone", "date", "time"]


class AppointmentService:
    """
    Servicio de citas que implementa flujos conversacionales
    usando Firebase como almacén de estado.
    """

    def __init__(self, db):
        self.db = db

    # -----------------------------------------------------------------------
    # FLUJO DE AGENDAMIENTO
    # -----------------------------------------------------------------------

    async def handle_booking_flow(self, phone: str, text: str, conversation: dict) -> str:
        """
        Maneja cada paso del flujo de agendamiento de una cita nueva.
        """
        booking_data = conversation.get("booking_data", {})
        step = self._get_current_booking_step(booking_data)

        if step == "name":
            if len(text) < 3:
                return "Por favor ingresa tu nombre completo (mínimo 3 caracteres)."
            booking_data["name"] = text.title()
            # CORRECCIÓN: Quitamos await porque las operaciones internas de base de datos son síncronas
            self._update_booking_data(phone, booking_data)
            return f"Gracias, *{booking_data['name']}* 👋\n\nAhora, ¿cuál es tu número de teléfono celular? (ejemplo: 3001112233)"

        elif step == "phone":
            cleaned = text.replace(" ", "").replace("+57", "")
            if not validate_colombian_phone(cleaned):
                return "⚠️ Número no válido. Ingresa un celular colombiano de 10 dígitos (ej: 3001112233)."
            booking_data["phone"] = cleaned
            self._update_booking_data(phone, booking_data)
            return (
                "Perfecto ✅\n\n"
                "¿Para qué *fecha* deseas tu cita?\n"
                "Formato: DD/MM/AAAA (ej: 25/06/2026)\n"
                "Solo disponible de lunes a viernes."
            )

        elif step == "date":
            parsed_date = self._parse_date(text)
            if not parsed_date:
                return "⚠️ Formato de fecha incorrecto. Usa DD/MM/AAAA (ej: 20/06/2026)."
            if not validate_future_date(parsed_date):
                return "⚠️ La fecha debe ser en el futuro. Por favor ingresa una fecha válida."
            if parsed_date.weekday() >= 5:  # Sábado=5, Domingo=6
                return "⚠️ Solo atendemos de lunes a viernes. Por favor elige otro día."

            booking_data["date"] = parsed_date.strftime("%Y-%m-%d")
            # CORRECCIÓN: Quitamos await porque get_available_slots es síncrono internamente
            available = self.get_available_slots(booking_data["date"])
            self._update_booking_data(phone, booking_data)

            if not available:
                return (
                    f"Lo siento, el *{text}* no tiene horarios disponibles. 😞\n"
                    "Por favor elige otra fecha (DD/MM/AAAA):"
                )

            slots_text = "\n".join([f"  • {s}" for s in available])
            return f"📅 Horarios disponibles para el {text}:\n\n{slots_text}\n\n¿Cuál hora prefieres?"

        elif step == "time":
            time_str = text.strip()
            try:
                parsed_time = datetime.strptime(time_str, "%H:%M")
                time_str = parsed_time.strftime("%H:%M")
            except ValueError:
                return "⚠️ Formato de hora incorrecto. Usa HH:MM (ej: 09:00)."

            if not validate_working_hours(time_str):
                return "⚠️ Ese horario está fuera de nuestro horario de atención (08:00 - 18:00)."

            available = self.get_available_slots(booking_data["date"])
            if time_str not in available:
                slots_text = "\n".join([f"  • {s}" for s in available])
                return (
                    f"⚠️ Lo siento, a las {time_str} ya está ocupado.\n\n"
                    f"Horarios disponibles:\n{slots_text}\n\n¿Cuál prefieres?"
                )

            booking_data["time"] = time_str

            # CORRECCIÓN: Quitamos await por base de datos síncrona
            appointment = self._create_appointment(phone, booking_data)
            self._clear_booking_flow(phone)

            date_obj = datetime.strptime(booking_data["date"], "%Y-%m-%d")
            date_formatted = date_obj.strftime("%d/%m/%Y")

            return (
                f"✅ *¡Cita confirmada exitosamente!*\n\n"
                f"👤 Paciente: {booking_data['name']}\n"
                f"📅 Fecha: {date_formatted}\n"
                f"⏰ Hora: {booking_data['time']}\n"
                f"🏥 Consultorio: HealthCare+\n\n"
                f"_Recuerda llegar 10 minutos antes de tu cita._\n"
                f"Para cancelar o reprogramar, escríbenos con anticipación.\n\n"
                f"¡Gracias por elegir HealthCare+! 💙"
            )

        return "Ha ocurrido un error en el flujo. Escribe 'agendar cita' para comenzar de nuevo."

    # -----------------------------------------------------------------------
    # FLUJO DE CANCELACIÓN
    # -----------------------------------------------------------------------

    async def start_cancel_flow(self, phone: str) -> str:
        """Inicia el flujo de cancelación buscando citas activas del paciente."""
        appointments = self._get_active_appointments_by_phone(phone)
        if not appointments:
            self._clear_all_flows(phone)
            return (
                "No encontramos citas activas asociadas a tu número. 🔍\n\n"
                "Si tienes una cita registrada con otro número, por favor llámanos."
            )

        appt_list = self._format_appointment_list(appointments)
        self._save_flow_state(phone, "cancel", {"appointments": appointments})
        return (
            f"📋 Tus citas activas:\n\n{appt_list}\n\n"
            "¿Cuál quieres cancelar? Escribe el número correspondiente (1, 2, 3...):"
        )

    async def handle_cancel_flow(self, phone: str, text: str, conversation: dict) -> str:
        """Procesa la selección del usuario y cancela la cita."""
        flow_data = conversation.get("flow_data", {})
        appointments = flow_data.get("appointments", [])

        try:
            index = int(text.strip()) - 1
            if index < 0 or index >= len(appointments):
                raise ValueError
        except ValueError:
            return f"⚠️ Por favor ingresa un número entre 1 y {len(appointments)}."

        appt = appointments[index]
        self._cancel_appointment(appt["id"])
        self._clear_all_flows(phone)

        return (
            f"❌ *Cita cancelada exitosamente.*\n\n"
            f"📅 Fecha: {appt['date']}\n"
            f"⏰ Hora: {appt['time']}\n\n"
            "Si deseas reagendar, escribe *'agendar cita'*. ¡Hasta pronto! 😊"
        )

    # -----------------------------------------------------------------------
    # FLUJO DE REPROGRAMACIÓN
    # -----------------------------------------------------------------------

    async def start_reschedule_flow(self, phone: str) -> str:
        """Inicia el flujo de reprogramación mostrando citas activas."""
        appointments = self._get_active_appointments_by_phone(phone)
        if not appointments:
            self._clear_all_flows(phone)
            return "No encontramos citas activas para reprogramar. 🔍"

        appt_list = self._format_appointment_list(appointments)
        self._save_flow_state(phone, "reschedule", {
            "appointments": appointments,
            "step": "select"
        })
        return (
            f"📋 Tus citas activas:\n\n{appt_list}\n\n"
            "¿Cuál quieres reprogramar? Escribe el número:"
        )

    async def handle_reschedule_flow(self, phone: str, text: str, conversation: dict) -> str:
        """Maneja los pasos del flujo de reprogramación."""
        flow_data = conversation.get("flow_data", {})
        step = flow_data.get("step", "select")

        if step == "select":
            appointments = flow_data.get("appointments", [])
            try:
                index = int(text.strip()) - 1
                if index < 0 or index >= len(appointments):
                    raise ValueError
            except ValueError:
                return f"⚠️ Ingresa un número entre 1 y {len(appointments)}."

            flow_data["selected_appointment"] = appointments[index]
            flow_data["step"] = "new_date"
            self._save_flow_state(phone, "reschedule", flow_data)
            return "📅 ¿Cuál es la nueva fecha? (DD/MM/AAAA):"

        elif step == "new_date":
            parsed_date = self._parse_date(text)
            if not parsed_date or not validate_future_date(parsed_date) or parsed_date.weekday() >= 5:
                return "⚠️ Fecha inválida. Debe ser una fecha futura de lunes a viernes (DD/MM/AAAA)."

            available = self.get_available_slots(parsed_date.strftime("%Y-%m-%d"))
            if not available:
                return f"No hay horarios disponibles para el {text}. Elige otra fecha:"

            flow_data["new_date"] = parsed_date.strftime("%Y-%m-%d")
            flow_data["step"] = "new_time"
            self._save_flow_state(phone, "reschedule", flow_data)

            slots_text = "\n".join([f"  • {s}" for s in available])
            return f"Horarios disponibles:\n\n{slots_text}\n\n¿Cuál hora prefieres?"

        elif step == "new_time":
            try:
                parsed_time = datetime.strptime(text.strip(), "%H:%M")
                time_str = parsed_time.strftime("%H:%M")
            except ValueError:
                return "⚠️ Formato incorrecto. Usa HH:MM (ej: 10:00)."

            available = self.get_available_slots(flow_data["new_date"])
            if time_str not in available:
                return f"⚠️ Ese horario no está disponible. Elige uno de los disponibles."

            appt_id = flow_data["selected_appointment"]["id"]
            self._reschedule_appointment(appt_id, flow_data["new_date"], time_str)
            self._clear_all_flows(phone)

            date_formatted = datetime.strptime(flow_data["new_date"], "%Y-%m-%d").strftime("%d/%m/%Y")
            return (
                f"✅ *¡Cita reprogramada exitosamente!*\n\n"
                f"📅 Nueva fecha: {date_formatted}\n"
                f"⏰ Nueva hora: {time_str}\n\n"
                "¡Hasta pronto! 💙"
            )

        return "Error en el flujo. Escribe 'reprogramar cita' para comenzar de nuevo."

    # -----------------------------------------------------------------------
    # Consulta de disponibilidad
    # -----------------------------------------------------------------------

    def get_available_slots(self, date_str: str) -> list:
        """
        Retorna los slots disponibles para una fecha dada de forma síncrona.
        """
        occupied = self._get_occupied_slots(date_str)
        return [slot for slot in AVAILABLE_SLOTS if slot not in occupied]

    def _get_occupied_slots(self, date_str: str) -> set:
        """Consulta Firebase para obtener los horarios ya reservados de forma síncrona."""
        docs = (
            self.db.collection("appointments")
            .where("date", "==", date_str)
            .where("doctor_id", "==", DOCTOR_ID)
            .where("status", "==", "scheduled")
            .stream()
        )
        return {doc.to_dict().get("time") for doc in docs}

    # -----------------------------------------------------------------------
    # Operaciones CRUD en Firebase (Síncronas)
    # -----------------------------------------------------------------------

    def _create_appointment(self, phone: str, data: dict) -> dict:
        """Crea una nueva cita en la colección appointments."""
        appt_id = str(uuid.uuid4())
        appointment = {
            "id": appt_id,
            "patient_phone": phone,
            "patient_name": data["name"],
            "doctor_id": DOCTOR_ID,
            "date": data["date"],
            "time": data["time"],
            "status": "scheduled",
            "created_at": firestore.SERVER_TIMESTAMP
        }
        self.db.collection("appointments").document(appt_id).set(appointment)
        logger.info(f"Appointment created: {appt_id} for {phone}")
        return appointment

    def _cancel_appointment(self, appt_id: str):
        """Cambia el estado de una cita a 'cancelled'."""
        self.db.collection("appointments").document(appt_id).update({
            "status": "cancelled",
            "updated_at": firestore.SERVER_TIMESTAMP
        })

    def _reschedule_appointment(self, appt_id: str, new_date: str, new_time: str):
        """Actualiza la fecha y hora de una cita existente."""
        self.db.collection("appointments").document(appt_id).update({
            "date": new_date,
            "time": new_time,
            "status": "scheduled",
            "updated_at": firestore.SERVER_TIMESTAMP
        })

    def _get_active_appointments_by_phone(self, phone: str) -> list:
        """Busca todas las citas activas de un número de teléfono."""
        docs = (
            self.db.collection("appointments")
            .where("patient_phone", "==", phone)
            .where("status", "==", "scheduled")
            .stream()
        )
        return [doc.to_dict() for doc in docs]

    # -----------------------------------------------------------------------
    # Gestión del estado de los flujos conversacionales (Síncronas)
    # -----------------------------------------------------------------------

    def _update_booking_data(self, phone: str, booking_data: dict):
        """Guarda el progreso del flujo de agendamiento."""
        self.db.collection("conversations").document(phone).update({
            "booking_data": booking_data,
            "active_flow": "booking",
            "updated_at": firestore.SERVER_TIMESTAMP
        })

    def _save_flow_state(self, phone: str, flow: str, data: dict):
        """Guarda el estado de flujos de cancelación o reprogramación."""
        self.db.collection("conversations").document(phone).update({
            "active_flow": flow,
            "flow_data": data,
            "updated_at": firestore.SERVER_TIMESTAMP
        })

    def _clear_booking_flow(self, phone: str):
        """Limpia el estado del flujo de agendamiento al finalizar."""
        self.db.collection("conversations").document(phone).update({
            "active_flow": None,
            "booking_data": {},
            "updated_at": firestore.SERVER_TIMESTAMP
        })

    def _clear_all_flows(self, phone: str):
        """Limpia todos los flujos activos de la conversación."""
        self.db.collection("conversations").document(phone).update({
            "active_flow": None,
            "booking_data": {},
            "flow_data": {},
            "updated_at": firestore.SERVER_TIMESTAMP
        })

    # -----------------------------------------------------------------------
    # Helpers de presentación
    # -----------------------------------------------------------------------

    def _get_current_booking_step(self, booking_data: dict) -> str:
        for step in BOOKING_STEPS:
            if step not in booking_data:
                return step
        return "complete"

    def _parse_date(self, text: str):
        try:
            return datetime.strptime(text.strip(), "%d/%m/%Y").date()
        except ValueError:
            return None

    def _format_appointment_list(self, appointments: list) -> str:
        lines = []
        for i, appt in enumerate(appointments, 1):
            try:
                d = datetime.strptime(appt["date"], "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                d = appt.get("date", "N/A")
            lines.append(f"{i}. 📅 {d} a las {appt.get('time', 'N/A')}")
        return "\n".join(lines)