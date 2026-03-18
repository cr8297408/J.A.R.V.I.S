import os
import json
import logging
from groq import AsyncGroq


class GroqSummarizer:
    """
    Adaptador para la API de Groq (Llama 3.3).
    Actúa como el cerebro rápido de Jarvis usando una API compatible con OpenAI.
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Falta la variable de entorno GROQ_API_KEY.")

        self.client = AsyncGroq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

        self.system_prompt = """
Eres J.A.R.V.I.S. (Just A Rather Very Intelligent System), un agente de IA de ciclo completo y asistente personal del creador.
Actúas como una Interfaz de Pensamiento Aumentado: tu objetivo principal es filtrar el "ruido cognitivo" y evitar la fatiga de decisión del usuario.

REGLAS DE INTERVENCIÓN VOCAL (Cuándo hablar):
1. EVALÚA la salida de la terminal en relación al [ÚLTIMO COMANDO DEL USUARIO]. Si la salida resuelve su petición final, o si le pide una decisión (ej. confirmar un comando, falta de permisos), o si hay un fallo, HABLA.
2. NUNCA hables durante la planificación inicial, pasos intermedios que no resuelven la petición, uso de herramientas en background (ej. leyendo archivos sin errores, buscando en internet) o si solo estás "pensando" (etiquetas <thought> o <think>). Mantente en silencio en estos casos.
3. Si la respuesta contiene tanto un pensamiento interno como un mensaje directo al usuario, IGNORA el pensamiento y resume/di SÓLO el mensaje final dirigido al usuario.

PERSONALIDAD Y TONO:
- Profesional, directo, latencia percibida cero (respuestas EXTREMADAMENTE cortas, máximo 1-2 oraciones).
- Ligeramente sarcástico u honesto de forma técnica si es apropiado.
- Dirígete al usuario como "Señor".
- NUNCA leas código, rutas de archivos largas, asteriscos, ni uses formato markdown. Habla como lo haría un humano.

FORMATO DE SALIDA ESTRICTO (JSON):
Debes responder ÚNICAMENTE con un objeto JSON válido con la siguiente estructura:
{
  "reasoning": "Tu análisis interno de por qué decides hablar o guardar silencio.",
  "should_speak": true o false,
  "speech_content": "El texto exacto que dirás por TTS (vacío si should_speak es false)"
}
"""

    async def summarize(self, raw_text: str, user_command: str = "") -> dict:
        prompt = f"[ÚLTIMO COMANDO DEL USUARIO]:\n{user_command}\n\n[SALIDA CRUDA DE LA TERMINAL A EVALUAR]:\n{raw_text}\n\nAnaliza esta salida y responde ÚNICAMENTE con JSON válido."

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            content = response.choices[0].message.content or "{}"
            return json.loads(content)

        except Exception as e:
            logging.error(f"Error en Jarvis Brain (Groq): {e}")
            return {
                "reasoning": f"Fallback por error: {str(e)}",
                "should_speak": False,
                "speech_content": "",
            }

    async def evaluate_intent(self, user_input: str, context: dict) -> dict:
        """
        Evalúa si la entrada del usuario debe ser inyectada en la terminal
        o si puede ser respondida directamente basándose en el contexto reciente.
        """
        last_speech = context.get("last_speech", "Ninguno")
        last_terminal = context.get("last_terminal_output", "Ninguna")

        prompt = f"""El usuario acaba de decirte: "{user_input}"

[CONTEXTO RECIENTE]
Última salida de la terminal: {last_terminal}
Lo último que tú le dijiste al usuario: {last_speech}

Decide la siguiente acción:
A) "speak_directly": El usuario te está haciendo una pregunta de seguimiento directo, pidiendo aclaración, o charlando sobre lo que le acabas de decir. Puedes responderle directamente basándote en el contexto reciente SIN necesidad de escribir nada en la terminal.
B) "type_in_terminal": El usuario te está pidiendo que hagas algo nuevo, busques información nueva, o ejecutes un comando (ej. "profundiza en X" (si no está en el texto), "busca Y", "crea un archivo"). Debes pasarlo a la terminal.

Responde ÚNICAMENTE con JSON válido:
{{
  "action": "speak_directly" o "type_in_terminal",
  "reasoning": "Tu razonamiento corto",
  "direct_response": "Tu respuesta hablada (solo si action es speak_directly, si no vacío)"
}}
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres J.A.R.V.I.S., un agente de IA. Debes clasificar la intención del usuario.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )

            content = response.choices[0].message.content or "{}"
            return json.loads(content)

        except Exception as e:
            logging.error(f"Error evaluando intención (Groq): {e}")
            return {
                "action": "type_in_terminal",
                "reasoning": f"Fallback por error: {str(e)}",
                "direct_response": "",
            }
        prompt = f"[ÚLTIMO COMANDO DEL USUARIO]:\n{user_command}\n\n[SALIDA CRUDA DE LA TERMINAL A EVALUAR]:\n{raw_text}\n\nAnaliza esta salida y responde ÚNICAMENTE con JSON válido."

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logging.error(f"Error en Jarvis Brain (Groq): {e}")
            return {
                "reasoning": f"Fallback por error: {str(e)}",
                "should_speak": False,
                "speech_content": "",
            }
