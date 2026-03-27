#!/bin/bash

set -euo pipefail

PORT="${1:-${SMARTDRIVE_PORT:-8001}}"
HOST="${2:-${SMARTDRIVE_HOST:-0.0.0.0}}"
BASE_MOUNT_ARG="${3:-}"

if [[ -n "$BASE_MOUNT_ARG" ]]; then
	export SMARTDRIVE_BASE_MOUNT="$BASE_MOUNT_ARG"
fi

if [[ ! "$PORT" =~ ^[0-9]+$ ]]; then
	echo "Error: el puerto debe ser numérico. Valor recibido: $PORT"
	echo "Uso: ./start.sh [PORT] [HOST] [BASE_MOUNT]"
	exit 1
fi

if [[ "$PORT" == "8000" ]]; then
	REQUIRE_MAIN_ON_8000="${SMARTDRIVE_REQUIRE_MAIN_ON_8000:-1}"
	if [[ "$REQUIRE_MAIN_ON_8000" =~ ^(1|true|TRUE|yes|YES|on|ON)$ ]]; then
		if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
			CURRENT_BRANCH="$(git branch --show-current 2>/dev/null || true)"
			if [[ "$CURRENT_BRANCH" != "main" ]]; then
				echo "Error: el puerto 8000 está reservado para la rama main."
				echo "Rama actual: ${CURRENT_BRANCH:-desconocida}"
				echo "Usa otro puerto para desarrollo (ej: ./start.sh 8001)."
				exit 1
			fi
		fi
	fi
fi

if ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq ":${PORT}$"; then
	echo "Error: el puerto $PORT ya está en uso."
	echo "Prueba con otro puerto: ./start.sh 8001"
	exit 1
fi

if [[ -n "${SMARTDRIVE_BASE_MOUNT:-}" ]]; then
	mkdir -p "$SMARTDRIVE_BASE_MOUNT/inbox" "$SMARTDRIVE_BASE_MOUNT/files"
fi

echo "Iniciando Smart Drive en http://${HOST}:${PORT}..."
if [[ "$HOST" == "0.0.0.0" ]]; then
	LOCAL_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
	if [[ -n "$LOCAL_IP" ]]; then
		echo "Acceso LAN: http://${LOCAL_IP}:${PORT}"
	fi
else
	echo "Acceso local: http://${HOST}:${PORT}"
fi

if [[ "$PORT" != "8000" ]]; then
	echo "Nota: esta instancia NO afecta a la web pública del puerto 8000."
fi
if [[ -n "${SMARTDRIVE_BASE_MOUNT:-}" ]]; then
	echo "Usando base de datos local en: $SMARTDRIVE_BASE_MOUNT"
fi

if [[ ! -f "venv/bin/activate" ]]; then
	echo "Error: no se encontró venv/bin/activate. Crea el entorno virtual antes de arrancar."
	exit 1
fi

source venv/bin/activate

RELOAD_FLAG=""
DEFAULT_RELOAD="1"
if [[ "$PORT" == "8000" ]]; then
	DEFAULT_RELOAD="0"
fi

case "${SMARTDRIVE_RELOAD:-$DEFAULT_RELOAD}" in
	1|true|TRUE|yes|YES|on|ON) RELOAD_FLAG="--reload" ;;
esac

uvicorn main:app --host "$HOST" --port "$PORT" $RELOAD_FLAG
