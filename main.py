import openai
import os
import pyaudio
import wave
import threading
import sys
import streamlit as st
import queue
from gtts import gTTS
import configparser
import webbrowser



def get_api_key():
    with open('.password.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'API_KEY' in line:
                return line.split('=')[1].strip()

openai.api_key = get_api_key()

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')

    audio_filename = config.get('audio', 'filename')
    channels = config.getint('audio', 'channels')
    rate = config.getint('audio', 'rate')
    chunk = config.getint('audio', 'chunk')
    return audio_filename, channels, rate, chunk

def stop_recording(stop_event):
    import numpy
    if stop_event:
        stop_event.set()
    else:
        stop_event = threading.Event()
        stop_event.set()
    st.session_state.stop_event=stop_event

# Record audio
def record_audio(channels, rate, chunk, filename, stop_event, audio_queue):
    FORMAT = pyaudio.paInt32

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=channels,
                        rate=rate, input=True,
                        frames_per_buffer=chunk)
    st.write("Recording... Press 'Stop Recording' button to stop.")

    while not stop_event.is_set():
        data = stream.read(chunk)
        audio_queue.put(data)

    st.write("Finished recording")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(rate)
        wf.writeframes(b''.join(list(audio_queue.queue)))

import pyautogui
import time

def refresh_page():
    # Send the "CTRL + R" keyboard shortcut
    pyautogui.hotkey('ctrl', 'r')

    # Wait for a short time to allow the page to refresh
    time.sleep(1)


def stream_record(audio_filename, channels, chunk, rate):
    stop_event = threading.Event()
    st.session_state.stop_event = stop_event
    audio_queue = queue.Queue()
    record_thread = threading.Thread(target=record_audio,
                                     args=(channels, rate,
                                           chunk, audio_filename,
                                           stop_event, audio_queue))
    record_thread.start()
    record_thread.join()
    st.stop()


# Transcribe audio
def transcribe_audio(filename):
    try:
        with open(filename, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            return transcript["text"]
    except Exception as e:
        st.write("Error: ", e)
        return None

def translate_text(text):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Please translate the following text into "
                   f"'{st.session_state.chosen_language}': {text}",
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        st.write("Error: ", e)
        return None


def read_the_translation():
    myobj = gTTS(text=st.session_state.translation,
                 lang=st.session_state.chosen_language, slow=False)

    # Saving the converted audio in a mp3 file named
    # welcome
    try:
        myobj.save("welcome.mp3")
    except Exception as e:
        pass

    # Playing the converted file
    os.system("xdg-open  welcome.mp3")

# Main function
def main():
    st.set_page_config(page_title="Speech2Speech")
    audio_filename, channels, rate, chunk = read_config()
    col1, col2, col3=st.columns(3)
    with col1:
        record= st.button("Record Audio", use_container_width=True)
        stop=st.button("Stop Recording", use_container_width=True)
        transcribe = st.button("Transcribe", use_container_width=True)
        placeholder=st.empty()
        lang_codes = ["en", "es", "fr", "de", "it", "pt", "pt-BR", "nl", "ru",
                  "ja", "zh", "zh-TW", "ko"]
        st.session_state.chosen_language=st.selectbox("Target Language",
                                                  lang_codes)
        translate = st.button("Translate", use_container_width=True)
        placeholder1=st.empty()
        read_translation=st.button("Read Translation",
                                   use_container_width=True)
        refresh=st.button("Refresh Page", on_click=refresh_page,
                          use_container_width=True)

    if record:
        stream_record(audio_filename, channels, chunk, rate)

    if stop:
        # if "stop_event" in st.session_state:
        stop_recording(st.session_state["stop_event"])

    if transcribe:
        transcription = transcribe_audio(audio_filename)
        st.session_state["transcription"]= transcription
        with placeholder:
            st.write("Transcription:")
            st.write(transcription)

    if translate:
        #print(st.session_state["transcription"])
        st.session_state.translation=translate_text(st.session_state[
                                                  "transcription"])
        with placeholder:
            st.write(f"""Transcription:\n{st.session_state.transcription}""")
        with placeholder1:
            st.write(f"""Translation:\n{st.session_state.translation}""")

    if read_translation:
        read_the_translation()
        with placeholder:
            st.write(f"""Transcription:\n{st.session_state.transcription}""")
        with placeholder1:
            st.write(f"""Translation:\n{st.session_state.translation}""")




if __name__ == "__main__":
    main()
