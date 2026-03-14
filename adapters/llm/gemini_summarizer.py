import os
import google.generativeai as genai


class GeminiSummarizer:
    """
    Adaptador para la API de Gemini.
    Su única responsabilidad es agarrar choclos de código y traducirlos
    a un lenguaje humano, corto y al pie.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "¡Pará, boludo! Te falta la variable de entorno GEMINI_API_KEY."
            )

        genai.configure(api_key=api_key)
        # Usamos flash porque necesitamos VELOCIDAD. Si querés calidad para pensar, usamos pro en el cerebro principal.
        # Para resumir código al vuelo, flash es el campeón.
        self.model = genai.GenerativeModel("gemini-2.5-flash")

        self.system_prompt = """
        Sos la voz de J.A.R.V.I.S., un asistente de terminal. 
        Te voy a pasar un bloque de código técnico o un output crudo.
        Tu ÚNICO trabajo es resumir qué hace ese código en MÁXIMO 2 ORACIONES muy cortas 
        y con tono conversacional (podés usar lunfardo argentino moderado).
        
        REGLAS ESTRICTAS:
        - NUNCA leas código literal (nada de "import", "llaves", "funciones").
        - NUNCA des explicaciones largas.
        - Sé directo.
        
        EJEMPLO DE ENTRADA: 
        ```javascript
        console.log("hola");
        ```
        EJEMPLO DE SALIDA: "Te armé el script de Javascript que imprime un saludo en consola. ¿Lo ejecutamos?"
        """

    async def summarize(self, code_block: str) -> str:
        prompt = f"{self.system_prompt}\n\n[CÓDIGO A RESUMIR]:\n{code_block}"
        # Llamada asíncrona para no bloquear el Hilo Principal de la terminal
        response = await self.model.generate_content_async(prompt)
        return response.text.strip()
