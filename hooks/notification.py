#!/usr/bin/env python3
import sys
import json
import socket

DAEMON_PORT = 49999
DAEMON_HOST = "127.0.0.1"

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            print(json.dumps({"decision": "allow"}))
            return 0
            
        payload = json.loads(raw_input)
        
        # Filtrar si es ToolPermission u otro que nos interesa
        if payload.get("notification_type") == "ToolPermission":
            try:
                with socket.create_connection((DAEMON_HOST, DAEMON_PORT), timeout=1.0) as sock:
                    msg = f"__NOTIFICATION__{json.dumps(payload)}\n".encode("utf-8")
                    sock.sendall(msg)
                    _ = sock.recv(1)
            except Exception as e:
                pass
                
    except Exception as e:
        pass
        
    print(json.dumps({"decision": "allow"}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
