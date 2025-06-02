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

# === Función para normalizar nombres de género ===
def normalize_genre_name(genre):
    """Reemplaza caracteres especiales para nombres de playlist más seguros."""
    return genre.replace("&", "AND").replace("_", " ").upper()

# === Función para obtener todas las playlists del usuario (paginación) ===
def get_all_user_playlists(sp):
    playlists = []
    results = sp.current_user_playlists()
    while results:
        playlists.extend(results['items'])
        results = sp.next(results) if results['next'] else None
    return playlists

# === Función para establecer la imagen de la playlist ===
def set_playlist_image(sp, playlist_id, genre):
    genre_image_name = f"{genre.lower().replace(' ', '_')}.jpg"
    genre_image_path = os.path.join("images", genre_image_name)  # Carpeta "images" para almacenar imágenes
    default_image_path = os.path.join("images", "spotibot.jpg")  # Imagen predeterminada

    if not os.path.exists(genre_image_path):
        print(f"No se encontró imagen '{genre_image_path}' para el género '{genre}', buscando imagen predeterminada.")
        if not os.path.exists(default_image_path):
            print(f"Error: No se encontró la imagen predeterminada '{default_image_path}'.")
            return
        else:
            print(f"Usando imagen predeterminada '{default_image_path}'.")
            genre_image_path = default_image_path

    try:
        with open(genre_image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read())
            sp.playlist_upload_cover_image(playlist_id, encoded_image)
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
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    config = {}
    with open(file_path, "r") as f:
        for line in f:
            key, value = line.strip().split("=", 1)
            config[key] = value
    return config

# === Funciones de Autenticación ===
def authenticate_spotify():
    config = load_config()
    scope = "playlist-read-private playlist-modify-private ugc-image-upload"
    
    sp_oauth = SpotifyOAuth(
        client_id=config["SPOTIPY_CLIENT_ID"],
        client_secret=config["SPOTIPY_CLIENT_SECRET"],
        redirect_uri=config["SPOTIPY_REDIRECT_URI"],
        scope=scope,
        cache_path="token_cache.json"
    )

    token_info = sp_oauth.get_cached_token()
    if not token_info:
        print("No se encontró token de acceso almacenado.")
        print("Por favor, ingresa el código de autorización manualmente.")

        auth_url = sp_oauth.get_authorize_url()
        print(f"Abre el siguiente enlace en tu navegador y otorga los permisos: {auth_url}")

        redirect_response = input("Pega la URL completa después de autorizar aquí: ")
        code = sp_oauth.parse_response_code(redirect_response)
        token_info = sp_oauth.get_access_token(code)

    sp = spotipy.Spotify(auth=token_info['access_token'])
    print("Autenticación exitosa.")
    return sp

# === Funciones de Manejo de Canciones ===
def get_playlist_tracks(sp, playlist_id):
    tracks = []
    try:
        results = sp.playlist_items(playlist_id, market='from_token')
        if not results['items']:
            print(f"La playlist {playlist_id} no tiene canciones o no se pudo acceder.")
        while results:
            tracks.extend(results['items'])
            results = sp.next(results) if results['next'] else None
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            print(f"Playlist {playlist_id} no encontrada o no accesible (error 404).")
        else:
            print(f"Error al obtener canciones de la playlist {playlist_id}: {e}")
    return tracks

def filter_new_tracks(old_tracks, current_tracks):
    old_ids = set(old_tracks)
    new_tracks = [track for track in current_tracks if track['track'] and track['track']['id'] not in old_ids]
    return new_tracks

def filter_recent_tracks(new_tracks, days):
    recent_tracks = []
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff_date = now - timedelta(days=days)

    for track in new_tracks:
        if 'added_at' not in track:
            print(f"Advertencia: El track {track['track']['name']} no tiene fecha de adición.")
            continue
        try:
            added_at = datetime.datetime.strptime(track['added_at'], '%Y-%m-%dT%H:%M:%SZ')
            added_at = added_at.replace(tzinfo=datetime.timezone.utc)
        except ValueError as e:
            print(f"Error al parsear fecha {track['added_at']}: {e}")
            continue
        if added_at >= cutoff_date:
            recent_tracks.append(track)

    print(f"{len(recent_tracks)} canciones recientes encontradas (últimos {days} días).")
    return recent_tracks

def filter_duplicate_tracks(new_tracks, global_track_ids):
    return [track for track in new_tracks if track['track'] and track['track']['id'] not in global_track_ids]

def get_weekly_playlist_tracks(sp, playlist_id):
    tracks = get_playlist_tracks(sp, playlist_id)
    return {track['track']['id'] for track in tracks if track['track']}

# === Funciones de Persistencia ===
def load_old_tracks(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return [line.strip() for line in f]
    return []

def save_new_tracks(file_path, tracks):
    dir_path = os.path.dirname(file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(file_path, "a") as f:
        for track in tracks:
            f.write(f"{track['track']['id']}\n")

def load_global_tracks(file_path="global_tracks.txt"):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return set(line.strip() for line in f)
    return set()

def save_global_tracks(tracks, file_path="global_tracks.txt"):
    with open(file_path, "a") as f:
        for track_id in tracks:
            f.write(f"{track_id}\n")

# === Funciones de Gestión de Listas ===
def get_or_create_genre_playlist(sp, user_id, genre):
    today = datetime.date.today()
    year = today.year

    playlist_name = f"{normalize_genre_name(genre)} {year}"
    print(f"Buscando o creando playlist con nombre: '{playlist_name}'")

    user_playlists = get_all_user_playlists(sp)
    for playlist in user_playlists:
        if playlist and 'name' in playlist and playlist['name'] == playlist_name:
            print(f"Playlist existente encontrada: '{playlist_name}' (ID: {playlist['id']})")
            return playlist['id'], playlist_name

    print(f"No se encontró playlist '{playlist_name}'. Creando una nueva...")
    new_playlist = sp.user_playlist_create(user_id, playlist_name, public=False)
    description = f"Lista generada con SpotiBOT para {normalize_genre_name(genre)}"
    sp.playlist_change_details(new_playlist['id'], description=description)
    return new_playlist['id'], playlist_name

# === Funcion seleccion rango de antiguedad para la actualizacion de listas ===
def seleccionar_rango_tiempo():
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
    user = sp.current_user()
    user_id = user['id']

    playlists_by_genre = load_playlists()
    dias = seleccionar_rango_tiempo()

    for genre, playlists in playlists_by_genre.items():
        print(f"\nProcesando género: {genre}")

        weekly_playlist_id, weekly_playlist_name = get_or_create_genre_playlist(sp, user_id, genre)
        weekly_track_ids = get_weekly_playlist_tracks(sp, weekly_playlist_id)
        global_tracks = load_global_tracks()

        for playlist in playlists:
            print(f"Procesando playlist: {playlist['url']}")
            current_tracks = get_playlist_tracks(sp, playlist['id'])
            old_tracks = load_old_tracks(f"data/{genre}_old_tracks.txt")
            new_tracks = filter_new_tracks(old_tracks, current_tracks)
            recent_tracks = filter_recent_tracks(new_tracks, dias)
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

        set_playlist_image(sp, weekly_playlist_id, genre)

    print("\nProceso finalizado.")

if __name__ == "__main__":
    main()
