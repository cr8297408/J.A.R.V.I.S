import os
import google.generativeai as genai
import logging
import json


class GeminiSummarizer:
    """
    Adaptador para la API de Gemini Flash.
    Su responsabilidad es actuar como el cerebro de J.A.R.V.I.S.,
    decidiendo si vale la pena interrumpir al usuario y qué decirle.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Falta la variable de entorno GEMINI_API_KEY.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

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
Debes responder ÚNICAMENTE con un objeto JSON válido con la siguiente estructura, sin backticks de markdown:
{
  "reasoning": "Tu análisis interno de por qué decides hablar o guardar silencio (simulación predictiva).",
  "should_speak": true o false,
  "speech_content": "El texto exacto que dirás por TTS (vacío si should_speak es false)",
  "expects_response": true o false (siempre true si haces una pregunta o pides una decisión)
}
"""

    async def evaluate_response(self, user_input: str, context: dict) -> dict:
        """
        Evalúa de forma inteligente la respuesta del usuario a una intervención de Jarvis.
        Contexto: last_speech (lo que dijo Jarvis), user_input (lo que dijo el usuario).
        """
        last_speech = context.get("last_speech", "")
        
        prompt = f"""
Eres la inteligencia central de JARVIS. Tu trabajo es evaluar la respuesta del usuario a tu intervención anterior.
Tu intervención anterior fue: "{last_speech}"
El usuario acaba de responder: "{user_input}"

Debes decidir la acción más lógica basándote en este intercambio:

1. SI el usuario está APROBANDO una ejecución (ej: "sí", "dale", "procede", "adelante", "ok", "hazlo"):
   - action: "authorize"
   - value: "1" (o el número correspondiente si había opciones)
   - reasoning: "El usuario aprueba la ejecución."

2. SI el usuario te está haciendo una pregunta de seguimiento o pidiendo una explicación:
   - action: "answer"
   - value: "" (deja vacío, el flujo principal generará la respuesta)
   - reasoning: "El usuario tiene una duda o pide más info."

3. SI el usuario está dando una nueva orden o comando:
   - action: "type"
   - value: (el comando a ejecutar, ej: "git status")
   - reasoning: "El usuario cambió de tema o dio una orden directa."

4. SI es ruido o no tiene sentido:
   - action: "ignore"
   - value: ""
   - reasoning: "Entrada no accionable."

Responde ÚNICAMENTE en JSON con el formato:
{{
  "action": "authorize|answer|type|ignore",
  "value": "string",
  "reasoning": "breve explicación"
}}
"""
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                ),
            )
            text = response.text.strip()
            return json.loads(text)
        except Exception as e:
            logging.error(f"Error evaluando respuesta con Gemini: {e}")
            return {"action": "answer", "value": "", "reasoning": f"Fallback por error: {e}"}

    async def summarize(self, raw_text: str, user_command: str = "") -> dict:
        prompt = f"{self.system_prompt}\n\n[ÚLTIMO COMANDO DEL USUARIO]:\n{user_command}\n\n[SALIDA CRUDA DE LA TERMINAL A EVALUAR]:\n{raw_text}\n\n[TU RESPUESTA EN JSON]:"
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                ),
            )
            result = json.loads(response.text.strip())
            return result
        except Exception as e:
            logging.error(f"Error en Jarvis Brain: {e}")
            return {
                "reasoning": f"Fallback por error: {str(e)}",
                "should_speak": False,
                "speech_content": "",
                "expects_response": False,
            }
