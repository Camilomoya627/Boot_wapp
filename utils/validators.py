"""
utils/validators.py - Funciones de validación reutilizables.

Centraliza todas las reglas de validación del dominio de negocio:
  - Teléfonos colombianos
  - Fechas futuras
  - Horarios laborales
"""

import re
from datetime import date, datetime, time


def validate_colombian_phone(phone: str) -> bool:
    """
    Valida que el número sea un celular colombiano válido de 10 dígitos.
    Soporta formatos internacionales previniendo la mutación destructiva de lstrip.

    Args:
        phone: Número con o sin prefijo +57, sin espacios
    """
    # Eliminar espacios, guiones y paréntesis
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    
    # CORRECCIÓN SEGURA: Quitar el prefijo de país de forma exacta (no con lstrip)
    if cleaned.startswith("+57"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("57") and len(cleaned) == 12:
        cleaned = cleaned[2:]
        
    return bool(re.match(r"^3\d{9}$", cleaned))


def validate_future_date(check_date) -> bool:
    """
    Verifica que la fecha sea hoy o en el futuro.
    """
    if isinstance(check_date, datetime):
        check_date = check_date.date()
    return check_date >= date.today()


def validate_working_hours(time_str: str) -> bool:
    """
    Verifica que la hora esté dentro del horario laboral permitido.
    Sincronizado con el horario de cierre de la clínica (08:00 AM - 05:30 PM).
    """
    try:
        parsed = datetime.strptime(time_str, "%H:%M").time()
        start = time(8, 0)     # 08:00 AM
        end = time(17, 30)    # 05:30 PM (Último slot almacenable)
        return start <= parsed <= end
    except ValueError:
        return False


def validate_date_format(date_str: str, fmt: str = "%d/%m/%Y") -> bool:
    """
    Verifica que una cadena de texto tenga el formato de fecha esperado.
    """
    try:
        datetime.strptime(date_str.strip(), fmt)
        return True
    except ValueError:
        return False


def sanitize_text(text: str, max_length: int = 500) -> str:
    """
    Limpia y trunca un texto de entrada para evitar caracteres extraños de control
    y garantizar la estabilidad del procesamiento con LLMs.
    """
    if not text:
        return ""
    # Conserva caracteres alfanuméricos, puntuación estándar, emojis y espacios/saltos de línea
    cleaned = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\x80-\xFF]", "", text)
    return cleaned.strip()[:max_length]