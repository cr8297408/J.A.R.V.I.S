import asyncio
import time


class StreamingLexer:
    """
    Simula ser el 'Interceptor' de la salida de Gemini CLI.
    Recibe tokens en tiempo real y decide cuándo tiene un bloque lógico
    con sentido para mandarlo a la Voz (TTS) o al Resumidor de Código.
    """

    def __init__(self):
        self.buffer = ""
        self.in_code_block = False
        self.delimiters = [".", "?", "!", "\n"]

    async def process_token(self, token: str):
        """
        Recibe un token (pedacito de string) y devuelve una tupla:
        (TIPO_DE_CHUNK, CONTENIDO) o (None, None) si todavía está acumulando.
        """
        self.buffer += token

        # Caso 1: Estamos adentro de un bloque de código acumulando silencio
        if self.in_code_block:
            # Buscamos si el token trajo el cierre del bloque (tres backticks)
            # Ojo: el stream puede cortar los backticks por la mitad (ej: "``" y luego "`")
            # Por eso buscamos en TODO el buffer, no solo en el token.
            if "```" in self.buffer:
                # ¡Terminó el código! Separamos lo que es código de lo que viene después.
                parts = self.buffer.split("```", 1)
                code_content = parts[0].strip()

                # Reseteamos el estado
                self.in_code_block = False
                self.buffer = parts[1] if len(parts) > 1 else ""

                return "CODE_BLOCK", code_content
            else:
                # Seguimos acumulando código en silencio. No devolvemos nada al TTS.
                return None, None

        # Caso 2: Estamos en modo TEXTO normal (Charla)
        else:
            # ¿Apareció un inicio de bloque de código?
            if "```" in self.buffer:
                parts = self.buffer.split("```", 1)
                text_before_code = parts[0].strip()

                # Entramos en modo pánico/silencio
                self.in_code_block = True
                self.buffer = parts[1] if len(parts) > 1 else ""

                # Si había texto acumulado ANTES de los backticks, lo mandamos a hablar ya mismo
                if text_before_code:
                    return "TEXT_CHUNK", text_before_code
                return None, None

            # ¿Encontramos un final de oración para que el TTS empiece a hablar?
            # Buscamos el ÚLTIMO delimitador en el buffer para asegurar oraciones largas.
            last_delimiter_idx = -1
            for d in self.delimiters:
                idx = self.buffer.rfind(d)
                if idx > last_delimiter_idx:
                    last_delimiter_idx = idx

            if last_delimiter_idx != -1:
                # Cortamos el buffer en ese delimitador
                chunk_to_speak = self.buffer[: last_delimiter_idx + 1].strip()
                self.buffer = self.buffer[last_delimiter_idx + 1 :]

                if chunk_to_speak:
                    return "TEXT_CHUNK", chunk_to_speak

            # Si no hay puntuación, seguimos acumulando letras
            return None, None


async def mock_gemini_stream():
    """Simula la API de Gemini tirando tokens con latencia de red."""
    mock_response = [
        "Hola ",
        "guacho. ",
        "Acá ",
        "tenés ",
        "el ",
        "script ",
        "de ",
        "Python ",
        "que ",
        "pediste.\n\n",
        "```python\n",
        "import os\n",
        "def borrar_todo():\n",
        "    os.system('rm -rf /')\n",
        "borrar_todo()\n",
        "```\n",
        "Avisame ",
        "si ",
        "querés ",
        "que ",
        "lo ",
        "ejecute ",
        "o ",
        "si ",
        "lo ",
        "guardamos.",
    ]

    for token in mock_response:
        # Simulamos la latencia asquerosa de internet (entre 50ms y 200ms por token)
        await asyncio.sleep(0.1)
        yield token


async def main():
    print("=== Iniciando Prueba de Lexer (Smart Chunking) ===\n")
    lexer = StreamingLexer()

    # Consumimos el stream asíncrono
    async for token in mock_gemini_stream():
        # Imprimimos lo que "ve" la terminal (opcional, para debug visual)
        print(token, end="", flush=True)

        chunk_type, chunk_content = await lexer.process_token(token)

        if chunk_type == "TEXT_CHUNK":
            print(f"\n\n[🎤 ENVIANDO AL TTS (Latencia Baja)] -> '{chunk_content}'\n")
        elif chunk_type == "CODE_BLOCK":
            print(
                f"\n\n[🧠 ENVIANDO AL RESUMIDOR (Bloque Gigante)] -> \n{chunk_content}\n"
            )
            # Acá es donde J.A.R.V.I.S llamaría a la otra IA para resumir esto en una frase corta
            print(
                f"[🤖 RESUMEN FALSO GENERADO] -> 'Te armé una función en Python que te borra el disco duro.'\n"
            )


if __name__ == "__main__":
    asyncio.run(main())
