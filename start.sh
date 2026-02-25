#!/bin/bash
echo "Iniciando Smart Drive..."
source venv/bin/activate
# Escucha en 0.0.0.0 para que sea accesible desde otros PCs de la red
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
