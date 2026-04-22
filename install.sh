#!/usr/bin/env bash
# J.A.R.V.I.S. Installer — 100% local, sin API keys, sin costo.
# Instala: Ollama + modelos Gemma 4, OpenCode, dependencias Python.

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

STEPS=7

_ok()   { echo -e "${GREEN}  ✓ $1${NC}"; }
_warn() { echo -e "${YELLOW}  ⚠ $1${NC}"; }
_fail() { echo -e "${RED}  ✗ $1${NC}"; }
_step() { echo -e "\n${CYAN}[$1/${STEPS}] $2${NC}"; }
_head() { echo -e "${BLUE}$1${NC}"; }

_head "======================================================"
_head "  J.A.R.V.I.S. — Asistente de voz 100% local"
_head "  Sin API keys. Sin internet. Sin costo."
_head "======================================================"
echo ""

START_DISK=$(df -k ~ | awk 'NR==2 {print $3}')
OS="$(uname -s)"


# ── 1. Sistema operativo y dependencias del sistema ───────────────────────────

_step 1 "Detectando SO e instalando dependencias del sistema..."

if [ "$OS" = "Darwin" ]; then
    _ok "macOS detectado"

    if ! command -v brew &> /dev/null; then
        _warn "Homebrew no está instalado. Instalándolo..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        if [ -x "/opt/homebrew/bin/brew" ]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv zsh)"' >> "$HOME/.zprofile"
            eval "$(/opt/homebrew/bin/brew shellenv zsh)"
        elif [ -x "/usr/local/bin/brew" ]; then
            echo 'eval "$(/usr/local/bin/brew shellenv zsh)"' >> "$HOME/.zprofile"
            eval "$(/usr/local/bin/brew shellenv zsh)"
        fi
    else
        _ok "Homebrew ya instalado"
    fi

    brew install portaudio ffmpeg 2>/dev/null || true
    _ok "portaudio y ffmpeg listos"

elif [ "$OS" = "Linux" ]; then
    _ok "Linux detectado"

    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y portaudio19-dev ffmpeg python3-venv python3-dev \
            python3-gi gir1.2-atspi-2.0 at-spi2-core 2>/dev/null || true
    elif command -v pacman &> /dev/null; then
        sudo pacman -Sy --noconfirm portaudio ffmpeg python-virtualenv at-spi2-core 2>/dev/null || true
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y portaudio-devel ffmpeg python3-virtualenv at-spi2-core 2>/dev/null || true
    else
        _warn "Gestor de paquetes no reconocido. Instalá portaudio manualmente."
    fi
    _ok "Dependencias del sistema listas"

else
    _fail "Sistema operativo no soportado: $OS"
    exit 1
fi


# ── 2. Python ─────────────────────────────────────────────────────────────────

_step 2 "Verificando Python..."

if ! command -v python3 &> /dev/null; then
    _fail "Python 3 no está instalado. Instalalo y volvé a correr este script."
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    _fail "Python $PY_VERSION detectado. Se requiere 3.10 o superior."
    exit 1
fi

_ok "Python $PY_VERSION"


# ── 3. Ollama ─────────────────────────────────────────────────────────────────

_step 3 "Instalando Ollama (servidor LLM local)..."

if ! command -v ollama &> /dev/null; then
    if [ "$OS" = "Darwin" ]; then
        brew install ollama 2>/dev/null || {
            _warn "Instalando Ollama via curl..."
            curl -fsSL https://ollama.com/install.sh | sh
        }
    else
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    _ok "Ollama instalado"
else
    _ok "Ollama ya instalado ($(ollama --version 2>/dev/null || echo 'versión desconocida'))"
fi

# Iniciar Ollama en background si no está corriendo
if ! curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    _warn "Iniciando Ollama en background..."
    ollama serve &>/tmp/ollama_install.log &
    OLLAMA_PID=$!
    sleep 3
    if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        _ok "Ollama iniciado (PID $OLLAMA_PID)"
    else
        _warn "Ollama no respondió. Inicialo manualmente con: ollama serve"
    fi
else
    _ok "Ollama ya está corriendo"
fi


# ── 4. Modelos de Ollama ──────────────────────────────────────────────────────

_step 4 "Descargando modelos Gemma 4 + Qwen Coder vía Ollama..."
echo -e "${YELLOW}  Esto puede tardar unos minutos según tu internet y GPU.${NC}"
echo ""

_pull_model() {
    local model="$1"
    local role="$2"
    echo -ne "  Descargando ${CYAN}${model}${NC} (${role})... "
    if ollama pull "$model" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠ falló — intentalo manualmente: ollama pull ${model}${NC}"
    fi
}

# Verificar si Ollama está disponible antes de intentar descargar
if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    _pull_model "gemma4:latest"         "GENERAL + PC CONTROL"
    _pull_model "qwen2.5-coder:latest"  "CODING"
else
    _warn "Ollama no está corriendo. Descargá los modelos luego:"
    echo "  ollama pull gemma4:latest"
    echo "  ollama pull qwen2.5-coder:latest"
fi


# ── 5. OpenCode ───────────────────────────────────────────────────────────────

_step 5 "Instalando OpenCode (agente de coding open-source)..."

if ! command -v opencode &> /dev/null; then
    if [ "$OS" = "Darwin" ]; then
        if command -v brew &> /dev/null; then
            brew install sst/tap/opencode 2>/dev/null && _ok "opencode instalado via brew" || {
                _warn "Brew tap falló. Intentando descarga directa..."
                _install_opencode_binary
            }
        else
            _install_opencode_binary
        fi
    elif [ "$OS" = "Linux" ]; then
        _install_opencode_binary
    fi
