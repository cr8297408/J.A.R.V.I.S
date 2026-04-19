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
Eres J.A.R.V.I.S., asistente de voz para una persona con DISCAPACIDAD VISUAL TOTAL.
El usuario NO puede ver ninguna pantalla. Lo que el LLM responde DEBE ser narrado oralmente.

── PASO 1: DETECTÁ EL TIPO DE PETICIÓN ──────────────────────────────────────
Analizá el [ÚLTIMO COMANDO DEL USUARIO] y clasificalo:

• EXPLICAR  → pide comprensión: "explícame", "qué es", "describí", "contame", "cómo funciona",
              "qué dice", "qué tiene", "qué son", "qué hace", "dame un resumen de", "cuáles son"
• EJECUTAR  → orden a realizar: "instalá", "creá", "borrá", "editá", "corré", "hacé", "commitear", "mostrá"
• ESTADO    → pide resultado: "cómo va", "qué pasó", "hay errores", "terminó", "qué hay"
• RESPUESTA → responde a Jarvis: "sí", "no", "dale", "uno", "dos", "tres", "ok", "correcto"

── PASO 2: REGLAS POR TIPO ───────────────────────────────────────────────────

EXPLICAR → SIEMPRE hablar aunque la salida sea larga.
  El usuario NECESITA escuchar la explicación porque no puede verla.
  Narrá los puntos clave de forma fluida y oral, como un locutor describiendo una pantalla.
  No leas código ni rutas de archivos. Describí conceptos, propósitos y resultados.
  Usá 4-8 oraciones si el contenido lo justifica.
  NO preguntes "¿desea continuar?" ni "¿quiere empezar?". Simplemente explicá el contenido.

EJECUTAR → Hablar SOLO si:
  a) La tarea completó exitosamente → una oración de confirmación.
  b) Hay un error → describir brevemente.
  c) Se requiere una decisión → presentarla.
  Silencio durante: planificación, búsqueda de archivos, pasos intermedios sin resultado final.

ESTADO → Hablar siempre. Resumir en 2-3 oraciones: qué pasó, si hay errores, si se necesita algo.

RESPUESTA → Hablar solo si la acción ejecutada tuvo un resultado relevante (éxito, error, nueva decisión).

── SIEMPRE EN SILENCIO ────────────────────────────────────────────────────────
• Pensamientos internos (<thought>, <think>)
• Herramientas en background sin errores (leyendo archivos, buscando sin resultado aún)
• Planificación inicial sin resultado final todavía

── PERSONALIDAD ──────────────────────────────────────────────────────────────
• Profesional y directo. Dirigite al usuario como "Señor".
• Para EXPLICAR: hablá como un locutor. Fluido, completo, humano.
• Para otros tipos: muy conciso (1-2 oraciones).
• NUNCA leas: código fuente, rutas de archivos, asteriscos, markdown, símbolos técnicos.

── FORMATO JSON ESTRICTO (sin backticks) ────────────────────────────────────
{
  "intent_type": "EXPLICAR|EJECUTAR|ESTADO|RESPUESTA|DESCONOCIDO",
  "reasoning": "análisis interno de la decisión",
  "should_speak": true|false,
  "speech_content": "texto exacto para TTS (vacío si should_speak es false)"
}
"""

    async def evaluate_response(self, user_input: str, context: dict) -> dict:
        """
        Evalúa de forma inteligente la respuesta del usuario a una intervención de Jarvis.
        Contexto: last_speech (lo que dijo Jarvis), user_input (lo que dijo el usuario).
        """
        last_speech = context.get("last_speech", "")
        
        prompt = f"""Eres la inteligencia central de JARVIS (asistente para usuario con discapacidad visual).
CONTEXTO:
- Lo que JARVIS dijo antes: "{last_speech}"
- Lo que el usuario acaba de decir: "{user_input}"

CRITERIOS (en orden de prioridad):

1. "authorize" — El usuario APRUEBA o ACEPTA algo.
   Señales: "sí", "dale", "ok", "adelante", "procede", "uno", "dos", "tres", "hazlo", "correcto".
   value: "1", "2" o "3" si hay opciones numeradas, sino "1".

2. "type" — El usuario da una orden o comando NUEVO y distinto al contexto actual.
   Señales: verbo imperativo nuevo, tema diferente al de JARVIS.
   value: el comando exacto como lo dijo el usuario.

3. "answer" — El usuario hace una pregunta, pide aclaración, o reformula lo que JARVIS dijo.
   Señales: pregunta directa, "qué es", "explicame", "por qué", "cómo", NO entendió la respuesta anterior,
   repite o reformula lo que JARVIS dijo (quiere que se lo expliquen mejor).
   REGLA CLAVE: si el usuario repitió o parafraseó la pregunta de JARVIS → "answer", NUNCA "ignore".
   value: "" (vacío).

4. "ignore" — SOLO ruido puro: palabras sueltas sin sentido, onomatopeyas, silencio transcrito mal.
   NUNCA uses "ignore" si el usuario formuló una oración completa o hizo una pregunta.

Respondé ÚNICAMENTE en JSON:
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

    async def summarize_permission(self, details: dict) -> str:
        """
        Resume una solicitud de permiso de herramienta y evalúa riesgos usando Gemini.
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
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logging.error(f"Error resumiendo permiso (Gemini): {e}")
            return "Señor, el sistema requiere su autorización para una acción de Gemini. Diga uno para permitir, dos para siempre o tres para denegar."
