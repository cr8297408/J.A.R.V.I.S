import asyncio
import threading
import sys
import os

# Agregamos el root del proyecto al PYTHONPATH para poder importar las carpetas sin quilombos
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from core.lexer.poc_lexer import StreamingLexer, mock_gemini_stream
from adapters.llm.gemini_summarizer import GeminiSummarizer
from adapters.tts.mac_say_tts import MacSayTTS

# Evento global para la interrupción (en el futuro esto lo disparará el hilo del VAD de la Fase 1)
global_interrupt_event = threading.Event()


async def main():
    print("=== Iniciando Fase 3: Lexer -> LLM -> TTS ===\n")

    lexer = StreamingLexer()
    summarizer = GeminiSummarizer()
    tts = MacSayTTS()

    async for token in mock_gemini_stream():
        # 1. Imprimimos el token simulando la terminal de Gemini
        print(token, end="", flush=True)

        # 2. Pasamos el token por la máquina de estados del Lexer
        chunk_type, chunk_content = await lexer.process_token(token)

        if chunk_type == "TEXT_CHUNK":
            print(f"\n\n[🎤 HABLANDO TEXTO NORMAL] -> '{chunk_content}'")
            # Ejecutamos el TTS de Mac en un hilo bloqueante (o lo esperamos)
            # En la vida real, mandaríamos esto a una Queue manejada por un hilo de Audio para no trabar el Async.
            # Por ahora, para la PoC, lo ejecutamos directo.
            tts.speak(chunk_content, global_interrupt_event)
            print("\n", end="", flush=True)

        elif chunk_type == "CODE_BLOCK":
            print(f"\n\n[🧠 TRADUCIENDO CÓDIGO CON GEMINI FLASH...]")
            try:
                # 3. Mandamos el bloque de código al LLM
                resumen_humano = await summarizer.summarize(chunk_content)
                print(f"[🤖 RESUMEN RECIBIDO] -> '{resumen_humano}'")

                # 4. Lo hablamos
                tts.speak(resumen_humano, global_interrupt_event)
                print("\n", end="", flush=True)
            except Exception as e:
                print(f"\n[❌ ERROR DEL LLM] -> {e}")


if __name__ == "__main__":
    asyncio.run(main())
