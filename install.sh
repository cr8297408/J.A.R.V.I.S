#!/usr/bin/env bash

set -e

# Colores para los mensajes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  J.A.R.V.I.S. (Gemini Speech Extension) Installer  ${NC}"
echo -e "${BLUE}======================================================${NC}\n"

# 1. Detectar el Sistema Operativo
OS="$(uname -s)"
echo -e "${YELLOW}[1/5] Detectando Sistema Operativo...${NC}"
if [ "$OS" = "Darwin" ]; then
    echo -e "${GREEN}-> macOS detectado.${NC}"
    
    # Comprobar Homebrew
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}Homebrew no está instalado. Instalándolo ahora...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo -e "${GREEN}-> Homebrew ya está instalado.${NC}"
    fi

    echo -e "${YELLOW}Instalando dependencias del sistema (portaudio)...${NC}"
    brew install portaudio

elif [ "$OS" = "Linux" ]; then
    echo -e "${GREEN}-> Linux detectado.${NC}"
    
    # Detectar el gestor de paquetes
    if command -v apt-get &> /dev/null; then
        echo -e "${YELLOW}Instalando dependencias del sistema (portaudio19-dev, python3-venv)...${NC}"
        sudo apt-get update
        sudo apt-get install -y portaudio19-dev python3-venv python3-dev
    elif command -v pacman &> /dev/null; then
        echo -e "${YELLOW}Instalando dependencias del sistema (portaudio)...${NC}"
        sudo pacman -Sy --noconfirm portaudio python-virtualenv
    elif command -v dnf &> /dev/null; then
        echo -e "${YELLOW}Instalando dependencias del sistema (portaudio-devel)...${NC}"
        sudo dnf install -y portaudio-devel python3-virtualenv
    else
        echo -e "${RED}Gestor de paquetes no soportado automáticamente. Por favor instala 'portaudio' manualmente.${NC}"
        exit 1
    fi
else
    echo -e "${RED}Sistema operativo no soportado por este instalador ($OS).${NC}"
    exit 1
fi

# 2. Comprobar Node.js y npm (para gemini-cli)
echo -e "\n${YELLOW}[2/5] Comprobando Node.js...${NC}"
if ! command -v npm &> /dev/null; then
    echo -e "${RED}npm no está instalado. J.A.R.V.I.S. requiere Node.js para el gemini-cli.${NC}"
    echo -e "Por favor instala Node.js (https://nodejs.org) y vuelve a ejecutar este script."
    exit 1
else
    echo -e "${GREEN}-> Node.js y npm detectados.${NC}"
fi

# 3. Instalar Gemini CLI globalmente si no está
echo -e "\n${YELLOW}[3/5] Instalando @google/generative-ai-cli...${NC}"
if ! command -v gemini &> /dev/null; then
    npm install -g @google/generative-ai-cli
    echo -e "${GREEN}-> gemini-cli instalado globalmente.${NC}"
else
    echo -e "${GREEN}-> gemini-cli ya está instalado.${NC}"
    # Opcional: npm update -g @google/generative-ai-cli
fi

# 4. Configurar Entorno Virtual de Python
echo -e "\n${YELLOW}[4/5] Configurando Entorno Virtual (Python)...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 no está instalado. Por favor instálalo y vuelve a intentar.${NC}"
    exit 1
fi

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}-> Entorno virtual '.venv' creado.${NC}"
else
    echo -e "${GREEN}-> Entorno virtual '.venv' ya existe.${NC}"
fi

# 5. Instalar Dependencias de Python
echo -e "\n${YELLOW}[5/5] Instalando dependencias de Python en .venv...${NC}"
source .venv/bin/activate
pip install --upgrade pip

# Si mlx-whisper falla en Linux, instalamos openai-whisper
if [ "$OS" = "Linux" ]; then
    echo -e "${YELLOW}Nota: MLX Whisper es específico de Apple Silicon. En Linux se usará una alternativa si es necesario, o fallará si mlx está hardcodeado. Adaptando dependencias...${NC}"
    # Esto es solo un warning, el requirements.txt se instalará normal,
    # pero mlx requiere macOS. En una app real de producción cambiaríamos la dependencia dinámicamente.
fi

pip install -r requirements.txt
echo -e "${GREEN}-> Dependencias de Python instaladas correctamente.${NC}"

# Configurar archivo .env
echo -e "\n${YELLOW}Configurando archivo .env...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}-> Archivo .env creado a partir de .env.example.${NC}"
    else
        touch .env
        echo -e "${GREEN}-> Archivo .env creado vacío.${NC}"
    fi
else
    echo -e "${GREEN}-> Archivo .env ya existe.${NC}"
fi

# 6. Crear el alias global "jarvis"
echo -e "\n${YELLOW}[6/6] Configurando comando global 'jarvis'...${NC}"
if [ -w "/usr/local/bin" ]; then
    ln -sf "$(pwd)/start.sh" /usr/local/bin/jarvis
    echo -e "${GREEN}-> Comando global 'jarvis' enlazado en /usr/local/bin.${NC}"
else
    echo -e "${YELLOW}Se requieren permisos de administrador (sudo) para crear el comando global en /usr/local/bin.${NC}"
    sudo ln -sf "$(pwd)/start.sh" /usr/local/bin/jarvis
    echo -e "${GREEN}-> Comando global 'jarvis' creado exitosamente.${NC}"
fi

echo -e "\n${GREEN}======================================================${NC}"
echo -e "${GREEN}  ¡Instalación Completada Exitosamente!  ${NC}"
echo -e "${GREEN}======================================================${NC}"
echo -e "\n${YELLOW}Próximos pasos:${NC}"
echo -e "1. Abre el archivo ${BLUE}.env${NC} y añade tus API Keys (GROQ_API_KEY, OPENROUTER_API_KEY, etc)."
echo -e "2. Asegúrate de tener los hooks de Gemini CLI configurados para apuntar a 'hooks/notification.py'."
echo -e "3. Ya puedes iniciar J.A.R.V.I.S. desde CUALQUIER carpeta escribiendo: ${BLUE}jarvis${NC}"
echo -e "======================================================\n"
