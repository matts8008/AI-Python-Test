import requests
import random
import pygame
import os
import tempfile
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading

def search_shows(song):
    url = f"https://archive.org/advancedsearch.php?q=grateful+dead+{song}&fl%5B%5D=identifier&rows=500&page=1&output=json"
    response = requests.get(url)
    data = response.json()
    shows = [result['identifier'] for result in data['response']['docs']]
    return shows

def find_audio_file(show, song):
    url = f"https://archive.org/metadata/{show}"
    response = requests.get(url)
    data = response.json()
    audio_files = [file for file in data['files'] if file['format'] == 'VBR MP3' and song.lower() in file['name'].lower()]
    if audio_files:
        return random.choice(audio_files)
    else:
        metadata = data.get('metadata', {})
        date = metadata.get('date', 'Unknown Date')
        show_name = metadata.get('title', 'Unknown Show')
        status_label.config(text=f"'{song}' not played on {date} - {show_name}")
    return None

def get_song_info(show, audio_file):
    url = f"https://archive.org/metadata/{show}"
    response = requests.get(url)
    data = response.json()
    metadata = data.get('metadata', {})
    return {
        'artist': metadata.get('creator', 'Unknown Artist'),
        'album': metadata.get('title', 'Unknown Album'),
        'title': audio_file['name']
    }

def play_audio(show, audio_file):
    global paused, playing, current_filename
    url = f"https://archive.org/download/{show}/{audio_file['name']}"
    filename = os.path.join(tempfile.gettempdir(), f"{audio_file['name']}.mp3")
    current_filename = filename  # Store the current filename
    status_label.config(text=f"Downloading audio file: {filename}")
    with open(filename, 'wb') as f:
        response = requests.get(url)
        f.write(response.content)
    status_label.config(text=f"Playing audio file: {filename}")
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    playing = True
    paused = False
    pause_button.config(text="Pause", command=pause_song)
    while pygame.mixer.music.get_busy() and not paused:
        pygame.time.Clock().tick(10)
    if not paused:
        status_label.config(text=f"Finished playing audio file: {filename}")
        playing = False
        pygame.mixer.music.unload()  # Unload the music file
        pygame.time.delay(1000)  # Add a short delay before deleting the file
        delete_audio_file()  # Delete the audio file when playback finishes
        
def delete_audio_file():
    global current_filename
    if current_filename:
        try:
            os.remove(current_filename)
            print(f"Deleted audio file: {current_filename}")
        except Exception as e:
            print(f"Error deleting audio file: {str(e)}")
        current_filename = None

def pause_song():
    global paused
    if playing:
        if paused:
            pygame.mixer.music.unpause()
            pause_button.config(text="Pause")
            paused = False
        else:
            pygame.mixer.music.pause()
            pause_button.config(text="Resume")
            paused = True

def play_song():
    global playing, recent_songs
    if not playing:
        song = song_var.get()
        if song not in recent_songs:
            recent_songs.append(song)
            if len(recent_songs) > 5:
                recent_songs.pop(0)
            song_dropdown['values'] = recent_songs
        status_label.config(text=f"Fetching show data for '{song}'...")
        shows = search_shows(song)
        status_label.config(text=f"Found {len(shows)} shows containing the song '{song}'")
        
        while shows:
            show = shows.pop(random.randint(0, len(shows) - 1))
            audio_file = find_audio_file(show, song)
            if audio_file:
                song_info = get_song_info(show, audio_file)
                song_label.config(text=f"Now playing: {song_info['title']}")
                artist_label.config(text=f"Artist: {song_info['artist']}")
                album_label.config(text=f"Album: {song_info['album']}")
                play_audio(show, audio_file)
                break
        else:
            status_label.config(text=f"No audio files found for the song '{song}'")

def play_song_thread():
    thread = threading.Thread(target=play_song)
    thread.start()

def delete_audio_file():
    global current_filename
    if current_filename:
        try:
            os.remove(current_filename)
            print(f"Deleted audio file: {current_filename}")
        except Exception as e:
            print(f"Error deleting audio file: {str(e)}")
        current_filename = None

def on_close():
    delete_audio_file()  # Delete the audio file when the app is closed
    window.destroy()

pygame.mixer.init()

window = tk.Tk()
window.title("Grateful Dead Song Player")
window.geometry("500x400")
window.configure(bg="#F0F0F0")

style = ttk.Style()
style.configure("TLabel", background="#F0F0F0", foreground="#333333", font=("Arial", 12))
style.configure("TButton", background="#4CAF50", foreground="white", font=("Arial", 12, "bold"))

title_label = ttk.Label(window, text="Grateful Dead Song Player", font=("Arial", 18, "bold"))
title_label.pack(pady=20)

song_frame = ttk.Frame(window)
song_frame.pack(pady=10)

song_label = ttk.Label(song_frame, text="Select or enter a Grateful Dead song:")
song_label.pack(side=tk.LEFT)

recent_songs = []
song_var = tk.StringVar()
song_dropdown = ttk.Combobox(song_frame, textvariable=song_var, values=recent_songs, width=30)
song_dropdown.pack(side=tk.LEFT, padx=10)

button_frame = ttk.Frame(window)
button_frame.pack(pady=10)

play_button = ttk.Button(button_frame, text="Play Song", command=play_song_thread)
play_button.pack(side=tk.LEFT, padx=5)

paused = False
playing = False
pause_button = ttk.Button(button_frame, text="Pause", command=pause_song)
pause_button.pack(side=tk.LEFT, padx=5)

info_frame = ttk.Frame(window)
info_frame.pack(pady=10)

song_label = ttk.Label(info_frame, text="")
song_label.pack()

artist_label = ttk.Label(info_frame, text="")
artist_label.pack()

album_label = ttk.Label(info_frame, text="")
album_label.pack()

status_label = ttk.Label(window, text="Ready")
status_label.pack(pady=10)

window.protocol("WM_DELETE_WINDOW", on_close)  # Bind the on_close function to the window close event

window.mainloop()

pygame.mixer.quit()
