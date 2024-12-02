import os
import datetime
from datetime import timedelta
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

# === Leer la configuración desde el fichero config.txt ===
def load_config(file_path="config.txt"):
    """Carga las configuraciones desde un archivo."""
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    config = {}
    with open(file_path, "r") as f:
        for line in f:
            key, value = line.strip().split("=", 1)
            config[key] = value
    return config

# === Funciones de Autenticación ===
def authenticate_spotify():
    """Autenticación con la API de Spotify."""
    config = load_config()
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=config["SPOTIPY_CLIENT_ID"],
        client_secret=config["SPOTIPY_CLIENT_SECRET"],
        redirect_uri=config["SPOTIPY_REDIRECT_URI"],
        scope="playlist-read-private playlist-modify-private"
    ))
    return sp

# === Función para cargar playlists desde un archivo ===
def load_playlists(file_path="playlists.txt"):
    """Carga las playlists desde un archivo y extrae sus IDs, nombres y géneros."""
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo '{file_path}' no existe.")
    
    playlists = {}
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line:  # Asegurarse de que la línea tenga el formato "genero=url"
                genre, url = line.split("=", 1)
                if "playlist/" in url:
                    playlist_id = url.split("playlist/")[1].split("?")[0]
                    if genre not in playlists:
                        playlists[genre] = []
                    playlists[genre].append({"id": f"spotify:playlist:{playlist_id}", "url": url})
    return playlists

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

def filter_recent_tracks(tracks, days):
    """Filtra canciones añadidas a las playlists originales en los últimos X días."""
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff_date = now - timedelta(days=days)
    recent_tracks = []

    for track in tracks:
        if track.get('added_at'):  # Validar que 'added_at' esté presente
            added_at = datetime.datetime.strptime(track['added_at'], '%Y-%m-%dT%H:%M:%SZ')
            added_at = added_at.replace(tzinfo=datetime.timezone.utc)
            if added_at >= cutoff_date:
                recent_tracks.append(track)
    return recent_tracks

def filter_duplicate_tracks(new_tracks, global_track_ids):
    """Filtra canciones que ya están en el registro global."""
    return [track for track in new_tracks if track['track'] and track['track']['id'] not in global_track_ids]

def get_existing_playlist_tracks(sp, playlist_id):
    """Obtiene los IDs de canciones ya presentes en una lista específica."""
    tracks = get_playlist_tracks(sp, playlist_id)
    return {track['track']['id'] for track in tracks if track['track']}  # Conjunto de IDs

# === Funciones de Persistencia ===
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
def get_or_create_monthly_playlist(sp, user_id, genre):
    """Crea o recupera la lista mensual actual para un género específico."""
    today = datetime.date.today()
    month_number = today.month
    year = today.year
    months_in_spanish = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    playlist_name = f"New {genre.capitalize()} Sounds {months_in_spanish[month_number - 1]} {year}"

    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        if playlist and 'name' in playlist and playlist['name'] == playlist_name:
            return playlist['id'], playlist_name

    new_playlist = sp.user_playlist_create(user_id, playlist_name, public=False)
    description = f"Playlist mensual de novedades del género {genre.capitalize()}"
    sp.playlist_change_details(new_playlist['id'], description=description)

    return new_playlist['id'], playlist_name

# === Selección de Rango de Tiempo ===
def seleccionar_rango_tiempo():
    """Selecciona el rango de tiempo para filtrar canciones según su fecha de agregado."""
    print("Por defecto se usarán los últimos 7 días para buscar canciones nuevas.")
    dias = input("Si deseas cambiar el rango de días, introduce un número (o presiona Enter para usar 7 días): ")
    try:
        dias_personalizados = int(dias) if dias else 7
        if dias_personalizados <= 0:
            print("Por favor, introduce un número positivo. Usando 7 días por defecto.")
            return 7
        return dias_personalizados
    except ValueError:
        print("Entrada inválida. Usando 7 días por defecto.")
        return 7

# === Función Principal ===
def main():
    sp = authenticate_spotify()
    user_id = sp.current_user()["id"]
    user_name = sp.current_user()["display_name"]

    print("SpotiBOT by GlmbXecurity")
    print(f"Bienvenid@ {user_name}")

    try:
        playlists_by_genre = load_playlists("playlists.txt")
    except Exception as e:
        print(f"Error al cargar playlists: {e}")
        exit(1)

    dias_recientes = seleccionar_rango_tiempo()
    global_tracks_path = "global_tracks.txt"
    global_track_ids = load_global_tracks(global_tracks_path)
    summary = []  # Para almacenar el resumen de canciones añadidas por género

    for genre, playlists in playlists_by_genre.items():
        monthly_playlist_id, monthly_playlist_name = get_or_create_monthly_playlist(sp, user_id, genre)
        print(f"\nProcesando género: {genre.capitalize()}")
        print(f"Playlist mensual: {monthly_playlist_name}")

        monthly_tracks_ids = get_existing_playlist_tracks(sp, monthly_playlist_id)
        all_new_tracks = []

        for playlist in playlists:
            current_tracks = get_playlist_tracks(sp, playlist["id"])
            recent_tracks = filter_recent_tracks(current_tracks, dias_recientes)
            unique_tracks = filter_duplicate_tracks(recent_tracks, global_track_ids)
            all_new_tracks.extend(unique_tracks)

        unique_tracks = {track['track']['id']: track for track in all_new_tracks}.values()
        final_tracks = [track for track in unique_tracks if track['track']['id'] not in monthly_tracks_ids]

        if final_tracks:
            batch_size = 100
            track_ids = [track['track']['id'] for track in final_tracks]

            for i in range(0, len(track_ids), batch_size):
                sp.playlist_add_items(monthly_playlist_id, track_ids[i:i + batch_size])

            save_global_tracks([track['track']['id'] for track in final_tracks], global_tracks_path)
            summary.append((genre, monthly_playlist_name, len(final_tracks)))
            print(f"Se añadieron {len(final_tracks)} canciones a la playlist '{monthly_playlist_name}'.")
        else:
            print(f"No se encontraron canciones nuevas para el género {genre.capitalize()}.")

    if summary:
        print("\n¿Quieres ver los detalles de las pistas añadidas? (s/n)")
        if input().lower() == "s":
            print("\n=== Resumen de canciones añadidas ===")
            for genre, playlist_name, count in summary:
                print(f"- {genre.capitalize()} -> {playlist_name}: {count} canciones añadidas")
            input("\nPresiona Enter para salir.")
        print("\nGracias por utilizar SpotiBOT by GlmbXecurity.")
        time.sleep(3)
    else:
        print("\nGracias por utilizar SpotiBOT by GlmbXecurity.")
        time.sleep(3)

if __name__ == "__main__":
    main()