else
    _ok "opencode ya instalado"
fi

_install_opencode_binary() {
    local arch
    arch="$(uname -m)"
    local platform_str
    if [ "$OS" = "Darwin" ]; then
        if [ "$arch" = "arm64" ]; then
            platform_str="darwin_arm64"
        else
            platform_str="darwin_amd64"
        fi
    else
        platform_str="linux_amd64"
    fi

    OPENCODE_VERSION=$(curl -sf https://api.github.com/repos/sst/opencode/releases/latest | grep '"tag_name"' | cut -d'"' -f4 || echo "v0.1.0")
    OPENCODE_URL="https://github.com/sst/opencode/releases/download/${OPENCODE_VERSION}/opencode_${platform_str}.tar.gz"

    echo "  Descargando opencode ${OPENCODE_VERSION}..."
    if curl -fsSL "$OPENCODE_URL" | tar -xz -C /tmp && mv /tmp/opencode /usr/local/bin/opencode 2>/dev/null; then
        chmod +x /usr/local/bin/opencode
        _ok "opencode instalado en /usr/local/bin/opencode"
    else
        _warn "No se pudo instalar opencode automáticamente."
        echo "  Descargalo manualmente desde: https://github.com/sst/opencode/releases"
    fi
}


# ── 6. Entorno virtual de Python + dependencias ───────────────────────────────

_step 6 "Configurando entorno virtual Python e instalando dependencias..."

if [ -d ".venv" ]; then
    if ! .venv/bin/python3 -c "import sys" &> /dev/null; then
        _warn "Entorno virtual corrupto. Recreándolo..."
        rm -rf .venv
    else
        _ok "Entorno virtual .venv ya existe"
    fi
fi

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    _ok "Entorno virtual .venv creado"
fi

source .venv/bin/activate
pip install --upgrade pip -q

# Seleccionar requirements según el SO
if [ "$OS" = "Darwin" ]; then
    pip install -r requirements.txt -q
    # Accesibilidad macOS
    pip install pyobjc-framework-Cocoa pyobjc-framework-ApplicationServices -q 2>/dev/null || \
        _warn "pyobjc no instalado — el screen reader fallará en macOS. Instalá manualmente."
elif [ "$OS" = "Linux" ]; then
    # mlx-whisper solo funciona en Apple Silicon — usar faster-whisper en Linux
    grep -v "mlx-whisper" requirements.txt > /tmp/requirements_linux.txt
    echo "faster-whisper" >> /tmp/requirements_linux.txt
    echo "pyatspi" >> /tmp/requirements_linux.txt
    pip install -r /tmp/requirements_linux.txt -q
fi

_ok "Dependencias Python instaladas"


# ── 7. Configuración final ────────────────────────────────────────────────────

_step 7 "Configuración final..."

# Archivo .env
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        _ok ".env creado desde .env.example"
    else
        cat > .env << 'EOF'
# J.A.R.V.I.S. — Configuración local
# Sin API keys necesarias. Todo corre en tu máquina.

OLLAMA_HOST=http://localhost:11434

# Modelos (cambiá según lo que tengas instalado)
JARVIS_GENERAL_MODEL=gemma4:latest
JARVIS_PC_MODEL=gemma4:latest
JARVIS_CODE_MODEL=qwen2.5-coder:latest

# TTS / STT
ACTIVE_TTS_ENGINE=edge_tts
ACTIVE_STT_ENGINE=mlx_whisper
EOF
        _ok ".env creado con configuración por defecto"
    fi
else
    _ok ".env ya existe"
fi

# Instalar el CLI de jarvis como comando global
if pip show jarvis-voice 2>/dev/null | grep -q "Location" || \
   python3 -c "import jarvis" 2>/dev/null; then
    _ok "jarvis CLI ya instalado"
else
    pip install -e . -q 2>/dev/null && _ok "jarvis CLI instalado (pip install -e .)" || \
        _warn "No se pudo instalar el CLI. Usá: python main.py"
fi

# Descargar modelos de wake word
echo -e "\n${YELLOW}  Descargando modelos de wake word (openwakeword)...${NC}"
python3 -c "
try:
    from openwakeword.utils import download_models
    download_models()
    print('  \033[32m✓ Modelos de wake word listos\033[0m')
except Exception as e:
    print(f'  \033[33m⚠ Wake word: {e}\033[0m')
" 2>/dev/null || true


# ── Resumen ───────────────────────────────────────────────────────────────────

END_DISK=$(df -k ~ | awk 'NR==2 {print $3}')
DIFF_MB=$(( (END_DISK - START_DISK) / 1024 ))

echo ""
echo -e "${GREEN}======================================================"
echo -e "  ¡Instalación completada!"
echo -e "======================================================${NC}"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo -e "  1. Iniciá Ollama:          ${CYAN}ollama serve${NC}"
echo -e "  2. Verificá el sistema:    ${CYAN}jarvis doctor${NC}"
echo -e "  3. Iniciá Jarvis:          ${CYAN}jarvis start${NC}"
echo ""
echo -e "${YELLOW}Modos disponibles:${NC}"
echo -e "  ${CYAN}jarvis start --mode code${NC}    → Programar por voz con OpenCode"
echo -e "  ${CYAN}jarvis start --mode daemon${NC}  → Control completo del PC por voz"
echo ""
[ "$DIFF_MB" -gt 0 ] && echo -e "${GREEN}  Espacio ocupado: ~${DIFF_MB} MB${NC}"
echo ""
