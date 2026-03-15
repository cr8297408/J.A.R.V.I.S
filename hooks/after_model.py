#!/usr/bin/env python3
import sys
import json
import socket

# Puerto local donde nuestro demonio Jarvis está escuchando
DAEMON_PORT = 49999
DAEMON_HOST = "127.0.0.1"


def main():
    # 1. Regla de Oro: Leer el JSON de sys.stdin silenciosamente
    try:
        raw_input = sys.stdin.read()
        print(
            f"[JARVIS HOOK DEBUG] Received {len(raw_input)} bytes from stdin",
            file=sys.stderr,
        )
        if not raw_input:
            # Si no hay entrada, salimos limpiamente para no crashear la CLI
            print(json.dumps({"decision": "allow"}))
            return 0

        payload = json.loads(raw_input)
    except Exception as e:
        # En caso de error, logeamos a stderr (NO a stdout!) y dejamos pasar a la CLI
        print(f"Error parseando stdin: {e}", file=sys.stderr)
        print(json.dumps({"decision": "allow"}))
        return 0

    # 2. Extraer el texto (chunk) de la respuesta del modelo si existe
    # El path según la doc: llm_response.candidates[0].content.parts[0]
    try:
        response_obj = payload.get("llm_response", {})
        candidates = response_obj.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                # Loggear las parts para ver cómo vienen estructuradas
                with open("/tmp/jarvis_payload_debug.log", "a") as f:
                    f.write(json.dumps(parts) + "\n")

                # TODO: Adaptar según si es dict o string
                if isinstance(parts[0], str):
                    chunk = parts[0]
                elif isinstance(parts[0], dict) and "text" in parts[0]:
                    # Some versions might send dicts
                    chunk = parts[0].get("text", "")
                else:
                    chunk = str(parts[0])

                # 3. Mandar el chunk al demonio Jarvis por socket TCP
                try:
                    with socket.create_connection(
                        (DAEMON_HOST, DAEMON_PORT), timeout=2.0
                    ) as sock:
                        # Mandamos el texto completo codificado en UTF-8
                        sock.sendall(chunk.encode("utf-8"))
                        # Cerramos la parte de escritura para enviar EOF
                        sock.shutdown(socket.SHUT_WR)
                        # Esperar un simple ACK del server (1 byte)
                        _ = sock.recv(1)
                except Exception as e:
                    print(
                        f"No me pude conectar al Demonio Jarvis: {e}. ¿Está corriendo?",
                        file=sys.stderr,
                    )
    except Exception as e:
        print(f"Error procesando el payload: {e}", file=sys.stderr)

    # 4. Devolver el control a la CLI de Gemini para que dibuje su TUI
    # Respetamos el contrato JSON exacto que espera la herramienta.
    output = {"decision": "allow"}

    # La salida final TIENE que ser puro JSON. Cero print/echo raros antes de esto.
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
