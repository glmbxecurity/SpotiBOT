import os
import datetime
from datetime import timedelta
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import base64
from spotipy.exceptions import SpotifyException

# === Función para cargar playlists desde un archivo ===
def load_playlists(file_path="playlists.txt"):
    """Carga las playlists desde un archivo y extrae sus URLs y géneros."""
    file_path = os.path.join(os.path.dirname(__file__), file_path)  # Ruta basada en el script
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo '{file_path}' no existe.")
    
    playlists_by_genre = {}  # Diccionario para agrupar playlists por género
    
    with open(file_path, "r") as f:
        for line in f:
            parts = line.strip().split(" ")
            if len(parts) < 2:  # Ignorar líneas mal formateadas
                continue
            url, genre = parts[0], parts[1]
            if "playlist/" in url:
                playlist_id = url.split("playlist/")[1].split("?")[0]  # Extraer ID sin parámetros
                playlist_data = {"id": f"spotify:playlist:{playlist_id}", "url": url}
                
                if genre not in playlists_by_genre:
                    playlists_by_genre[genre] = []
                playlists_by_genre[genre].append(playlist_data)
    
    return playlists_by_genre

# === Función para establecer la imagen de la playlist ===
def set_playlist_image(sp, playlist_id, genre):
    """
    Establece una imagen para la playlist según el género. Si no encuentra
    una imagen para el género, usa una imagen predeterminada.
    """
    # Convertir el nombre del género a un nombre de archivo
    genre_image_name = f"{genre.lower().replace(' ', '_')}.jpg"
    genre_image_path = os.path.join("images", genre_image_name)  # Carpeta "images" para almacenar imágenes
    default_image_path = os.path.join("images", "spotibot.jpg")  # Imagen predeterminada

    # Verificar si la imagen específica del género existe
    if not os.path.exists(genre_image_path):
        print(f"No se encontró imagen '{genre_image_path}' para el género '{genre}', buscando imagen predeterminada.")
        if not os.path.exists(default_image_path):
            print(f"Error: No se encontró la imagen predeterminada '{default_image_path}'.")
            return  # Si no se encuentra la imagen predeterminada, salimos de la función
        else:
            print(f"Usando imagen predeterminada '{default_image_path}'.")
            genre_image_path = default_image_path  # Usamos la imagen predeterminada si no hay imagen para el género

    # Intentar abrir y cargar la imagen
    try:
        with open(genre_image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read())  # Sin decodificar a utf-8
            sp.playlist_upload_cover_image(playlist_id, encoded_image)  # Subir la imagen a la playlist
            print(f"Imagen establecida para la playlist del género '{genre}' con éxito.")
    except FileNotFoundError:
        print(f"Error: La imagen '{genre_image_path}' no fue encontrada.")
    except IOError as e:
        print(f"Error al abrir la imagen '{genre_image_path}': {e}")
    except SpotifyException as e:
        print(f"Error al subir la imagen para la playlist {playlist_id}: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

# === Leer la configuración desde el fichero config.txt ===
def load_config(file_path="config.txt"):
    """Carga las configuraciones desde un archivo."""
    file_path = os.path.join(os.path.dirname(__file__), file_path)  # Ruta absoluta basada en el directorio del script
    config = {}
    with open(file_path, "r") as f:
        for line in f:
            key, value = line.strip().split("=", 1)  # Divide en clave y valor
            config[key] = value
    return config

# === Funciones de Autenticación ===
import webbrowser

def authenticate_spotify():
    """Autenticación con la API de Spotify utilizando un flujo manual con refresh token."""
    config = load_config()  # Cargar configuraciones desde config.txt
    scope = "playlist-read-private playlist-modify-private ugc-image-upload"
    
    # Crear el objeto de autenticación de Spotify
    sp_oauth = SpotifyOAuth(
        client_id=config["SPOTIPY_CLIENT_ID"],
        client_secret=config["SPOTIPY_CLIENT_SECRET"],
        redirect_uri=config["SPOTIPY_REDIRECT_URI"],  # Debe ser http://localhost:8888/callback
        scope=scope,
        cache_path="token_cache.json"  # Archivo para almacenar los tokens
    )

    # Intentar cargar el token desde el cache
    token_info = sp_oauth.get_cached_token()
    
    if not token_info:
        print("No se encontró token de acceso almacenado.")
        print("Por favor, ingresa el código de autorización manualmente.")

        # Generar el enlace de autorización y mostrarlo
        auth_url = sp_oauth.get_authorize_url()
        print(f"Abre el siguiente enlace en tu navegador y otorga los permisos: {auth_url}")

        # Después de autorizar la aplicación, el usuario debe pegar el código aquí
        redirect_response = input("Pega la URL completa después de autorizar aquí: ")

        # Usamos la URL que el usuario ha pegado para obtener el código
        code = sp_oauth.parse_response_code(redirect_response)
        token_info = sp_oauth.get_access_token(code)

    # Usamos el token de acceso para autenticar el cliente
    sp = spotipy.Spotify(auth=token_info['access_token'])

    print("Autenticación exitosa.")
    return sp

# === Funciones de Manejo de Canciones ===
def get_playlist_tracks(sp, playlist_id):
    """Obtiene todas las canciones de una lista de reproducción."""
    tracks = []
    try:
        results = sp.playlist_items(playlist_id)
        while results:
            tracks.extend(results['items'])
            results = sp.next(results) if results['next'] else None
    except spotipy.exceptions.SpotifyException as e:
        print(f"Error al obtener canciones de la playlist {playlist_id}: {e}")
    return tracks

def filter_new_tracks(old_tracks, current_tracks):
    """Filtra canciones nuevas que no estén en el histórico."""
    old_ids = set(old_tracks)  # IDs previos como conjunto
    new_tracks = [track for track in current_tracks if track['track'] and track['track']['id'] not in old_ids]
    return new_tracks

def filter_recent_tracks(new_tracks, days):
    """Filtra canciones añadidas a la lista en los últimos X días."""
    recent_tracks = []
    now = datetime.datetime.now(datetime.timezone.utc)  # Hora actual en UTC
    cutoff_date = now - timedelta(days=days)  # Fecha de corte para los últimos X días

    for track in new_tracks:
        # Validar existencia de 'added_at'
        if 'added_at' not in track:
            print(f"Advertencia: El track {track['track']['name']} no tiene fecha de adición.")
            continue
        
        try:
            # Parsear la fecha 'added_at'
            added_at = datetime.datetime.strptime(track['added_at'], '%Y-%m-%dT%H:%M:%SZ')
            added_at = added_at.replace(tzinfo=datetime.timezone.utc)  # Convertir a UTC si no lo está
        except ValueError as e:
            print(f"Error al parsear fecha {track['added_at']}: {e}")
            continue

        # Comparar fechas
        if added_at >= cutoff_date:
            recent_tracks.append(track)

    print(f"{len(recent_tracks)} canciones recientes encontradas (últimos {days} días).")
    return recent_tracks


def filter_duplicate_tracks(new_tracks, global_track_ids):
    """Filtra canciones que ya están en el registro global."""
    return [track for track in new_tracks if track['track'] and track['track']['id'] not in global_track_ids]

def get_weekly_playlist_tracks(sp, playlist_id):
    """Obtiene los IDs de canciones ya presentes en la lista semanal."""
    tracks = get_playlist_tracks(sp, playlist_id)
    return {track['track']['id'] for track in tracks if track['track']}  # Conjunto de IDs

# === Funciones de Persistencia ===
def load_old_tracks(file_path):
    """Carga el histórico de canciones procesadas de un archivo."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return [line.strip() for line in f]
    return []

def save_new_tracks(file_path, tracks):
    """Guarda los IDs de las canciones nuevas en el histórico."""
    dir_path = os.path.dirname(file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(file_path, "a") as f:
        for track in tracks:
            f.write(f"{track['track']['id']}\n")

def load_global_tracks(file_path="global_tracks.txt"):
    """Carga el registro global de canciones procesadas."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return set(line.strip() for line in f)  # Conjunto para evitar duplicados
    return set()

def save_global_tracks(tracks, file_path="global_tracks.txt"):
    """Guarda canciones nuevas en el registro global."""
    with open(file_path, "a") as f:
        for track_id in tracks:
            f.write(f"{track_id}\n")

# === Funciones de Gestión de Listas ===
def get_or_create_genre_playlist(sp, user_id, genre):
    """Crea o recupera la lista para un género específico."""
    today = datetime.date.today()
    year = today.year  # Usamos el año en lugar del mes

    # Formato de nombre de la lista (sin espacio inicial)
    playlist_name = f"{genre.upper()} {year}"

    # Buscar si ya existe la lista para el género
    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        if playlist and 'name' in playlist and playlist['name'] == playlist_name:
            return playlist['id'], playlist_name

    # Si no existe, crearla
    new_playlist = sp.user_playlist_create(user_id, playlist_name, public=False)
    
    # Establecer la descripción de la lista
    description = f"Lista generada con SpotiBOT para {genre.upper()}"
    sp.playlist_change_details(new_playlist['id'], description=description)

    return new_playlist['id'], playlist_name

# === Funcion seleccion rango de antiguedad para la actualizacion de listas ===
def seleccionar_rango_tiempo():
    """Mostrar una línea interactiva para seleccionar el rango de tiempo."""
    opcion = input("Se agregarán las novedades de los últimos 7 días (Introduce un número para modificar la cantidad de días): ").strip()

    if opcion == "":
        return 7
    else:
        try:
            dias_personalizados = int(opcion)
            if dias_personalizados <= 0:
                print("Por favor, introduce un número positivo. Se usará 7 días por defecto.")
                return 7
            return dias_personalizados
        except ValueError:
            print("Entrada inválida, se usarán 7 días por defecto.")
            return 7

# === Función principal ===
def main():
    sp = authenticate_spotify()

    # Obtener usuario y playlists cargadas
    user = sp.current_user()
    user_id = user['id']

    playlists_by_genre = load_playlists()

    dias = seleccionar_rango_tiempo()

    for genre, playlists in playlists_by_genre.items():
        print(f"\nProcesando género: {genre}")

        # Obtener o crear la playlist semanal del género
        weekly_playlist_id, weekly_playlist_name = get_or_create_genre_playlist(sp, user_id, genre)

        # Obtener canciones ya en la playlist semanal para evitar duplicados
        weekly_track_ids = get_weekly_playlist_tracks(sp, weekly_playlist_id)

        # Cargar histórico global de canciones para evitar repeticiones
        global_tracks = load_global_tracks()

        for playlist in playlists:
            print(f"Procesando playlist: {playlist['url']}")

            # Obtener canciones actuales de la playlist origen
            current_tracks = get_playlist_tracks(sp, playlist['id'])

            # Cargar canciones históricas para esta playlist
            old_tracks = load_old_tracks(f"data/{genre}_old_tracks.txt")

            # Filtrar canciones nuevas no vistas antes en esta playlist
            new_tracks = filter_new_tracks(old_tracks, current_tracks)

            # Filtrar canciones recientes según rango de días
            recent_tracks = filter_recent_tracks(new_tracks, dias)

            # Filtrar canciones que no estén ya en la lista semanal
            unique_tracks = filter_duplicate_tracks(recent_tracks, weekly_track_ids.union(global_tracks))

            if unique_tracks:
                print(f"Agregando {len(unique_tracks)} canciones únicas a la lista semanal '{weekly_playlist_name}'...")
                track_uris = [track['track']['uri'] for track in unique_tracks if track['track']]
                try:
                    sp.playlist_add_items(weekly_playlist_id, track_uris)
                    save_new_tracks(f"data/{genre}_old_tracks.txt", unique_tracks)
                    save_global_tracks([track['track']['id'] for track in unique_tracks])
                except SpotifyException as e:
                    print(f"Error al agregar canciones a la playlist: {e}")
            else:
                print("No se encontraron canciones nuevas para agregar.")

        # Actualizar la imagen de la playlist semanal
        set_playlist_image(sp, weekly_playlist_id, genre)

    print("\nProceso finalizado.")

if __name__ == "__main__":
    main()
