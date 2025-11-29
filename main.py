import shutil
import os
from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from natsort import natsorted
from pydantic import BaseModel
from urllib.parse import quote
import asyncio

# 1. Creamos una instancia de FastAPI
app = FastAPI()
app.mount("/data", StaticFiles(directory="/mnt/midrive"), name="datos")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Configuramos la carpeta de plantillas
templates = Jinja2Templates(directory="templates")

# 3. Definimos una ruta que renderiza una plantilla HTML
@app.get("/")
def home(request: Request):
    
    # Obtenemos el uso del disco en la ruta /mnt/midrive
    gb_total, gb_free, porcentaje_uso = obtenerUsoDisco()

    #Mostramos los archivos en el directorio /mnt/midrive/inbox
    lista_archivos_inbox = archivosInbox()

    #Mostramos los archivos en el directorio /mnt/midrive/files
    carpeta_files = "/mnt/midrive/files"
    arbol_completo_files = obtener_arbol_directorios(carpeta_files)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "espacio_total": gb_total,
        "espacio_libre": gb_free,
        "porcentaje": porcentaje_uso,
        "archivos_inbox": lista_archivos_inbox,
        "arbol_archivos": arbol_completo_files["subcarpetas"]
    })

# --- FUNCIÓN DE SEGURIDAD PARA PREVENIR PATH TRAVERSAL ---
def sanitizar_ruta_entrada(user_input: str, base_dir: str):
    """
    Verifica que la entrada del usuario no intente salir de la ruta base.
    Lanza HTTPException si se detecta un ataque.
    """
    if not user_input:
        return ""

    # 1. Combina la ruta base con la entrada del usuario
    requested_path = os.path.join(base_dir, user_input)
    
    # 2. Resuelve la ruta real (limpia los ../ y enlaces simbólicos)
    safe_path = os.path.realpath(requested_path)
    
    # 3. VERIFICACIÓN CRÍTICA: La ruta final debe comenzar con la ruta base.
    # Esto asegura que el atacante no ha escapado de BASE_DIR.
    if not safe_path.startswith(base_dir):
        raise HTTPException(
            status_code=403, 
            detail="Forbidden: Path Traversal detectado y bloqueado."
        )
    
    # Devolvemos el segmento final limpio
    return safe_path

def obtenTamaño(size):
    for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unidad}"
        size /= 1024
    return f"{size:.2f} PB"

def obtenerUsoDisco():
    total, used, free = shutil.disk_usage("/mnt/midrive")
    gb_total = obtenTamaño(total)
    gb_free = obtenTamaño(free)
    porcentaje_uso = f"{(used / total) * 100:.1f}"
    return gb_total,gb_free,porcentaje_uso

def archivosInbox():
    carpeta_inbox = "/mnt/midrive/inbox"
    archivos_inbox = os.listdir(carpeta_inbox)
    archivos_inbox = natsorted(archivos_inbox)
    lista_archivos_inbox = []
    for archivo in archivos_inbox:
        ruta_completa = sanitizar_ruta_entrada(archivo, carpeta_inbox)
        if os.path.isfile(ruta_completa):
            tamano = os.path.getsize(ruta_completa)
            nombre_url = quote(archivo)
            info_archivo = {"nombre": archivo, "tamano": obtenTamaño(tamano), "url_encoded": nombre_url}
            lista_archivos_inbox.append(info_archivo)
    return lista_archivos_inbox

# --- FUNCIÓN AUXILIAR RECURSIVA ---
def obtener_arbol_directorios(ruta_base, ruta_relativa=""):
    """
    Recorre una carpeta y devuelve un diccionario con sus archivos 
    y una lista de sus subcarpetas (que a su vez son diccionarios).
    """
    estructura = {
        "nombre": os.path.basename(ruta_base),
        "ruta_relativa": ruta_relativa,
        "archivos": [],
        "subcarpetas": []
    }

    if os.path.exists(ruta_base):
        items = natsorted(os.listdir(ruta_base)) # Ordenamos con natsort
        # --- DEBUG NUEVO ---
        print(f"[DEBUG] Mirando en: {ruta_base} -> Encontrados: {items}")
        # -------------------
        for item in items:
            ruta_completa = os.path.join(ruta_base, item)
            nueva_ruta_relativa = os.path.join(ruta_relativa, item) if ruta_relativa else item

            if os.path.isdir(ruta_completa):
                subcarpeta = obtener_arbol_directorios(ruta_completa, nueva_ruta_relativa)
                estructura["subcarpetas"].append(subcarpeta)
            
            elif os.path.isfile(ruta_completa):
                size = os.path.getsize(ruta_completa)
                estructura["archivos"].append({
                    "nombre": item,
                    "tamano": obtenTamaño(size),
                    "url_descarga": f"{quote(nueva_ruta_relativa)}".replace("\\", "/") 
                })
    
    return estructura

# 4. Definimos una ruta para manejar la subida de archivos
# OJO: Cambiamos 'file: UploadFile' por 'files: List[UploadFile]'
# Asegúrate de eliminar la importación: from fastapi import Form
# Asegúrate de mantener la importación: from typing import List

