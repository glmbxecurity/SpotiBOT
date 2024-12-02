
import os
import datetime
from datetime import timedelta
import spotipy
from spotipy.oauth2 import SpotifyOAuth


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
def authenticate_spotify():
    """Autenticación con la API de Spotify."""
    config = load_config()  # Cargar configuraciones desde config.txt
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=config["SPOTIPY_CLIENT_ID"],
        client_secret=config["SPOTIPY_CLIENT_SECRET"],
        redirect_uri=config["SPOTIPY_REDIRECT_URI"],
        scope="playlist-read-private playlist-modify-private"
    ))
    return sp

# === Función para cargar playlists desde un archivo ===
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
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
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
# === Función para obtener o crear playlist por género ===
def get_or_create_genre_playlist(sp, user_id, genre):
    """Crea o recupera la lista para un género específico."""
    today = datetime.date.today()
    month_number = today.month  # Usamos el mes en lugar de la semana
    year = today.year
    
    # Lista de nombres de meses en español
    months_in_spanish = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    # Formato de nombre de la lista
    playlist_name = f"New {genre.upper()} {months_in_spanish[month_number - 1]} {year}"

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


# === Funcion selecion rango de antiguedad para la actualizacion de listas ===
def seleccionar_rango_tiempo():
    """Mostrar una línea interactiva para seleccionar el rango de tiempo."""
    # Mensaje de solicitud en una sola línea
    opcion = input("Se agregarán las novedades de los últimos 7 días (Introduce un número para modificar la cantidad de días): ")

    # Si el usuario no introduce nada, se usan 7 días como valor por defecto
    if opcion == "":
        return 7
    else:
        try:
            # Intenta convertir la entrada del usuario a un número entero
            dias_personalizados = int(opcion)
            if dias_personalizados <= 0:
                print("Por favor, introduce un número positivo. Usando 7 días por defecto.")
                return 7  # Si el número no es válido o es negativo, usamos 7 días
            return dias_personalizados
        except ValueError:
            # Si la entrada no es un número válido, muestra un mensaje de error y usa 7 días
            print("Entrada no válida. Usando 7 días por defecto.")
            return 7



# === Función Principal ===
def main():
    sp = authenticate_spotify()
    user_id = sp.current_user()["id"]
    user_name = sp.current_user()["display_name"]  # Nombre del usuario

    # === Bienvenida ===
    print("SpotiBOT by GlmbXecurity")
    print(f"Bienvenid@ {user_name}")
    print("\nCargando playlists...\n")

    # === Cargar playlists desde el archivo ===
    try:
        playlists_by_genre = load_playlists("playlists.txt")  # Lee las playlists por género
        if not playlists_by_genre:  # Si no hay playlists
            print("El archivo 'playlists.txt' no contiene playlists válidas.")
            exit(1)  # Terminar el programa si no hay playlists
    except FileNotFoundError:
        print("El archivo 'playlists.txt' no se encontró. Por favor, créalo y agrega URLs de playlists.")
        exit(1)
    except Exception as e:
        print(f"Ocurrió un error al cargar las playlists: {e}")
        exit(1)

    # Seleccionar el rango de tiempo
    dias_recientes = seleccionar_rango_tiempo()

    # Cargar el registro global
    global_tracks_path = "global_tracks.txt"
    global_track_ids = load_global_tracks(global_tracks_path)

    # Procesar las playlists por género
    for genre, playlists in playlists_by_genre.items():
        # Obtener o crear la lista para ese género
        genre_playlist_id, genre_playlist_name = get_or_create_genre_playlist(sp, user_id, genre)
        
        all_new_tracks = []

        # Obtener canciones de las playlists para ese género
        for playlist in playlists:
            old_tracks_path = f"data/{playlist['id'].split(':')[-1]}_tracks.txt"
            old_tracks = load_old_tracks(old_tracks_path)

            current_tracks = get_playlist_tracks(sp, playlist["id"])
            new_tracks = filter_new_tracks(old_tracks, current_tracks)
            recent_tracks = filter_recent_tracks(new_tracks, dias_recientes)  # Filtra las canciones en el rango de días
            unique_tracks = filter_duplicate_tracks(recent_tracks, global_track_ids)

            all_new_tracks.extend(unique_tracks)

        # Eliminar duplicados entre playlists
        unique_tracks = {track['track']['id']: track for track in all_new_tracks}.values()

        # Si hay canciones nuevas, agregarlas a la lista de reproducción sin mostrar nada por pantalla
        if unique_tracks:
            track_ids = [track['track']['id'] for track in unique_tracks]

            # Agregar canciones a la lista de reproducción por lotes
            batch_size = 100
            for i in range(0, len(track_ids), batch_size):
                batch = track_ids[i:i + batch_size]
                try:
                    sp.playlist_add_items(genre_playlist_id, batch)  # Añadir las canciones a la playlist
                except spotipy.exceptions.SpotifyException as e:
                    print(f"Error al añadir tracks en el rango {i}-{i + batch_size - 1}: {e}")

            # Guardar en el registro global y el histórico local
            save_global_tracks([track['track']['id'] for track in unique_tracks], global_tracks_path)
            for playlist in playlists:
                old_tracks_path = f"data/{playlist['id'].split(':')[-1]}_tracks.txt"
                save_new_tracks(old_tracks_path, unique_tracks)

        # Mostrar cuántas canciones se añadieron al final (solo por género)
        print(f"New {genre.upper()} Diciembre 2024: {len(unique_tracks)} canciones nuevas")

    input("\nPresiona Enter para salir...")


if __name__ == "__main__":
    main()
