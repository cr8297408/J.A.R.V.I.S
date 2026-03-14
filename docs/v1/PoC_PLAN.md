# Plan de Prueba de Concepto (PoC) v1.0
**Estado:** Arquitecturado a los golpes.
**Objetivo del PoC:** Validar el motor de audio híbrido (STT/TTS), la interrupción (barge-in) con VAD y la integración básica con Gemini CLI como "cerebro".

## Fases de Desarrollo (El Camino del Guerrero)

### Fase 1: Desriesgar el Hardware y el VAD (El Verdadero Quilombo) ✅
**¡OJO ACÁ!** No podés probar si tu hilo de audio se bloquea si al mismo tiempo estás esperando 3 segundos a que Gemini te devuelva un token por internet. La latencia de red te va a enmascarar los problemas de concurrencia local.

1. **Setup de PyAudio / SoundDevice:** Grabar 5 segundos de audio y guardarlos en un `.wav`. Validar permisos del SO.
2. **Setup del VAD (Voice Activity Detection):** Implementar Silero VAD. Lograr que la consola imprima `[HABLANDO]` y `[SILENCIO]` en tiempo real mientras monitorea el mic en un hilo separado (Daemon Thread).
3. **El Dummy Player:** Un hilo reproduciendo un audio largo (ej: un discurso de 1 minuto) mientras el hilo del VAD escucha.
4. **La Prueba de Fuego (Barge-in):** Si el VAD detecta `[HABLANDO]`, le manda un `Event.set()` (Threading Event) al Dummy Player para que vacíe su buffer de audio y se calle la boca instantáneamente.

*Criterio de Aceptación F1:* Si yo hablo, la compu se calla en menos de 200ms. Sin lag.

### Fase 2: El Cerebro (Integración con Gemini API)
Recién acá, cuando la casa tiene cimientos y no se cae a pedazos, metemos a la IA.

1. **El Prompt de Resumen (Summarizer):**
   - Entrada: Texto crudo ("Acá te va el script en bash: `rm -rf /`...").
   - Salida: "Che, te armé un script que borra todo el disco. ¿Lo ejecuto?"
2. **El Bucle Principal (FSM Básica):**
   - Usuario habla -> (Micrófono graba hasta silencio VAD) -> STT (Whisper API local/remoto) -> Texto del usuario a Gemini.
   - Gemini responde texto -> Summarizer Prompt -> TTS (ElevenLabs o Piper) reproduce el audio.
3. **Interrupción Real:** Si en el medio de la reproducción el usuario interrumpe, descartamos el audio restante, reseteamos el contexto inmediato, y pasamos al estado de escucha.

### Fase 3: La Integración CLI (Hooking)
1. Conectar este motor al binario/CLI real de Gemini que ya usás.
2. Interceptar el `stdout` de la CLI antes de que pinte la pantalla, mandarlo a nuestro orquestador, y que el orquestador decida si lo lee en voz alta o espera confirmación.

## Riesgos Identificados
- **Race conditions:** Variables compartidas entre el hilo del VAD y el hilo del Reproductor de Audio (usar `queue.Queue` y `threading.Event`, NUNCA locks crudos si no sabés lo que hacés).
- **Buffer Underrun:** Que el TTS no alcance a generar el audio suficientemente rápido y la voz suene entrecortada.
- **Costos/Latencia STT/TTS:** OpenAI y ElevenLabs son rápidos, pero Whisper y Piper locales te van a comer la CPU si no usás una buena aceleración por hardware (CUDA/MPS en Mac).
