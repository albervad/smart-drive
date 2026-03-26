#!/bin/bash

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_REF="${1:-main}"
DEFAULT_PROD_DIR="$HOME/mydrive-prod-main"
PROD_DIR="${SMARTDRIVE_PROD_DIR:-$DEFAULT_PROD_DIR}"
SERVICE_NAME="${SMARTDRIVE_SERVICE_NAME:-smartdrive}"

if ! git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: $REPO_DIR no es un repositorio git."
  exit 1
fi

TARGET_COMMIT="$(git -C "$REPO_DIR" rev-parse "$TARGET_REF")"

if [[ ! -e "$PROD_DIR/.git" ]]; then
  git -C "$REPO_DIR" worktree add --detach "$PROD_DIR" "$TARGET_COMMIT"
fi

git -C "$PROD_DIR" checkout --detach "$TARGET_COMMIT"

if [[ ! -d "$PROD_DIR/venv" ]]; then
  python3 -m venv "$PROD_DIR/venv"
fi

source "$PROD_DIR/venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$PROD_DIR/requirements.txt"

if ! command -v systemctl >/dev/null 2>&1; then
  echo "Error: systemctl no está disponible en este sistema."
  exit 1
fi

if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}\.service"; then
  echo "Error: no existe ${SERVICE_NAME}.service en systemd."
  exit 1
fi

sudo systemctl restart "$SERVICE_NAME"

echo "OK: $SERVICE_NAME publicado en 8000 desde $PROD_DIR"
echo "Commit activo: $(git -C "$PROD_DIR" rev-parse --short HEAD)"