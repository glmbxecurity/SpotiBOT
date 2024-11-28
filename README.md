# SpotiBOT by GlmbXecurity

SpotiBOT es un bot para Spotify que facilita la gestión automática de playlists, agregando nuevas canciones de manera eficiente y organizada. Está diseñado para recolectar canciones nuevas de varias playlists y agregarlas a una playlist mensual creada específicamente para ello. Utiliza la API de Spotify para interactuar con las playlists y las canciones.

## Características

- **Autenticación con Spotify**: Se conecta a tu cuenta de Spotify de manera segura utilizando el flujo de autorización estándar.
- **Cargar Playlists**: Permite cargar las playlists desde un archivo `playlists.txt` para obtener las canciones de ellas.
- **Filtrado de Canciones Nuevas**: Filtra las canciones nuevas y las canciones duplicadas.
- **Playlist Mensual Automática**: Crea y/o actualiza una playlist mensual con las canciones nuevas del mes, asignando un nombre basado en el mes y el año.
- **Soporte para múltiples playlists**: Puedes cargar varias playlists y agregar canciones a la playlist mensual.
- **Historial de Canciones**: Mantiene un historial de las canciones ya procesadas para evitar duplicados.

 ## Screenshots del programa
 #### EJECUCIÓN DEL PROGRAMA
![image](https://raw.githubusercontent.com/glmbxecurity/SpotiBOT/refs/heads/main/screenshots/ejecucion.jpeg)
 #### RESULTADO FINAL
![image](https://raw.githubusercontent.com/glmbxecurity/SpotiBOT/refs/heads/main/screenshots/spotify.jpeg)
## Instalación

Para usar SpotiBOT, primero necesitas tener Python 3.x (Probado en Python 3.13.0)
Luego debes instalar spotipy y python-dotenv
```bash
pip install spotipy
pip install python-dotenv
```

### 1. Clonar el repositorio
Clona el repositorio de GitHub en tu máquina local:

```bash
git clone https://github.com/tu_usuario/SpotiBOT.git
```

### 2. Configuracion
Antes de ejecutar el programa, necesitas configurar las credenciales de la API de Spotify. Para ello, crea un archivo config.txt en el directorio raíz del proyecto con la siguiente estructura:

```bash 
SPOTIPY_CLIENT_ID=tu_client_id
SPOTIPY_CLIENT_SECRET=tu_client_secret
SPOTIPY_REDIRECT_URI=tu_redirect_uri
```

Estos valores los puedes obtener creando una aplicación en Spotify Developer Dashboard.
![image](https://raw.githubusercontent.com/glmbxecurity/SpotiBOT/refs/heads/main/screenshots/config.jpeg)
 ### 3. Crear el archivo playlists.txt
Crea un archivo playlists.txt en el directorio raíz del proyecto. Este archivo debe contener las URL de las playlists de las que deseas obtener las canciones, una por línea. Por ejemplo:

```bash
https://open.spotify.com/playlist/playlist_id_1
https://open.spotify.com/playlist/playlist_id_2
```
![image](https://raw.githubusercontent.com/glmbxecurity/SpotiBOT/refs/heads/main/screenshots/playlists.jpeg)
 ### 4. Uso
Una vez que hayas configurado todo, puedes ejecutar el script para que SpotiBOT recoja las canciones nuevas de las playlists y las agregue a la playlist mensual.

Ejecuta el script desde la terminal:

```bash
python SpotiBOT.py
```

 ### TROUBLESHOOTING
Para ejecutar la opción de "Los últimos 30 días", previamente has de haber sincronizado al menos los ultimos 7 o 15 días, sino Spotify detecta muchas requests de una vez y rechaza la petición.
 Si eliminas canciones por error y no querías, o eliminas la playlist, la manera de corregir y volver a empezar es eliminando la carpeta data (se genera al lanzar el programa), y eliminar el fichero global_traacks.txt



