#  Medical Chatbot API — WhatsApp Business & FastAPI

¡Bienvenido al repositorio del **Medical Chatbot API**! Este sistema automatiza la gestión de una clínica médica a través de WhatsApp, permitiendo a los pacientes agendar, reprogramar y cancelar citas médicas de forma autónoma gracias a la Inteligencia Artificial, delegando casos complejos a agentes humanos a través de un sistema de orquestación en la nube.

La asistente virtual principal se llama **Camila**, y está integrada con modelos de lenguaje avanzados para ofrecer respuestas empáticas, profesionales y precisas.

---

##  Características Principales

* ** Orquestación de IA:** Clasificación de intenciones en tiempo real mediante la API de **Groq** / **OpenAI** / **Anthropic**.
* ** Gestión de Flujos Dinámicos:** Manejo estricto de estados para agendamiento, reprogramación y cancelación de citas sin perder el contexto.
* ** Base de Datos NoSQL:** Persistencia de historiales de conversación, estados de flujo y escalaciones utilizando **Firebase Firestore**.
* ** Integración Oficial:** Conexión directa con la **WhatsApp Cloud API** de Meta mediante Webhooks.
* ** Arquitectura Robusta:** Desarrollado con **FastAPI** (Python 3.14+), utilizando programación asíncrona (`async/await`) y validación de tipos con **Pydantic v2**.

---

## Arquitectura y Tecnologías

* **Backend:** FastAPI, Uvicorn, Gunicorn
* **Base de Datos:** Firebase Admin SDK (Firestore)
* **Proveedores de IA:** Groq API / OpenAI API
* **Servicios Externos:** WhatsApp Cloud API (Meta)
* **Servidor de Producción:** Linux (Render Cloud)

---

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:
* Python 3.14 o superior
* Una cuenta en [Meta for Developers](https://developers.facebook.com/) con WhatsApp configurado.
* Un proyecto activo en [Firebase](https://firebase.google.com/) con una base de datos Firestore limpia.

---

##  Configuración del Entorno (`.env`)

Crea un archivo `.env` en la raíz del proyecto y configura las siguientes variables (no subas este archivo a GitHub por seguridad):

`+
# --- Configuración del Servidor ---
PORT=8000

# --- Tokens de WhatsApp (Meta) ---
WHATSAPP_TOKEN="tu_token_de_acceso_permanente_de_meta"
PHONE_NUMBER_ID="tu_identificador_de_numero_de_telefono"
WEBHOOK_VERIFY_TOKEN="tu_numero_o_clave_de_verificacion"

# --- Proveedores de Inteligencia Artificial ---
GROQ_API_KEY="tu_llave_secreta_de_groq"
OPENAI_API_KEY="tu_llave_secreta_de_openai"
###Instalación Local
Clonar el repositorio:

Bash
git clone [https://github.com/Camilomoya2024/Boot_wapp.git](https://github.com/Camilomoya2024/Boot_wapp.git)
cd Boot_wapp
Crear y activar un entorno virtual:

Bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/Mac:
source .venv/bin/activate
Instalar las dependencias corregidas para entorno headless:

Bash
pip install -r requirements.txt
Arrancar el servidor de desarrollo:

Bash
uvicorn main:app --reload
El servidor estará disponible localmente en: http://127.0.0.1:8000

 Despliegue en Producción (Render)
Este proyecto está configurado para ejecutarse en entornos Linux limpios (Headless), habiendo removido dependencias de hardware local de sonido o interfaces exclusivas de Windows.

Conecta este repositorio de GitHub a tu servicio web en Render.com.

Configura el comando de arranque (Start Command):

Bash
uvicorn main:app --host 0.0.0.0 --port $PORT
Inyecta todas las variables definidas en el archivo .env dentro de la pestaña Environment de Render.

 Configuración del Webhook en Meta
Para conectar WhatsApp con el servidor en producción, dirígete al panel de Meta y configura las credenciales del Webhook de la siguiente manera:

URL de devolución de llamada: https://tu-subdominio.onrender.com/webhook

Token de verificación: El valor exacto que asignaste a WEBHOOK_VERIFY_TOKEN (ej. tu número de verificación).

Nota Importante: Recuerda suscribirte al campo messages en la tabla de campos de Webhook de Meta para que el servidor pueda capturar y responder los mensajes entrantes de los pacientes de forma automática.

 Contribuidores y Soporte
Desarrollador Principal: Camilo Moya

Contacto Comercial:camilomoya864@gmail.com

Este proyecto se distribuye bajo la licencia MIT.

# --- Credenciales de Firebase ---
# (Asegúrate de inicializar el SDK con tu archivo de llaves de cuenta de servicio)
FIREBASE_CREDENTIALS_PATH="path/to/firebase-key.json"
