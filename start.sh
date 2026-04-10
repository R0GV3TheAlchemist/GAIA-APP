#!/bin/bash
# GAIA Launch Script — starts both the Python backend and Vite frontend
# Usage: bash start.sh

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}⬡ GAIA Starting...${NC}"
echo ""

# ------------------------------------------------------------------ #
#  Checks                                                              #
# ------------------------------------------------------------------ #

if ! command -v python &> /dev/null; then
    echo -e "${RED}ERROR: Python not found. Install Python 3.11+${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}ERROR: Node.js not found. Install Node.js 18+${NC}"
    exit 1
fi

# ------------------------------------------------------------------ #
#  Kill stale processes on our ports (Windows Git Bash compatible)     #
# ------------------------------------------------------------------ #

echo -e "${BLUE}▶ Clearing stale ports...${NC}"
# Use netstat + taskkill (works on Windows Git Bash / MINGW64)
for PORT in 8008 5173 1420; do
    PID=$(netstat -ano 2>/dev/null | grep ":${PORT} " | grep LISTENING | awk '{print $NF}' | head -1)
    if [ -n "$PID" ]; then
        taskkill //PID $PID //F &>/dev/null || true
        echo -e "  Cleared port ${PORT} (PID $PID)"
    fi
done
sleep 1

# ------------------------------------------------------------------ #
#  Ollama                                                              #
# ------------------------------------------------------------------ #

if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}WARNING: Ollama not found. LLM synthesis will use fallback mode.${NC}"
else
    echo -e "${BLUE}▶ Starting Ollama...${NC}"
    ollama serve &>/dev/null &
    sleep 2
    echo -e "  Ollama ready."
fi

# ------------------------------------------------------------------ #
#  Python Backend                                                      #
# ------------------------------------------------------------------ #

echo -e "${BLUE}▶ Starting GAIA backend (port 8008)...${NC}"
# Run as a module so 'from core.x import y' resolves correctly
python -m core.server &
BACKEND_PID=$!
echo -e "  Backend PID: ${BACKEND_PID}"
sleep 3

if kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "  ${GREEN}Backend is alive ✓${NC}"
else
    echo -e "  ${RED}Backend failed. Check errors above.${NC}"
fi

# ------------------------------------------------------------------ #
#  Vite Frontend                                                       #
# ------------------------------------------------------------------ #

echo -e "${BLUE}▶ Starting GAIA frontend...${NC}"
npm run dev &
FRONTEND_PID=$!
echo -e "  Frontend PID: ${FRONTEND_PID}"
sleep 2

# ------------------------------------------------------------------ #
#  Ready                                                               #
# ------------------------------------------------------------------ #

echo ""
echo -e "${GREEN}✅ GAIA is running!${NC}"
echo -e "  Frontend: ${BLUE}http://localhost:5173${NC}"
echo -e "  Backend:  ${BLUE}http://127.0.0.1:8008${NC}"
echo -e "  Status:   ${BLUE}http://127.0.0.1:8008/status${NC}"
echo -e "  GAIANs:   ${BLUE}http://127.0.0.1:8008/gaians${NC}"
echo ""
echo -e "Press ${YELLOW}Ctrl+C${NC} to stop everything."

trap "echo ''; echo -e '${YELLOW}Shutting down GAIA...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

wait
