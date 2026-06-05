"""
services/ai_service.py - Servicio de IA con Groq y Diagnóstico Forzado.
"""

import os
import logging
import traceback
from groq import Groq

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        print("\n--- [DIAGNÓSTICO] Iniciando AIService ---")
        api_key = os.getenv("GROQ_API_KEY")
        print(f"--- [DIAGNÓSTICO] GROQ_API_KEY encontrada: {f'SÍ (Empieza con {api_key[:6]}...)' if api_key else 'NO'} ---")
        
        if not api_key:
            raise ValueError("❌ GROQ_API_KEY no está configurada en el archivo .env")
            
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"
        print("--- [DIAGNÓSTICO] Cliente de Groq inicializado correctamente ---\n")

    async def analyze_intent(self, text: str) -> str:
        print(f"\n--- [DIAGNÓSTICO ENTRO A INTENTOS] Analizando texto: '{text}' ---")
        prompt = (
            "Analiza el mensaje del usuario y clasifícalo en una de las siguientes intenciones. "
            "Responde ÚNICAMENTE con la palabra clave: 'booking', 'cancel', 'reschedule', 'human', 'general'.\n"
            f"Mensaje: \"{text}\""
        )

        try:
            print("--- [DIAGNÓSTICO INTENTOS] Llamando a la API de Groq... ---")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un clasificador estricto."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=10
            )
            intent = response.choices[0].message.content.strip().lower()
            print(f"--- [DIAGNÓSTICO INTENTOS] Groq respondió intención: '{intent}' ---")
            
            valid_intents = ["booking", "cancel", "reschedule", "human", "general"]
            return intent if intent in valid_intents else "general"

        except Exception as e:
            print(f"\n❌ [ERROR CRÍTICO EN ANALYZE_INTENT]: {str(e)}\n")
            traceback.print_exc()
            return "general"

    async def get_general_response(self, text: str, history: list) -> str:
        print(f"\n--- [DIAGNÓSTICO GENERAL_RESP] Generando respuesta para: '{text}' ---")
        system_instruction = (
            "Eres Camila, la asistente virtual médica de la clínica HealthCare+. "
            "Sé amable, concisa y profesional."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": text}
        ]

        try:
            print("--- [DIAGNÓSTICO GENERAL_RESP] Llamando a la API de Groq para chat... ---")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            respuesta_final = response.choices[0].message.content.strip()
            print("--- [DIAGNÓSTICO GENERAL_RESP] ¡Respuesta generada con éxito con Groq! ---")
            return respuesta_final
            
        except Exception as e:
            print(f"\n❌ [ERROR CRÍTICO EN GET_GENERAL_RESPONSE]: {str(e)}\n")
            traceback.print_exc()
            return "Lo siento, en este momento tengo problemas para procesar tu solicitud. ¿Podrías intentar escribirme de nuevo? 🩺"