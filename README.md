# Smart Drive

Proyecto de web personal con frontend web y backend FastAPI, diseñado con enfoque en **seguridad defensiva aplicada**: validación de rutas, control de superficie de búsqueda de contenido y despliegue seguro sin exponer puertos.

<img width="1874" height="921" alt="image" src="https://github.com/user-attachments/assets/2c68bc8e-df0c-4c71-ac89-945f049241aa" />
<img width="1856" height="922" alt="image" src="https://github.com/user-attachments/assets/6441ce17-93fd-42b0-8043-ed325f7f3305" />
<img width="1872" height="917" alt="image" src="https://github.com/user-attachments/assets/d50e3108-e7ce-481e-b111-279776226d9d" />
<img width="1871" height="921" alt="image" src="https://github.com/user-attachments/assets/a4d22c7e-e6f8-4d94-8707-5f5278a589a0" />
<img width="1866" height="915" alt="image" src="https://github.com/user-attachments/assets/ce3f7b16-e11e-4dd2-a3ae-4f7bb2785209" />



## 🎯 Objetivo del proyecto

Construir un servicio de archivos autohospedado que sea útil en casa/lab y, al mismo tiempo, sirva como pieza de portfolio orientada a ciberseguridad:

- Diseño de controles básicos de hardening en backend.
- Reducción de riesgos típicos (Path Traversal, lectura fuera de base, abuso de búsqueda).
- Exposición remota con acceso seguro (Zero Trust / red privada).

## 🧩 Funcionalidades principales

- Portfolio público en `/` (alias legacy: `/portfolio`).
- Dashboard en `/dashboard` como punto de entrada de navegación.
- Drive operativo bajo `/drive`.
- Selector de entorno en dashboard (local por defecto: `192.168.1.47`; remoto: `199.68.161.18`) con accesos directos a Jellyseerr, Jellyfin, Radarr, Sonarr, Jackett y qBittorrent.
- Sección de estado del sistema en dashboard con métricas en vivo: temperatura, consumo energético (si el hardware lo expone), CPU, RAM, disco, carga media y uptime.
- Tarifa eléctrica configurable desde `static/data/energy_rates.json` para estimar coste por hora en el dashboard.
- Coste eléctrico estimado por hora/día/mes y uso de GPU (dedicada/integrada) con soporte para cualquier número de gráficas detectadas.
- Navegación guiada: Portfolio -> Dashboard -> Drive y acceso de vuelta a Dashboard desde Drive.
- Subida de archivos por chunks con reintentos y cierre controlado.
- Inbox + catálogo en árbol de carpetas.
- Operaciones de archivo/carpeta: mover, renombrar, borrar, descargar y abrir.
- Búsqueda por nombre y contenido con selector de modo.
- Descarga de carpetas en ZIP.

## 🔐 Controles de seguridad implementados

### 1) Validación estricta de rutas

- Se normalizan rutas con `realpath` y se verifica que permanezcan dentro de las bases permitidas (`/mnt/midrive/inbox` y `/mnt/midrive/files`).
- Se evita acceso fuera de la “jaula” (mitigación de Path Traversal / LFI).

### 2) Defensa adicional en búsqueda de contenido

- Se ignoran symlinks durante el recorrido de archivos.
- Se verifica que cada `realpath` siga dentro del directorio base antes de procesarlo.

### 3) Reducción de superficie de parsing

- La búsqueda de contenido se limita a formatos legibles permitidos (texto y documentos extraíbles), excluyendo imágenes/vídeos.
- Se aplican límites de tamaño por archivo y número máximo de resultados para evitar abuso de recursos.

### 4) Validación de parámetros de entrada

- Longitud máxima de consulta en búsqueda.
- Validación del modo de búsqueda (`both`, `name`, `content`).
- Respuestas con códigos HTTP adecuados ante parámetros inválidos.

### 5) Operación de servicio controlada

- Ejecución en `systemd` con reinicio automático.
- Limpieza programada de archivos temporales `.part` por `cron`.

### 6) Segmentación de superficie expuesta

- Zona funcional del Drive concentrada en `/drive`.
- Endpoints de documentación FastAPI deshabilitados: `/docs`, `/redoc`, `/openapi.json`.
- Assets estáticos de frontend en `/static`.

## ⚠️ Riesgos conocidos / límites actuales