@app.post("/upload")
async def upload_files(
    # Eliminamos el argumento 'sub_dir'
    files: List[UploadFile] = File(...),
):
    archivos_guardados = []
    base_inbox = "/mnt/midrive/inbox"
    
    # Aseguramos que el inbox exista
    if not os.path.exists(base_inbox):
        os.makedirs(base_inbox)

    for file in files:
        # El archivo aterriza directamente en la raíz del inbox
        ubicacion_archivo = os.path.join(base_inbox, file.filename)
        
        try:
            with open(ubicacion_archivo, "wb+") as file_object:
                shutil.copyfileobj(file.file, file_object)
            
            archivos_guardados.append(file.filename)
            
        except Exception as e:
            # Asegúrate de cerrar el archivo temporal si hay un error
            await file.close()
            # Devolvemos un 500 si hay error de escritura
            raise HTTPException(status_code=500, detail=f"Error al escribir {file.filename}: {str(e)}")
        finally:
            await file.close()
    
    return {"info": f"Subidos: {', '.join(archivos_guardados)}"}

@app.delete("/delete/{filename}")
async def delete_file(filename: str):
    # 1. Construimos la ruta
    ruta_archivo = f"/mnt/midrive/inbox/{filename}"
    
    # 2. Comprobamos si existe para evitar errores
    if os.path.exists(ruta_archivo):
        try:
            os.remove(ruta_archivo) # <--- Aquí ocurre la destrucción
            return {"info": f"Archivo {filename} eliminado"}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "El archivo no existe"}

# --- ENDPOINTS PARA LA VERSIÓN 2 (ORGANIZACIÓN) ---

# Esquema para cuando el JS nos pida crear una carpeta
class FolderSchema(BaseModel):
    folder_name: str

# Esquema para cuando el JS nos mande mover un archivo
class MoveSchema(BaseModel):
    filename: str
    destination_folder: str

@app.post("/create-folder")
async def create_folder(folder: FolderSchema):
    ruta_files = "/mnt/midrive/files"
    nueva_ruta = sanitizar_ruta_entrada(folder.folder_name, ruta_files)
    
    if not os.path.exists(nueva_ruta):
        try:
            os.makedirs(nueva_ruta)
            return {"info": f"Carpeta '{folder.folder_name}' creada"}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Esa carpeta ya existe"}

@app.get("/scan-folders/{filename}")
async def scan_folders(filename: str):
    ruta_files = "/mnt/midrive/files"
    ruta_origen = f"/mnt/midrive/inbox/{filename}" 
    
    # --- EL CAMBIO CRUCIAL: Usamos la función recursiva para obtener TODAS las carpetas ---
    carpetas_existentes = obtener_lista_plana_carpetas(ruta_files)
    
    # 2. LÓGICA DE SUGERENCIA (Heurística)
    # Aquí puedes usar tu CerebroDigital o las reglas simples como antes:
    sugerencia = "General" 
    ext = filename.split('.')[-1].lower()
    if ext in ['jpg', 'png', 'jpeg', 'gif']:
        sugerencia = "Imagenes"
    elif ext in ['pdf', 'doc', 'txt']:
        sugerencia = "Documentos"
        
    return {
        # Ahora esta lista incluye 'Docs/Facturas/2025'
        "folders": carpetas_existentes,
        "suggested": sugerencia
    }

def tarea_mover_bloqueante(origen, ruta_final):
    """Función de trabajo pesado que será ejecutada en un hilo separado."""
    shutil.move(origen, ruta_final)

@app.post("/move")
async def move_file(move_data: MoveSchema):

    origen = sanitizar_ruta_entrada(move_data.filename, "/mnt/midrive/inbox")
    # OJO: La ruta destino incluye la carpeta seleccionada Y el nombre del archivo
    
    carpeta_destino = sanitizar_ruta_entrada(move_data.destination_folder, "/mnt/midrive/files")
    ruta_final = os.path.join(carpeta_destino, move_data.filename)
    
    # Aseguramos que la carpeta destino exista (seguridad)
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    if not os.path.exists(origen):
        return {"error": "El archivo origen no existe"}
    await asyncio.to_thread(tarea_mover_bloqueante, origen, ruta_final)
    return {"info": f"Archivo movido a {move_data.destination_folder}"}

@app.delete("/delete-cataloged/{filepath:path}")
async def delete_cataloged_file(filepath: str):
    BASE_DIR = "/mnt/midrive/files"
    # Usamos la función de seguridad
    ruta_a_borrar = sanitizar_ruta_entrada(filepath, BASE_DIR)
    
    if os.path.isfile(ruta_a_borrar):
        try:
            os.remove(ruta_a_borrar)
            return {"info": f"Archivo eliminado de forma segura"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al borrar: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    
# --- FUNCIÓN AUXILIAR PARA LISTAR TODAS LAS CARPETAS (Necesario para el desplegable) ---
def obtener_lista_plana_carpetas(path_base):
    """Utiliza os.walk para listar todas las carpetas en el árbol de forma plana."""
    
    lista_plana = []
    lista_plana.append(".") 

    if os.path.exists(path_base):
        for root, dirs, files in os.walk(path_base):
            relative_root = os.path.relpath(root, path_base)
            
            for dir_name in dirs:
                # La ruta completa relativa que usaremos en el dropdown
                current_relative_path = os.path.join(relative_root, dir_name)
                # La añadimos solo si no es la raíz (que ya la añadimos como ".")
                if current_relative_path != ".":
                    lista_plana.append(current_relative_path.replace("\\", "/")) # Aseguramos barras /
    
    return natsorted(lista_plana) # Usamos natsort para que el dropdown se vea bien


# --- NUEVO ENDPOINT PARA EL JS ---
@app.get("/all-folders")
def get_all_folders():
    BASE_DIR = "/mnt/midrive/files"
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
        
    folders = obtener_lista_plana_carpetas(BASE_DIR)
    return {"folders": folders}