# SpotiBOT by GlmbXecurity

##### ES
SpotiBOT es un bot para Spotify que facilita la gestión automática de playlists, agregando nuevas canciones de manera eficiente y organizada. Está diseñado para recolectar canciones nuevas de varias playlists y agregarlas a una playlist mensual creada específicamente para ello. Utiliza la API de Spotify para interactuar con las playlists y las canciones.

----------
##### EN
SpotiBOT is a Spotify bot that facilitates the automatic management of playlists, efficiently and systematically adding new songs. It is designed to collect new tracks from multiple playlists and add them to a monthly playlist specifically created for this purpose. It uses the Spotify API to interact with playlists and tracks.

----------

[Español](#tabla-de-contenidos-en-espa%C3%B1ol) | [ English](#table-of-contents-in-english)

## Tabla de Contenidos en Español

-   [Características](#caracter%C3%ADsticas)
-   [Screenshots del programa](#screenshots-del-programa)
-   [Instalación](#instalaci%C3%B3n)
-   [Uso](#uso)
-   [Resolución de problemas](#resolucion-de-problemas)

## Características

-   **Autenticación con Spotify**: Se conecta a tu cuenta de Spotify de manera segura utilizando el flujo de autorización estándar.
-   **Cargar Playlists**: Permite cargar las playlists desde un archivo `playlists.txt` para obtener las canciones de ellas.
-   **Filtrado de Canciones Nuevas**: Filtra las canciones nuevas y las canciones duplicadas.
-   **Playlist Mensual Automática**: Crea y/o actualiza una playlist mensual con las canciones nuevas del mes, asignando un nombre basado en el mes y el año.
-   **Soporte para múltiples playlists**: Puedes cargar varias playlists y agregar canciones a la playlist mensual.
-   **Historial de Canciones**: Mantiene un historial de las canciones ya procesadas para evitar duplicados.

## Screenshots del programa

#### EJECUCIÓN DEL PROGRAMA

![image](https://raw.githubusercontent.com/glmbxecurity/SpotiBOT/refs/heads/main/screenshots/ejecucion.jpeg)

#### RESULTADO FINAL

![image](https://raw.githubusercontent.com/glmbxecurity/SpotiBOT/refs/heads/main/screenshots/spotify.jpeg)

## Instalación

Para usar SpotiBOT, primero necesitas tener Python 3.x (Probado en Python 3.13.0)  
Luego debes instalar `spotipy` y `python-dotenv`


```bash
pip install spotipy
pip install python-dotenv
``` 

### 1. Clonar el repositorio

Clona el repositorio de GitHub en tu máquina local:


`git clone https://github.com/tu_usuario/SpotiBOT.git` 

### 2. Configuración

Antes de ejecutar el programa, necesitas configurar las credenciales de la API de Spotify. Para ello, crea un archivo `config.txt` en el directorio raíz del proyecto con la siguiente estructura:

```bash
SPOTIPY_CLIENT_ID=tu_client_id
SPOTIPY_CLIENT_SECRET=tu_client_secret
SPOTIPY_REDIRECT_URI=tu_redirect_uri
``` 

Estos valores los puedes obtener creando una aplicación en [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications).

![image](https://raw.githubusercontent.com/glmbxecurity/SpotiBOT/refs/heads/main/screenshots/config.jpeg)

### 3. Crear el archivo `playlists.txt`

Crea un archivo `playlists.txt` en el directorio raíz del proyecto. Este archivo debe contener las URL de las playlists de las que deseas obtener las canciones, una por línea. Por ejemplo:

`https://open.spotify.com/playlist/playlist_id_1` 

![image](https://raw.githubusercontent.com/glmbxecurity/SpotiBOT/refs/heads/main/screenshots/playlists.jpeg)

### 4. Uso

Una vez que hayas configurado todo, puedes ejecutar el script para que SpotiBOT recoja las canciones nuevas de las playlists y las agregue a la playlist mensual.

Ejecuta el script desde la terminal:

`python SpotiBOT.py` 

### Resolucion de problemas

* Hay ciertas playlists que, por algún motivo, no es capaz de leer, ya sea porque son privadas o porque necesiten de algún permiso especial. Hasta que se dé con la solución, esas playlists se deben de omitir para evitar fallos.

* Para ejecutar la opción de "Los últimos 30 días", previamente has de haber sincronizado al menos los últimos 7 o 15 días, sino Spotify detecta muchas requests de una vez y rechaza la petición.

* Si eliminas canciones por error y no querías, o eliminas la playlist, la manera de corregir y volver a empezar es eliminando la carpeta `data` (se genera al lanzar el programa), y eliminar el fichero `global_tracks.txt`.

----------

## Table of Contents in English

-   [Features](#features)
-   [Program Screenshots](#program-screenshots)
-   [Installation](#installation)
-   [Usage](#usage)
-   [Troubleshooting](#troubleshooting)

## Features

-   **Spotify Authentication**: Connects to your Spotify account securely using the standard authorization flow.
-   **Load Playlists**: Allows you to load playlists from a `playlists.txt` file to gather songs from them.
-   **New Song Filtering**: Filters out new songs and duplicates.
-   **Automatic Monthly Playlist**: Creates and/or updates a monthly playlist with the new songs from the month, assigning a name based on the month and year.
-   **Support for Multiple Playlists**: You can load multiple playlists and add songs to the monthly playlist.
-   **Song History**: Keeps track of songs already processed to avoid duplicates.

## Program Screenshots

#### PROGRAM EXECUTION

![image](https://raw.githubusercontent.com/glmbxecurity/SpotiBOT/refs/heads/main/screenshots/ejecucion.jpeg)

#### FINAL RESULT

![image](https://raw.githubusercontent.com/glmbxecurity/SpotiBOT/refs/heads/main/screenshots/spotify.jpeg)

## Installation

To use SpotiBOT, you first need to have Python 3.x (Tested on Python 3.13.0)  
Then, install `spotipy` and `python-dotenv`

```bash
pip install spotipy
pip install python-dotenv
``` 

### 1. Clone the repository

Clone the GitHub repository to your local machine:

`git clone https://github.com/your_user/SpotiBOT.git` 

### 2. Configuration

Before running the program, you need to configure your Spotify API credentials. To do this, create a `config.txt` file in the root directory of the project with the following structure:

```bash
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=your_redirect_uri
``` 

You can get these values by creating an app in [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications).

![image](https://raw.githubusercontent.com/glmbxecurity/SpotiBOT/refs/heads/main/screenshots/config.jpeg)

### 3. Create the `playlists.txt` file

Create a `playlists.txt` file in the root directory of the project. This file should contain the URLs of the playlists you want to get songs from, one per line. For example:

`https://open.spotify.com/playlist/playlist_id_1` 

![image](https://raw.githubusercontent.com/glmbxecurity/SpotiBOT/refs/heads/main/screenshots/playlists.jpeg)

### 4. Usage

Once everything is configured, you can run the script for SpotiBOT to collect new songs from the playlists and add them to the monthly playlist.

Run the script from the terminal:

`python SpotiBOT.py` 

### Troubleshooting

* Some playlists might not be accessible, either because they are private or require special permissions. Until a solution is found, those playlists should be omitted to avoid errors.

* To use the "Last 30 Days" option, you must have already synced at least the last 7 or 15 days, otherwise Spotify detects too many requests at once and rejects the request.

* If you accidentally delete songs or playlists, you can reset everything by deleting the `data` folder (generated when you run the program), and remove the `global_tracks.txt` file.