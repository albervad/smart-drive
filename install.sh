#!/bin/bash

# Colores para los mensajes
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}>>> Iniciando instalación de Raspberry Pi Smart Drive...${NC}"

# 1. Actualizar sistema e instalar dependencias de sistema
echo -e "${GREEN}>>> Actualizando sistema e instalando Python3-venv...${NC}"
sudo apt update
sudo apt install -y python3-pip python3-venv

# 2. Crear estructura de carpetas de datos
echo -e "${GREEN}>>> Creando directorios en /mnt/midrive...${NC}"
# Creamos la carpeta base por si no existe
sudo mkdir -p /mnt/midrive/inbox
sudo mkdir -p /mnt/midrive/files

# 3. Asignar permisos (CRÍTICO para evitar errores 500)
echo -e "${GREEN}>>> Ajustando permisos (777) para evitar errores de escritura...${NC}"
sudo chmod -R 777 /mnt/midrive

# 4. Configurar Entorno Virtual Python
echo -e "${GREEN}>>> Configurando entorno virtual (venv)...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Venv creado."
else
    echo "Venv ya existía."
fi

# 5. Instalar librerías
echo -e "${GREEN}>>> Instalando dependencias desde requirements.txt...${NC}"
source venv/bin/activate
pip install -r requirements.txt

echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}   ¡INSTALACIÓN COMPLETADA CON ÉXITO!  ${NC}"
echo -e "${GREEN}=======================================${NC}"
echo "Para iniciar el servidor, ejecuta: ./start.sh"
echo "NOTA: Asegúrate de que tu USB esté montado en /mnt/midrive si vas a usar uno externo."
