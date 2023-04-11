import openai
import os
import pyaudio
import wave
import threading
import sys
import streamlit as st
import queue
from gtts import gTTS


def get_api_key():
    with open('.password.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'API_KEY' in line:
                return line.split('=')[1].strip()


openai.api_key = get_api_key()


def stop_recording(stop_event):
    if stop_event:
        stop_event.set()
        st.session_state["stop_event"] = None


# Record audio
def record_audio(channels, rate, chunk, filename, stop_event, audio_queue):
    FORMAT = pyaudio.paInt16

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
            engine="text-davinci-002",
            prompt=f"Please translate the following text into "
                   f"{st.session_state.chosen_language}: \"{text}\"",
            max_tokens=1000,
            n=1,
            stop=None,
            temperature=0.7,
        )
        # st.write(response.choices[0].text.strip())
        return response.choices[0].text.strip()
    except Exception as e:
        st.write("Error: ", e)
        return None


def callback():
    st.write(st.session_state["chosen_language"])

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
    audio_filename = "recorded_audio.wav"
    channels = st.sidebar.number_input(label="Channels", value=1)
    rate = st.sidebar.number_input(label="Rate", value=16000)
    chunk = st.sidebar.number_input(label="Chunk", value=1024)
    placeholder = st.empty()
    record= st.sidebar.button("Record Audio")
    stop=st.button("Stop Recording")
    transcribe = st.button("Transcribe")
    chosen_language=st.text_input("Language to translate the "
                                      "transcription",
                                  on_change=callback, key="chosen_language")
    st.write(chosen_language)
    translate = st.button("Translate")
    read_translation=st.button("Read Translation")

    if record:
        stop_event = threading.Event()
        st.session_state["stop_event"] = stop_event
        audio_queue = queue.Queue()
        record_thread = threading.Thread(target=record_audio,
                                         args=(channels, rate,
                                               chunk, audio_filename,
                                               stop_event, audio_queue))
        record_thread.start()
        record_thread.join()
        st.stop()

    if stop:
        if "stop_event" in st.session_state:
            stop_recording(st.session_state["stop_event"])

    if transcribe:
        transcription = transcribe_audio(audio_filename)
        st.session_state["transcription"]= transcription
        with placeholder.container():
            st.write("Transcription:")
            st.write(transcription)

    if translate:
        #print(st.session_state["transcription"])
        st.session_state.translation=translate_text(st.session_state[
                                                  "transcription"])
        st.write(st.session_state.translation)

    if read_translation:
        read_the_translation()
if __name__ == "__main__":
    main()
