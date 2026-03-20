#!/usr/bin/env bash

# Resolver el path real del script (soporta symlinks en macOS y Linux)
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  # Si $SOURCE es un path relativo, resolverlo respecto al path donde está el symlink
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

# Ir al directorio del proyecto sin importar desde dónde se llamó el comando
cd "$DIR"

if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "🎙️  Iniciando J.A.R.V.I.S. Daemon..."
    python core/server/jarvis_daemon.py
else
    echo "❌ Error: No se encontró el entorno virtual (.venv). Ejecuta ./install.sh primero."
    exit 1
fi
