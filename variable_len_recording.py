import openai
import os
import pyaudio
import wave
import threading
import sys
import streamlit as st
import queue

def get_api_key():
    with open('.password.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'API_KEY' in line:
                return line.split('=')[1].strip()

openai.api_key = get_api_key()

def stop_recording(stop_event):
    stop_event.set()
    st.session_state["stop_event"]=None

# Record audio
def record_audio(channels, rate, chunk, filename, stop_event, audio_queue):
    FORMAT = pyaudio.paInt16

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=channels,
                        rate=rate, input=True,
                        frames_per_buffer=chunk)
    print("Recording... Press return key to stop.")

    while not stop_event.is_set():
        data = stream.read(chunk)
        audio_queue.put(data)

    print("Finished recording")

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
    with open(filename, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        return transcript["text"]

# Main function
def main():
    global audio_filename
    # global stop_event
    stop_event=""
    audio_filename = "recorded_audio.wav"
    st.title("Speech2Speech")
    channels = st.sidebar.number_input(label="Channels", value=1)
    rate = st.sidebar.number_input(label="Rate", value=16000)
    chunk = st.sidebar.number_input(label="Chunk", value=1024)
    record= st.sidebar.button("Record Audio")
    if record:
        stop_event = threading.Event()
        st.session_state["stop_event"]=stop_event
        audio_queue = queue.Queue()

        record_thread = threading.Thread(target=record_audio,
                                         args=(channels, rate,
                                               chunk, audio_filename,
                                               stop_event, audio_queue))
        record_thread.start()

        #input("Press the return key to stop recording...\n")
        #stop_event.set()
        record_thread.join()

    stop=st.sidebar.button("Stop Recording")
    if stop:
        if "stop_event" in st.session_state:
            stop_recording(st.session_state["stop_event"])

    transcribe = st.sidebar.button("Transcribe")
    if transcribe:
        transcription = transcribe_audio(audio_filename)
        st.write("Transcription:")
        st.write(transcription)

if __name__ == "__main__":
    main()