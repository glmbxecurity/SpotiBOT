import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from SpotiBOTGUILESS import *  # Importamos las funciones de SpotiBOT.py
import nest_asyncio  # Necesario para entornos con un event loop ya activo
import sys
import os
sys.path.append('/root/SpotiBOTGUIless')

# Configuración básica de logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Tu ID de usuario de Telegram (obtenido previamente)
AUTHORIZED_USER_ID = 942135888  # Sustituye este número con tu ID real

# Aplicar nest_asyncio para permitir que asyncio funcione en entornos con bucles de eventos activos
nest_asyncio.apply()

# Variables globales
sp = None  # Variable para la instancia de Spotify
user_id = None  # Variable para el ID del usuario de Spotify
user_name = None  # Nombre del usuario

# Función para verificar si el mensaje viene de tu cuenta
def is_authorized_user(update: Update):
    return update.message.from_user.id == AUTHORIZED_USER_ID

# Definir el comando /start para dar la bienvenida
async def start(update: Update, context):
    if not is_authorized_user(update):
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return
    
    await update.message.reply_text("¡Hola! Soy SpotiBOT, un bot creado por GlmbXecurity. Con este bot puedes actualizar tus playlists de Spotify automáticamente. Actualizaremos las novedades de los ultimos días (Indicar días):")

# Función para manejar el comando que recibe el rango de días
async def handle_message(update: Update, context):
    if not is_authorized_user(update):
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return
    
    global sp, user_id, user_name
    
    # Procesar el mensaje recibido para obtener el rango de días
    try:
        # Si el mensaje es un número, lo tratamos como el rango de días
        dias_recientes = int(update.message.text)
        if dias_recientes <= 0:
            await update.message.reply_text("Por favor, ingresa un número positivo.")
            return
    except ValueError:
        # Si no es un número, usamos 7 días por defecto
        dias_recientes = 7
        await update.message.reply_text(f"Usando {dias_recientes} días por defecto.")

    await update.message.reply_text(f"Comenzando la actualización de novedades para los últimos {dias_recientes} días...")

    # Llamar la función principal de SpotiBOT
    result = run_spotibot(dias_recientes)

    # Enviar el resultado de SpotiBOT al usuario
    await update.message.reply_text(result)

# Función para ejecutar SpotiBOT
def run_spotibot(dias_recientes):
    try:
        # Autenticación de Spotify
        global sp, user_id, user_name
        sp = authenticate_spotify()
        user_id = sp.current_user()["id"]
        user_name = sp.current_user()["display_name"]

        # Cargar playlists desde el archivo
        playlists_by_genre = load_playlists("playlists.txt")
        if not playlists_by_genre:
            return "No se encontraron playlists válidas en 'playlists.txt'."

        # Cargar el registro global
        global_tracks_path = "global_tracks.txt"
        global_track_ids = load_global_tracks(global_tracks_path)

        # Procesar las playlists por género
        result_message = ""
        for genre, playlists in playlists_by_genre.items():
            genre_playlist_id, genre_playlist_name = get_or_create_genre_playlist(sp, user_id, genre)
            set_playlist_image(sp, genre_playlist_id, genre)

            all_new_tracks = []

            # Obtener canciones de las playlists para ese género
            for playlist in playlists:
                old_tracks_path = f"data/{playlist['id'].split(':')[-1]}_tracks.txt"
                old_tracks = load_old_tracks(old_tracks_path)

                current_tracks = get_playlist_tracks(sp, playlist["id"])
                new_tracks = filter_new_tracks(old_tracks, current_tracks)
                recent_tracks = filter_recent_tracks(new_tracks, dias_recientes)
                unique_tracks = filter_duplicate_tracks(recent_tracks, global_track_ids)

                all_new_tracks.extend(unique_tracks)

            # Eliminar duplicados entre playlists
            unique_tracks = {track['track']['id']: track for track in all_new_tracks}.values()

            if unique_tracks:
                track_ids = [track['track']['id'] for track in unique_tracks]

                # Agregar canciones a la lista de reproducción por lotes
                batch_size = 100
                for i in range(0, len(track_ids), batch_size):
                    batch = track_ids[i:i + batch_size]
                    sp.playlist_add_items(genre_playlist_id, batch)

                # Guardar en el registro global y el histórico local
                save_global_tracks([track['track']['id'] for track in unique_tracks], global_tracks_path)
                for playlist in playlists:
                    old_tracks_path = f"data/{playlist['id'].split(':')[-1]}_tracks.txt"
                    save_new_tracks(old_tracks_path, unique_tracks)

                result_message += f"{genre.upper()} {datetime.date.today().year}: {len(unique_tracks)} canciones nuevas agregadas.\n"
            else:
                result_message += f"{genre.upper()} {datetime.date.today().year}: No se encontraron canciones nuevas.\n"

        return result_message

    except Exception as e:
        return f"Hubo un error al ejecutar SpotiBOT: {str(e)}"

# Función principal que configura y ejecuta el bot
async def main():
    # Crea una instancia de la aplicación del bot con tu token
    application = Application.builder().token("7814670578:AAHtGcv8n64KAkODJLf-zP37wc23bIhCfVw").build()

    # Añadir manejadores de comandos y mensajes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Ejecutar el bot de manera continua
    await application.run_polling()

if __name__ == "__main__":
    try:
        # Intentamos ejecutar el código dentro de un bucle de eventos existente
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        # Si el bucle de eventos ya está en ejecución, creamos una tarea en segundo plano
        if 'This event loop is already running' in str(e):
            asyncio.create_task(main())  # Usa create_task si el bucle ya está en ejecución
        else:
            raise e
