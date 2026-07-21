"""
Etapa 8 del desafio: registro de ejecucion (trazabilidad).

Guarda cada interaccion pregunta/respuesta en logs/interacciones.jsonl
(formato JSON Lines), tal como sugiere el material para ejecucion local.
Si despliegas en la nube, puedes ademas enviar estos mismos registros
a un servicio de logs centralizado (CloudWatch, OCI Logging, etc.).
"""
import json
import os
from datetime import datetime, timezone

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "interacciones.jsonl")


def registrar_interaccion(pregunta, contexto, respuesta, fuentes, tiempo_respuesta_seg,
                           feedback=None):
    os.makedirs(LOG_DIR, exist_ok=True)
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pregunta": pregunta,
        "contexto_recuperado": contexto,
        "respuesta": respuesta,
        "fuentes": fuentes,
        "tiempo_respuesta_seg": tiempo_respuesta_seg,
        "feedback": feedback,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro


def actualizar_feedback(timestamp, feedback):
    """Recorre el log y actualiza el feedback de la entrada con ese timestamp."""
    if not os.path.exists(LOG_FILE):
        return
    lineas = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for linea in f:
            registro = json.loads(linea)
            if registro["timestamp"] == timestamp:
                registro["feedback"] = feedback
            lineas.append(json.dumps(registro, ensure_ascii=False))
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
