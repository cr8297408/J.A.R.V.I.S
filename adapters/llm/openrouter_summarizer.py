import os
import json
import logging
from openai import AsyncOpenAI


class OpenRouterSummarizer:
    """
    Adaptador para la API de OpenRouter.
    Permite acceder a múltiples modelos gratuitos (como Llama 3 o Gemini Flash)
    con una sola API key y formato compatible con OpenAI.
    """

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("Falta la variable de entorno OPENROUTER_API_KEY.")

        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        # Puedes cambiar esto a "google/gemini-2.5-flash-free" o cualquier modelo :free
        self.model = os.getenv(
            "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"
        )

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
  "speech_content": "El texto exacto que dirás por TTS (vacío si should_speak es false)",
  "expects_response": true o false (siempre true si haces una pregunta o pides una decisión)
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
                extra_headers={
                    "HTTP-Referer": "https://github.com/cr8297408/J.A.R.V.I.S",
                    "X-Title": "JARVIS",
                },
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logging.error(f"Error en Jarvis Brain (OpenRouter): {e}")
            return {
                "reasoning": f"Fallback por error: {str(e)}",
                "should_speak": False,
                "speech_content": "",
                "expects_response": False,
            }

    async def evaluate_response(self, user_input: str, context: dict) -> dict:
        """
        Evalúa de forma inteligente la respuesta del usuario a una intervención de Jarvis.
        """
        last_speech = context.get("last_speech", "Ninguno")
        last_terminal = context.get("last_terminal_output", "Ninguna")

        prompt = f"""Eres la inteligencia central de JARVIS. Evalúa la respuesta del usuario a tu intervención anterior.
Tu intervención anterior: "{last_speech}"
Última salida de terminal: "{last_terminal}"
El usuario acaba de responder: "{user_input}"

Decide la acción más lógica:
1. "authorize": El usuario aprueba la ejecución (ej: "sí", "dale", "ok"). 
   - Retorna value: "1", "2" o "3" según corresponda.
2. "answer": El usuario hace una pregunta o pide aclaración.
   - Retorna value: (vacio, el flujo principal generará la respuesta).
3. "type": El usuario da una nueva orden o comando directo.
   - Retorna value: (el comando a ejecutar).
4. "ignore": Ruido o entrada no accionable.

Responde ÚNICAMENTE en JSON con el formato:
{{
  "action": "authorize|answer|type|ignore",
  "value": "string",
  "reasoning": "breve explicación"
}}
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres J.A.R.V.I.S., un agente de IA. Clasifica la intención del usuario.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                extra_headers={
                    "HTTP-Referer": "https://github.com/cr8297408/J.A.R.V.I.S",
                    "X-Title": "JARVIS",
                },
            )

            content = response.choices[0].message.content or "{}"
            return json.loads(content)

        except Exception as e:
            logging.error(f"Error evaluando respuesta (OpenRouter): {e}")
            return {
                "action": "answer",
                "value": "",
                "reasoning": f"Fallback por error: {str(e)}",
            }

    async def summarize_permission(self, details: dict) -> str:
        """
        Resume una solicitud de permiso de herramienta y evalúa riesgos usando OpenRouter.
        """
        prompt = f"""Analiza esta solicitud de permiso de Gemini CLI y genera un resumen natural para el usuario.
Detalles de la solicitud: {json.dumps(details)}

INSTRUCCIONES:
1. Identifica qué quiere hacer Gémini (ej: borrar, editar, ver archivos, buscar en internet).
2. Resume el propósito en una frase corta y amena.
3. **MENCIONA LA CARPETA/FOLDER**: Si la solicitud indica un directorio de trabajo (cwd), una ruta de archivo o el contexto permite deducir dónde se realizará la acción, menciónalo claramente (ej: "en la carpeta actual", "en el directorio src", "dentro de tu proyecto de eliox").
4. EVALUACIÓN DE RIESGO: Si la acción es potencialmente peligrosa (borrar archivos, instalar paquetes, modificar configuración crítica), menciónalo explícitamente y con precaución.
5. Dirígete al usuario como "Señor".
6. Termina SIEMPRE con una pregunta sobre si debe proceder, o pide que diga uno para permitir, dos para siempre o tres para denegar si es una autorización formal.
   Ejemplo: "Señor, Gemini quiere borrar el archivo temporal en la carpeta logs. Es una acción destructiva, ¿procedemos? Diga uno para permitir, dos para siempre o tres para denegar."

Responde ÚNICAMENTE con el texto que Jarvis debe decir por voz. Sin JSON, sin etiquetas.
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres J.A.R.V.I.S., el asistente personal. Resume permisos y evalúa riesgos.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                extra_headers={
                    "HTTP-Referer": "https://github.com/cr8297408/J.A.R.V.I.S",
                    "X-Title": "JARVIS",
                },
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"Error resumiendo permiso (OpenRouter): {e}")
            return "Señor, el sistema requiere su autorización para una acción de Gemini. Diga uno para permitir, dos para siempre o tres para denegar."