- No incluye autenticación/autorización nativa en la app web.
- No hay registro de auditoría completo de acciones (quién hizo qué y cuándo).
- No hay antimalware ni DLP en subidas.
- Riesgo de **ZIP bomb / compresión abusiva**: no existe una defensa específica para detectar archivos comprimidos maliciosos (incluyendo documentos empaquetados como `.docx/.odt` durante extracción de contenido o cargas diseñadas para agotar CPU/RAM/disco).

Esto se mitiga recomendando despliegue detrás de una capa segura de acceso.

## 🌐 Exposición segura (recomendado)

### Cloudflare WAF (producción actual)

La política WAF está configurada para bloquear rutas no permitidas y solo dejar pasar rutas conocidas:

- `/`
- `/portfolio`
- `/dashboard`
- `/static/`
- `/drive`
- `/favicon.ico`
- `/cdn-cgi/` (login/challenge de Cloudflare)

Recomendación: mantener esta allowlist y revisar cada cambio de rutas antes de publicar nuevas versiones.

### Opción A: Cloudflare Zero Trust (Tunnel)

- Publicación sin abrir puertos en router.
- Control de acceso, políticas y capa Zero Trust.

### Opción B: Tailscale

- Acceso por red privada mesh (WireGuard).
- Menor superficie pública, ideal para uso personal/lab.

> Recomendación: no exponer directamente `:8000` a Internet.

## 🛠️ Requisitos

- Linux con `sudo` y `systemd`.
- Python 3 y `git`.
- Disco/pendrive montado en `/mnt/midrive`.

La metrica de uso de GPU Intel en el dashboard se obtiene con `intel_gpu_top` (paquete `intel-gpu-tools` o `igt-gpu-tools` segun distro).

## 🧪 Sistemas operativos compatibles

El instalador está preparado para ejecutarse en Linux con distintos gestores de paquetes y detecta la plataforma automáticamente:

- Raspberry Pi OS / Debian / Ubuntu Server (`apt`).
- Fedora / RHEL derivados (`dnf` o `yum`).
- Arch Linux (`pacman`).
- openSUSE (`zypper`).
- Alpine Linux (`apk`).

Notas de compatibilidad:

- Requiere `systemd` para registrar `smartdrive.service`.
- Requiere servicio de cron (`cron` o `crond`) para la limpieza automática de temporales.

## 🚀 Instalación rápida

1. Clonar:

   ```bash
   git clone https://github.com/albervad/raspberry-smart-drive.git
   cd raspberry-smart-drive
   ```

2. Dar permisos:

   ```bash
   chmod +x install.sh start.sh
   ```

3. Instalar:

   ```bash
   sudo ./install.sh
   ```

El instalador configura dependencias, entorno virtual, carpetas de datos, servicio `smartdrive` y limpieza diaria de temporales.

En hosts con GPU Intel detectada, el instalador intenta instalar `intel-gpu-tools` para habilitar la metrica de GPU en dashboard.

> Nota: el instalador usa `requirements.txt` para instalar dependencias Python.

## ▶️ Ejecución

### Producción

```bash
sudo systemctl start smartdrive
sudo systemctl status smartdrive
```

Instancia pública inmutable (`8000`):

- El servicio público corre desde un directorio aislado (`/home/alberto/mydrive-prod-main`), no desde el directorio de trabajo.
- Cambiar de rama o editar archivos en `/home/alberto/mydrive` no modifica la web pública.
- La web pública solo se actualiza cuando publicas explícitamente `main`.

Publicar `main` en la web pública:

```bash
./deploy_main_to_public.sh
```

Opcionalmente, puedes publicar otra referencia:

```bash
./deploy_main_to_public.sh main
```

### Desarrollo

```bash
./start.sh 8001
```

Parámetros opcionales:

```bash
./start.sh [PORT] [HOST] [BASE_MOUNT]
```

- `PORT`: por defecto `8001` (evita chocar con producción en `8000`).
- `HOST`: por defecto `0.0.0.0` (accesible desde la red local).
- `BASE_MOUNT`: ruta de datos para esta instancia (si se indica, se crea `inbox/` y `files/`).

Regla de seguridad en `start.sh`:

- El puerto `8000` queda reservado para la rama `main`.
- Si se intenta arrancar en `8000` desde otra rama, el script falla con error.
- En `8000`, `--reload` queda desactivado por defecto (se puede forzar con `SMARTDRIVE_RELOAD=1` si es necesario).

### Debug logs (desarrollo)

Para activar trazas de depuración y logs HTTP de cada request:

```bash
SMARTDRIVE_DEBUG=1 SMARTDRIVE_REQUEST_LOGGING=1 ./start.sh 8001
```

Para forzar solo localhost:

```bash
SMARTDRIVE_DEBUG=1 SMARTDRIVE_REQUEST_LOGGING=1 ./start.sh 8001 127.0.0.1
```

Para depurar sin tocar datos de la instancia pública:

```bash
SMARTDRIVE_DEBUG=1 SMARTDRIVE_REQUEST_LOGGING=1 SMARTDRIVE_BASE_MOUNT=/tmp/smartdrive-dev ./start.sh 8001
```

Variables útiles:

- `SMARTDRIVE_DEBUG`: activa modo debug (por defecto `0`).
- `SMARTDRIVE_REQUEST_LOGGING`: activa middleware de trazas HTTP (por defecto hereda `SMARTDRIVE_DEBUG`).
- `SMARTDRIVE_LOG_LEVEL`: fuerza nivel de log (`DEBUG`, `INFO`, `WARNING`, etc.).
- `SMARTDRIVE_BASE_MOUNT`: sobreescribe la base de datos (`/mnt/midrive`) para usar otra ruta en local.
- `SMARTDRIVE_PORT` / `SMARTDRIVE_HOST`: valores por defecto para `start.sh` si no se pasan parámetros.
- `SMARTDRIVE_OWNER_IPS`: IPs consideradas "admin" para acceder al panel de control (CSV, por defecto `127.0.0.1,::1`).
- `SMARTDRIVE_TRUST_PROXY_HEADERS`: habilita confianza en `X-Forwarded-For`/`X-Real-IP` (`0` por defecto). Activar solo detrás de proxy inverso.
- `SMARTDRIVE_TRUSTED_PROXY_IPS`: IPs de proxies de confianza autorizados a reenviar IP cliente (CSV, por defecto `127.0.0.1,::1`).
- `SMARTDRIVE_AUDIT_DIR`: directorio donde se guardan registros de accesos/acciones (por defecto `./.smartdrive_audit`, más rápido que usar discos externos).
- `SMARTDRIVE_AUDIT_MAX_EVENTS`: máximo de eventos de auditoría persistidos.
- `SMARTDRIVE_AUDIT_RECENT_LIMIT`: cuántos eventos recientes mostrar en el panel.
- `SMARTDRIVE_NEW_VISITOR_WINDOW_HOURS`: ventana para marcar usuarios como "nuevos".

Acceso local:

- `http://127.0.0.1:8001` (o el host/puerto que indiques)

## 🗂️ Estructura de datos

- `/mnt/midrive/inbox`: archivos recién subidos.
- `/mnt/midrive/files`: archivos catalogados.

En desarrollo puedes aislar datos con `SMARTDRIVE_BASE_MOUNT` (por ejemplo `/tmp/smartdrive-dev`).

## 🛂 Panel de control de accesos

- URL: `/control`.
- Muestra usuarios detectados de forma pasiva (cookie técnica + IP + user-agent + idioma, sin permisos del navegador).
- Permite bloquear/desbloquear usuarios y marcar/quitar "admin" para excluir visitas de administración del portfolio.
- Registra acciones clave: subir archivos (finalización), borrar, mover, renombrar, guardar portapapeles, descargar ZIP y vistas del portfolio.
- Permite borrar registros globales o por usuario una vez revisados.
- Estadísticas de portfolio excluyen automáticamente a usuarios marcados como admin.
- Endpoints mutables (`POST`/`PUT`/`PATCH`/`DELETE`) aplican protección CSRF (token y validación same-origin).

## 🛣️ Roadmap de seguridad (portfolio)

- Autenticación fuerte (OIDC/SSO o MFA) y roles mínimos.
- Logging de auditoría estructurado y centralizado.
- Rate limiting por endpoint sensible.
- Escaneo de ficheros subidos (AV) y política de cuarentena.
- Hardening HTTP (cabeceras, CORS estricto, CSP en frontend).

## 🤝 Contribuciones

Pull Requests bienvenidos.
