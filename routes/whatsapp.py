"""
routes/whatsapp.py - Rutas del webhook de WhatsApp Cloud API.

Maneja:
  - GET /webhook  → verificación del webhook por Meta
  - POST /webhook → recepción de mensajes entrantes
"""

import os
import logging
from fastapi import APIRouter, Request, Response, HTTPException
from firebase_admin import firestore 

from services.whatsapp_service import WhatsAppService
from services.ai_service import AIService
from services.appointment_service import AppointmentService
from services.patient_service import PatientService
from database.firebase import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# Instancias de servicios (inyección de dependencias manual)
db = get_db()
whatsapp_svc = WhatsAppService()
ai_svc = AIService()
appointment_svc = AppointmentService(db)
patient_svc = PatientService(db)


# ---------------------------------------------------------------------------
# GET /webhook — Verificación del webhook (handshake de Meta)
# ---------------------------------------------------------------------------
@router.get("")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    # CORRECCIÓN: Sincronizado con el nombre exacto de tu archivo .env
    verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN", "")

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == verify_token:
        logger.info("Webhook verified successfully.")
        return Response(content=challenge, media_type="text/plain")

    logger.warning("Webhook verification failed.")
    raise HTTPException(status_code=403, detail="Verification failed")


# ---------------------------------------------------------------------------
# POST /webhook — Recepción de mensajes de WhatsApp
# ---------------------------------------------------------------------------
@router.post("")
async def receive_message(request: Request):
    try:
        body = await request.json()
        logger.info(f"Incoming webhook payload: {body}")

        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ok"}

        message = messages[0]
        from_number = message.get("from")
        msg_type = message.get("type")

        if msg_type != "text":
            await whatsapp_svc.send_message(
                from_number,
                "Por el momento solo proceso mensajes de texto. 😊"
            )
            return {"status": "ok"}

        user_text = message["text"]["body"].strip()
        logger.info(f"Message from {from_number}: {user_text}")

        response_text = await process_user_message(from_number, user_text)
        await whatsapp_svc.send_message(from_number, response_text)

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Lógica principal de orquestación
# ---------------------------------------------------------------------------
async def process_user_message(phone: str, text: str) -> str:
    conversation = _get_or_create_conversation(phone)
    history = conversation.get("messages", [])

    active_flow = conversation.get("active_flow")
    if active_flow == "booking":
        return await appointment_svc.handle_booking_flow(phone, text, conversation)
    if active_flow == "reschedule":
        return await appointment_svc.handle_reschedule_flow(phone, text, conversation)
    if active_flow == "cancel":
        return await appointment_svc.handle_cancel_flow(phone, text, conversation)

    # CORRECCIÓN: Cambiado detect_intent -> analyze_intent (coincide con tu ai_service.py)
    intent = await ai_svc.analyze_intent(text)
    logger.info(f"Detected intent for {phone}: {intent}")

    if intent == "general":
        # CORRECCIÓN: Cambiado answer_faq -> get_general_response
        return await ai_svc.get_general_response(text, history)

    elif intent == "booking":
        _update_conversation_flow(phone, "booking", conversation)
        return (
            "¡Con gusto te ayudo a agendar tu cita! 📅\n\n"
            "Por favor, dime tu *nombre completo*:"
        )

    elif intent == "reschedule":
        _update_conversation_flow(phone, "reschedule", conversation)
        return await appointment_svc.start_reschedule_flow(phone)

    elif intent == "cancel":
        _update_conversation_flow(phone, "cancel", conversation)
        return await appointment_svc.start_cancel_flow(phone)

    elif intent == "human":
        return _escalate_to_human(phone)

    else:
        # CORRECCIÓN: Caída por defecto usando el método correcto de Groq
        return await ai_svc.get_general_response(text, history)


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------
def _get_or_create_conversation(phone: str) -> dict:
    """Recupera la conversación activa o crea una nueva de forma síncrona."""
    conv_ref = db.collection("conversations").document(phone)
    doc = conv_ref.get()
    if doc.exists:
        return doc.to_dict()
    
    new_conv = {"phone": phone, "messages": [], "active_flow": None}
    conv_ref.set(new_conv)
    return new_conv


def _update_conversation_flow(phone: str, flow: str, conversation: dict):
    """Actualiza el flujo activo de la conversación en Firebase de forma síncrona."""
    conversation["active_flow"] = flow
    db.collection("conversations").document(phone).update({
        "active_flow": flow,
        "updated_at": firestore.SERVER_TIMESTAMP
    })


def _escalate_to_human(phone: str) -> str:
    """Registra la solicitud de agente humano en Firebase de forma síncrona."""
    db.collection("human_escalations").document(phone).set({
        "phone": phone,
        "status": "pending",
        "created_at": firestore.SERVER_TIMESTAMP
    })
    return (
        "🙋 Entendido. Uno de nuestros asesores te atenderá en breve.\n\n"
        "Nuestro horario de atención es de lunes a viernes, 8:00 AM a 6:00 PM.\n"
        "¡Gracias por tu paciencia!"
    )