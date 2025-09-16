import streamlit as st
import yt_dlp
import os

def download_best_audio(url, outtmpl="song_output/%(title)s-%(id)s.%(ext)s"):
    """
    Télécharge la meilleure qualité audio d'une URL, la convertit en MP3 320kbps
    avec la miniature et les métadonnées intégrées.
    """
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'quiet': True, # Mettre à False pour le débogage
        'noplaylist': True,
        'writethumbnail': True,
        'ffmpeg_location':'/opt/homebrew/bin',

        # La chaîne de post-traitement. L'ordre est crucial.
        'postprocessors': [
            # 1. Extrait l'audio et le convertit en MP3
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            },
            # 2. Convertit la miniature en JPG pour une meilleure compatibilité
            {
                'key': 'FFmpegThumbnailsConvertor',
                'format': 'jpg',
            },
            # 3. Intègre la miniature JPG dans le fichier MP3
            {
                'key': 'EmbedThumbnail',
            },
            # 4. Intègre les métadonnées (titre, artiste, etc.) dans le fichier MP3
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            },
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            # Le nom du fichier est modifié par les post-processeurs,
            # il faut donc le reconstruire.
            base = ydl.prepare_filename(info).rsplit('.', 1)[0]
            final_path = base + '.mp3'
            
            if os.path.exists(final_path):
                print(f"Téléchargement réussi : {final_path}")
                return final_path
            else:
                # Si le fichier d'origine était déjà un MP3, le nom peut ne pas avoir changé
                original_file = ydl.prepare_filename(info)
                if os.path.exists(original_file) and original_file.endswith('.mp3'):
                     print(f"Téléchargement réussi (fichier original MP3) : {original_file}")
                     return original_file
                raise RuntimeError("Le post-traitement a échoué, le fichier MP3 final est introuvable.")

        except Exception as e:
            print(f"Une erreur est survenue durant le téléchargement : {e}")
            return None

def format_duration(seconds):
    if seconds is None:
        return ''
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"

def format_views(count):
    if count is None:
        return ''
    for unit in ['','k','M','B']:
        if count < 1000:
            return f"{count}{unit}"
        count //= 1000
    return f"{count}B+"

def search_topic(artist, title, max_results=3):
    query = f'ytsearch{max_results}:{artist} "topic" "{title}"'
    opts = {'skip_download': True, 'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(query, download=False)
    return info.get('entries', [])

def return_entries_info(entries):
    results = []
    for e in entries:
        uploader = e.get('uploader') or e.get('channel') or ''
        results.append([
            e.get('id'),
            e.get('webpage_url'),
            e.get('title'),
            e.get('description', ''),
            uploader,
            format_duration(e.get('duration')),
            format_views(e.get('view_count')),
            e.get("thumbnails")[-1].get("url")
        ])
    return results
    

artist = st.text_input("Artist")
title = st.text_input("Title")

if st.button("Search"):
    entries = search_topic(artist, title)
    entries_info = return_entries_info(entries)

    for e in entries_info:
        st.divider()
        st.text(f"Title : {e[2]}")
        st.text(f"Artist : {e[4]}")
        st.text(f"Duration: {e[5]}")
        st.text(f"Views: {e[6]}")
        st.image(e[7])

        st.button("Download", key=e[0], on_click=lambda : download_best_audio(e[1]))