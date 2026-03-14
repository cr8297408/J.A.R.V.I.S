# Estrategia de Buffering para Streams (Smart Chunking)
**Estado:** Definición Crítica
**Problema:** `gemini-cli` devuelve los datos por streaming (token a token). No podemos mandar tokens individuales ni al Resumidor (porque no tiene contexto) ni al TTS (porque sonaría cortado y robótico).

## El Dolor de Huevos del Streaming + Resumen
Si la CLI te está escupiendo un bloque de código de 200 líneas en tiempo real, nuestro sistema no puede empezar a hablar hasta saber qué carajo está haciendo ese código, para poder decirte: *"Che, te armé el script de Python"*.

## Solución: El 'Smart Context Buffer' (Buffer Inteligente)

Necesitamos un parser en tiempo real que lea el `stdout` de la CLI y decida cuándo tiene un "bloque lógico" completo para procesar.

### Reglas de la Máquina de Estados del Buffer:

1. **Modo Texto Normal (Conversacional):**
   - Va acumulando tokens.
   - Cuando detecta un delimitador de final de oración (`.`, `?`, `!`, o `\n\n`), agarra ese chunk y lo manda directo al TTS (o a un summarizer ultra rápido si es muy largo).
   - *Beneficio:* Baja latencia percibida. Empieza a hablarte mientras Gemini sigue pensando el resto.

2. **Modo Código (Bloqueo por Markdown):**
   - Si en el stream detecta la apertura de un bloque de código (`` ``` ``), **CAMBIA DE MODO**.
   - Deja de mandar al TTS. Empieza a acumular TODO el texto silenciosamente en memoria.
   - Recién cuando detecta el cierre del bloque de código (`` ``` ``), agarra todo ese choclo de código y se lo manda al **LLM Resumidor**.
   - El Resumidor lee el código y genera la frase corta: *"Acá tenés la función de React con los hooks. ¿Te la leo o la guardamos?"*
   - Esa frase corta va al TTS.

3. **Interrupción (Barge-in) durante el Streaming:**
   - Si el usuario interrumpe (habla) MIENTRAS Gemini CLI sigue stremeando texto, J.A.R.V.I.S. manda un `SIGINT` (Ctrl+C) al proceso PTY de Gemini para cortarle el chorro, limpia los buffers y se pone a escuchar la nueva instrucción.

## Resumen Arquitectónico
El Hilo Lector (Reader Thread) del PTY no es tonto. Es un lexer básico que entiende Markdown al vuelo para separar lo que es "charla" (se habla casi en tiempo real) de lo que es "código/datos pesados" (se espera, se resume y luego se habla).
