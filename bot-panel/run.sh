#!/usr/bin/env bash
# =============================================
# Script de inicio del Bot Panel
# Crea el venv, instala dependencias y lanza Flask
# =============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_BIN="python3"

echo "=== Discord Bot Panel — Iniciando ==="

# Crear venv si no existe
if [ ! -d "$VENV_DIR" ]; then
    echo "[*] Creando entorno virtual..."
    $PYTHON_BIN -m venv "$VENV_DIR"
fi

# Activar venv
source "$VENV_DIR/bin/activate"

# Actualizar pip silenciosamente
pip install --upgrade pip -q

# Instalar dependencias si hay cambios
echo "[*] Verificando dependencias..."
pip install -r requirements.txt -q --no-warn-script-location

# Crear directorios necesarios
mkdir -p logs uploads backups bot_files instance

# Copiar .env si no existe
if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "[!] Se creó .env desde .env.example — configura tus credenciales."
fi

echo "[*] Iniciando panel en puerto ${PANEL_PORT:-5000}..."

# Producción con Gunicorn, desarrollo con Flask
if [ "${FLASK_ENV:-production}" = "development" ]; then
    python app.py
else
    exec gunicorn app:app \
        --bind "0.0.0.0:${PANEL_PORT:-5000}" \
        --workers 2 \
        --threads 2 \
        --worker-class gthread \
        --timeout 120 \
        --keep-alive 5 \
        --log-level info \
        --access-logfile - \
        --error-logfile -
fi
