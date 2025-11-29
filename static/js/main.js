/**
 * Raspberry Pi Smart Drive - Main Client Script
 * Maneja la interacción del usuario, carga de carpetas y operaciones con archivos.
 */

document.addEventListener("DOMContentLoaded", function() {

    const folders = Array.from(document.querySelectorAll('.folder-node'));
    
    folders.reverse().forEach(folder => {
        let total = 0;
        
        const table = folder.querySelector(':scope > div > table'); 
        
        if (table) { 
            total += table.querySelectorAll('tr').length; 
        }
        
        const subfolders = folder.querySelectorAll(':scope > div > .folder-node');
        subfolders.forEach(sub => { total += parseInt(sub.getAttribute('data-total') || 0); });
        
        // Actualizar UI
        folder.setAttribute('data-total', total);
        const span = folder.querySelector(':scope > summary .file-count');
        if (span) span.innerText = `(${total})`;
    });
});

// Variables Globales
const form = document.getElementById('upload-form');
const dialog = document.getElementById('moveDialog');
let archivoActual = ""; 

/**
 * Función Unificada: Ordena y renderiza carpetas en un elemento <select>
 * Crea una estructura jerárquica visual con indentación.
 */
function formatAndRenderFolders(selectElement, folders, suggestedFolder = null) {
    selectElement.innerHTML = ""; 
    // Mapeo para ordenación
    const processedFolders = folders.map(path => {
        let cleanedPath = path.startsWith('./') ? path.substring(2) : path;
        return {
            original: path,
            display: cleanedPath,
            sortKey: cleanedPath === '.' ? ' ' : cleanedPath // Asegura que la raíz '.' vaya primero
        };
    });
    // Ordenación alfabética sobre la ruta limpia
    processedFolders.sort((a, b) => a.sortKey.localeCompare(b.sortKey));

    // Renderizado con indentación
    processedFolders.forEach(folder => {
        const option = document.createElement('option');
        option.value = folder.original;
        let displayText = folder.display;
        
        if (folder.original === ".") {
            displayText = "Raíz (/files/)"; 
        } else {
            const parts = displayText.split('/');
            const level = parts.length - 1; 
            const indent = '— '.repeat(level); // Indentación visual
            displayText = indent + parts.pop(); // Muestra solo el último nombre
        }
        
        if (suggestedFolder && folder.original === suggestedFolder) {
            displayText += " (⭐ Sugerido)";
        }
        option.text = displayText;
        selectElement.add(option);
    });
}

// Carga inicial de carpetas para "Crear Nueva Carpeta"
async function fetchAndRenderFolders() {
    const select = document.getElementById('parentFolderSelect');
    try {
        const res = await fetch('/all-folders');
        const data = await res.json();
        formatAndRenderFolders(select, data.folders);
    } catch (error) { select.innerHTML = "<option value='.'>Error al cargar.</option>"; }
}
window.addEventListener('load', fetchAndRenderFolders);

// Operaciones con Carpetas
async function crearCarpetaGlobal() {
    const parentPath = document.getElementById('parentFolderSelect').value;
    const newFolderName = document.getElementById('newFolderName').value;
    if (!newFolderName) return alert("Nombre vacío.");
    const fullPath = parentPath === "." ? newFolderName : `${parentPath}/${newFolderName}`; 
    
    const res = await fetch('/create-folder', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({folder_name: fullPath})
    });
    if (res.ok) { location.reload(); } else { alert("Error al crear."); }
}

async function crearCarpeta() {
    const nombre = document.getElementById('newFolderInput').value;
    if (!nombre) return;
    const res = await fetch('/create-folder', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({folder_name: nombre})
    });
    if (res.ok) { 
        alert("Carpeta creada"); 
        document.getElementById('newFolderInput').value = ""; 
        moverArchivo(archivoActual); // Recarga el diálogo
    }
}

// Manejo de Subida de Archivos (con barra de progreso)
form.addEventListener('submit', function(event) {
    event.preventDefault();
    
    // Crear contenedor de progreso si no existe
    let progressBox = document.getElementById('upload-progress-box');
    if(!progressBox) {
        progressBox = document.createElement('div');
        progressBox.id = 'upload-progress-box';
        progressBox.className = 'section-box';
        progressBox.style.marginTop = '15px';
        // Usamos los estilos de la barra de estado principal
        progressBox.innerHTML = `
            <div class="flex-row" style="margin-bottom: 5px;"><small id="statusText" style="color: var(--text-muted);">Iniciando subida...</small></div>
            <div style="background: #333; border-radius: 4px; overflow: hidden; height: 10px;">
                <div id="progressBar" class="progress-bar" style="width: 0%;"></div>
            </div>`;
        form.appendChild(progressBox);
    }
    
    form.querySelector('button').disabled = true; 
    const formData = new FormData(form); 
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener("progress", function(e) {
        if (e.lengthComputable) { 
            const percent = (e.loaded / e.total) * 100; 
            document.getElementById('progressBar').style.width = percent + "%"; 
            document.getElementById('statusText').innerText = "Subiendo: " + Math.round(percent) + "%"; 
        }
    });
    xhr.addEventListener("load", function() {
        if (xhr.status === 200) { location.reload(); } else { alert("Error: " + xhr.status); form.querySelector('button').disabled = false; }
    });
    xhr.addEventListener("error", function() { alert("Error de red"); form.querySelector('button').disabled = false; });
    xhr.open("POST", "/upload"); xhr.send(formData);
});

// Operaciones con Archivos (Mover y Borrar)
async function moverArchivo(nombre) {
    archivoActual = nombre; 
    document.getElementById('modalFilename').innerText = nombre;
    const res = await fetch('/scan-folders/' + encodeURIComponent(nombre)); 
    const data = await res.json();
    const select = document.getElementById('folderSelect'); 
    
    if (data.folders.length === 0) { 
        select.innerHTML = ""; select.add(new Option("-- No hay carpetas --")); 
    } else {
        formatAndRenderFolders(select, data.folders, data.suggested);
    }
    dialog.showModal(); 
}

async function confirmarMover() {
    const destino = document.getElementById('folderSelect').value;
    if (!destino || destino.includes("--")) return alert("Destino inválido");
    const res = await fetch('/move', { 
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ filename: archivoActual, destination_folder: destino }) 
    });
    if (res.ok) { dialog.close(); location.reload(); } else { alert("Error al mover"); }
}

async function borrarArchivo(nombre) { if (confirm("¿Eliminar " + nombre + "?")) { (await fetch('/delete/' + encodeURIComponent(nombre), { method: 'DELETE' })).ok ? location.reload() : alert("Error"); } }
async function borrarCatalogado(ruta) { if (confirm("¿Eliminar del catálogo?")) { (await fetch('/delete-cataloged/' + ruta, { method: 'DELETE' })).ok ? location.reload() : alert("Error"); } }