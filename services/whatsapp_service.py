"""
services/whatsapp_service.py - Servicio de envío de mensajes por WhatsApp Cloud API.

Responsabilidades:
  - Enviar mensajes de texto simples
  - Enviar mensajes con botones interactivos
  - Enviar mensajes con listas
  - Marcar mensajes como leídos
  - Encapsular toda la comunicación con la API de Meta
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

META_API_VERSION = "v19.0"
META_API_BASE = f"https://graph.facebook.com/{META_API_VERSION}"


class WhatsAppService:
    """
    Cliente HTTP para la WhatsApp Cloud API de Meta.
    Implementa el patrón de servicio con métodos asíncronos.
    """

    def __init__(self):
        self.token = os.getenv("WHATSAPP_TOKEN")
        self.phone_number_id = os.getenv("PHONE_NUMBER_ID")

        if not self.token or not self.phone_number_id:
            raise ValueError(
                "WHATSAPP_TOKEN y PHONE_NUMBER_ID deben estar en el .env"
            )

        # CORRECCIÓN: Separamos la URL de mensajes y la URL base del teléfono
        self.phone_base_url = f"{META_API_BASE}/{self.phone_number_id}"
        self.messages_url = f"{self.phone_base_url}/messages"
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    async def send_message(self, to: str, text: str) -> bool:
        """
        Envía un mensaje de texto simple a un número de WhatsApp.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text
            }
        }
        return await self._post(self.messages_url, payload)

    async def send_interactive_buttons(self, to: str, body: str, buttons: list) -> bool:
        """
        Envía un mensaje con botones de respuesta rápida (máx 3).
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": btn["id"], "title": btn["title"]}
                        }
                        for btn in buttons[:3]
                    ]
                }
            }
        }
        return await self._post(self.messages_url, payload)

    async def send_list_message(self, to: str, body: str, button_text: str, sections: list) -> bool:
        """
        Envía un mensaje con una lista de opciones seleccionables.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": body},
                "action": {
                    "button": button_text,
                    "sections": sections
                }
            }
        }
        return await self._post(self.messages_url, payload)

    async def mark_as_read(self, message_id: str) -> bool:
        """
        Marca un mensaje como leído (doble check azul).
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        # CORRECCIÓN: El endpoint de marcas de lectura golpea directamente a /messages
        return await self._post(self.messages_url, payload)

    async def _post(self, url: str, payload: dict) -> bool:
        """
        Método privado que ejecuta la petición HTTP a la API de Meta.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )

            # Meta puede responder 200 o 201 en peticiones exitosas de la API Graph
            if response.status_code in [200, 201]:
                logger.info(f"Petición de WhatsApp exitosa: {response.json()}")
                return True
            else:
                logger.error(
                    f"Error de WhatsApp API {response.status_code}: {response.text}"
                )
                return False

        except httpx.TimeoutException:
            logger.error("Timeout excedido al conectar con la API de WhatsApp")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en WhatsAppService: {e}", exc_info=True)
            return False