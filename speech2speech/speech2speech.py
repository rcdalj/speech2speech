import openai
import streamlit as st
import os
from gtts import gTTS
import pyautogui
import time
import configparser
from typing import Tuple
from typing import Optional
import pyaudio
import wave
import queue
import threading


def get_api_key() -> str:
    """
    Read the OpenAI API key from the environment and return it.

    Returns:
        str: The OpenAI API key.

    Raises:
        KeyError: If the API key environment variable is not found.
        ValueError: If the API key is an empty string.
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise KeyError("OPENAI_API_KEY environment variable not set")

    if not api_key.strip():
        raise ValueError("OPENAI_API_KEY is empty")

    return api_key.strip()


openai.api_key = get_api_key()

def read_config() -> Tuple[str, int, int, int]:
    """
    Reads the configuration values from the 'config.ini' file.

    Returns:
        A tuple containing the audio filename (str), number of channels (int), sample rate (int), and chunk size (int).

    Raises:
        configparser.Error: If there is an error reading the configuration file.
        ValueError: If any of the configuration values are invalid.
    """
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')

        audio_filename = config.get('audio', 'filename')
        channels = config.getint('audio', 'channels')
        rate = config.getint('audio', 'rate')
        chunk = config.getint('audio', 'chunk')

        if channels <= 0:
            raise ValueError("'channels' must be a positive integer.")
        if rate <= 0:
            raise ValueError("'rate' must be a positive integer.")
        if chunk <= 0:
            raise ValueError("'chunk' must be a positive integer.")

        return audio_filename, channels, rate, chunk

    except configparser.Error as e:
        raise configparser.Error(f"Error reading configuration file: {e}")

    except ValueError as e:
        raise ValueError(f"Invalid configuration value: {e}")


def stop_recording(stop_event: Optional[threading.Event] = None) -> None:
    """
    Stops the recording process by setting the stop event.

    Args:
        stop_event (threading.Event, optional): The stop event to set. If None, a new event is created.

    Raises:
        TypeError: If stop_event is not None and is not a threading.Event object.
    """
    if stop_event:
        if not isinstance(stop_event, threading.Event):
            raise TypeError("stop_event must be a threading.Event object.")
        stop_event.set()
    else:
        stop_event = threading.Event()
        stop_event.set()
    st.session_state.stop_event = stop_event

# Record audio
from typing import Tuple

def record_audio(channels: int, rate: int, chunk: int, filename: str,
                 stop_event: threading.Event, audio_queue: queue.Queue) -> None:
    """
    Records audio and saves it to a file.

    Args:
        channels (int): The number of audio channels to record.
        rate (int): The sampling rate of the audio.
        chunk (int): The number of audio frames to read at a time.
        filename (str): The name of the file to save the audio to.
        stop_event (threading.Event): The event to signal when recording should stop.
        audio_queue (queue.Queue): The queue to store recorded audio data in.

    Raises:
        ValueError: If channels, rate, or chunk are not positive integers.
        TypeError: If stop_event is not a threading.Event object or if audio_queue is not a queue.Queue object.
    """
    if not isinstance(stop_event, threading.Event):
        raise TypeError("stop_event must be a threading.Event object.")
    if not isinstance(audio_queue, queue.Queue):
        raise TypeError("audio_queue must be a queue.Queue object.")
    if channels <= 0 or not isinstance(channels, int):
        raise ValueError("channels must be a positive integer.")
    if rate <= 0 or not isinstance(rate, int):
        raise ValueError("rate must be a positive integer.")
    if chunk <= 0 or not isinstance(chunk, int):
        raise ValueError("chunk must be a positive integer.")

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



def refresh_page() -> None:
    """
    Refreshes the current web page by simulating the "CTRL + R" keyboard shortcut.

    Raises:
        pyautogui.FailSafeException: If the mouse is moved to the upper-left corner of the screen
            during the execution of this function, a `pyautogui.FailSafeException` is raised to
            prevent accidental execution of the function.
    """
    try:
        # Send the "CTRL + R" keyboard shortcut
        pyautogui.hotkey('ctrl', 'r')
    except pyautogui.FailSafeException:
        # If the mouse is moved to the upper-left corner of the screen during the execution of
        # this function, a `pyautogui.FailSafeException` is raised to prevent accidental
        # execution of the function.
        print(
            "Aborting refresh: mouse is in the upper-left corner of the screen")
        return

    # Wait for a short time to allow the page to refresh
    time.sleep(1)


import queue
import threading
from typing import Tuple


def stream_record(audio_filename: str, channels: int, chunk: int, rate: int) -> None:
    """Record audio from microphone and save to file.

    Args:
        audio_filename (str): Name of the output audio file.
        channels (int): Number of audio channels.
        chunk (int): Number of audio frames per buffer.
        rate (int): Sampling rate of audio.

    Raises:
        Exception: Raised if there is an error while recording audio.

    """
    try:
        stop_event = threading.Event()
        st.session_state.stop_event = stop_event
        audio_queue = queue.Queue()
        record_thread = threading.Thread(target=record_audio,
                                         args=(channels, rate,
                                               chunk, audio_filename,
                                               stop_event, audio_queue))
        record_thread.start()
    except Exception as e:
        st.write(f"Error starting recording: {e}")
        return

    st.write("Recording... Press 'Stop Recording' button to stop.")

    # Wait for the recording to finish or for the "Stop Recording" button to be pressed
    while record_thread.is_alive() and not stop_event.is_set():
        time.sleep(0.1)

    if record_thread.is_alive():
        # If the thread is still running, stop it and wait for it to finish
        stop_event.set()
        record_thread.join()

    st.write("Recording stopped by user")


#Transcribe audio
def transcribe_audio(filename: str) -> str:
    """Transcribes an audio file using OpenAI's API.

    Args:
        filename (str): The path to the audio file to transcribe.

    Returns:
        str: The transcribed text.
    """
    try:
        with open(filename, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            return transcript["text"]
    except Exception as e:
        st.error(f"Error transcribing audio: {e}")
        return ""



def translate_text(text: str, target_lang: str) -> str:
    """
    Translates the given text into the specified target language using OpenAI's GPT-3 API.

    Args:
        text (str): The text to translate.
        target_lang (str): The ISO 639-1 language code for the target language.

    Returns:
        str: The translated text.
    """
    # Validate input
    if not text or not target_lang:
        raise ValueError("Both 'text' and 'target_lang' arguments are required.")

    # Translate text using OpenAI's API
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Please translate the following text into '{target_lang}': {text}",
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )
        return response.choices[0].text.strip()
    except openai.Error as e:
        # Catch specific OpenAI errors
        st.write("OpenAI Error: ", e)
        return None
    except Exception as e:
        # Catch all other errors
        st.write("Error: ", e)
        return None



def read_the_translation() -> None:
    """
    Converts the translated text to speech and plays the audio file.

    Returns:
        None.
    """
    if not st.session_state.translation or not st.session_state.target_lang:
        raise ValueError("'translation' and 'target_lang' must be set in session state.")

    # Generate speech from translated text
    myobj = gTTS(text=st.session_state.translation, lang=st.session_state.target_lang, slow=False)

    # Save speech to MP3 file
    try:
        myobj.save("wwwelcome.mp3")
    except Exception as e:
        # Handle file save errors
        print(f"Error saving audio file: {e}")
        return None

    # Play MP3 file
    try:
        os.system("xdg-open wwwelcome.mp3")
    except Exception as e:
        # Handle file play errors
        print(f"Error playing audio file: {e}")
        return None

def set_state():
    st.session_state.disabled=True


# Main function
def main() -> None:
    """
    Main function to run the Speech2Speech app.
    """
    try:
        st.set_page_config(page_title="Speech2Speech")
        st.header("Speech2Speech")
        audio_filename, channels, rate, chunk = read_config()
        col1, col2, col3 = st.columns(3)
        st.session_state.disabled = False
        st.session_state.recording_stopped = False

        with col1:
            record_button = st.button(
                "Record Audio",
                key="record",
                on_click=set_state,
                use_container_width=True,
                disabled=st.session_state.disabled,
            )

            stop_button = st.button(
                "Stop Recording",
                use_container_width=True,
            )

            transcribe_button = st.button(
                "Transcribe",
                use_container_width=True,
            )

            placeholder_1 = st.empty()

            lang_codes = [
                "de", "en", "es", "fr", "it", "ja", "ko", "nl", "pt",
                "pt-BR", "ru", "zh", "zh-TW"
            ]

            target_lang = st.selectbox(
                "Target Language",
                lang_codes,
                key="target_lang",
            )

            translate_button = st.button(
                "Translate",
                use_container_width=True
            )

            placeholder_2 = st.empty()

            read_translation_button = st.button(
                "Read Translation",
                use_container_width=True,
            )

            refresh_button = st.button(
                "Refresh Page",
                on_click=refresh_page,
                use_container_width=True,
            )

        handle_record(record_button, audio_filename, channels, chunk, rate)
        handle_stop(stop_button)
        handle_transcribe(transcribe_button, audio_filename, placeholder_1)
        handle_translate(translate_button, target_lang, placeholder_1,
                         placeholder_2)
        handle_read_translation(read_translation_button, placeholder_1,
                                placeholder_2)
    except Exception as e:
        st.write("Error: ", e)

def handle_record(record_button: bool, audio_filename: str, channels: int, chunk: int, rate: int) -> None:
    """
    If record_button is True, record audio and save it to audio_filename.

    Args:
        record_button (bool): Indicates whether the record button is pressed.
        audio_filename (str): The name of the audio file to save.
        channels (int): The number of audio channels.
        chunk (int): The number of audio frames per buffer.
        rate (int): The sampling rate of the audio.

    Raises:
        ValueError: If channels or rate are not positive integers.
        IOError: If there was an error opening the audio file.
    """
    if not isinstance(channels, int) or channels <= 0:
        raise ValueError("channels must be a positive integer")
    if not isinstance(rate, int) or rate <= 0:
        raise ValueError("rate must be a positive integer")

    if record_button:
        stream_record(audio_filename, channels, chunk, rate)


def handle_stop(stop_button: bool) -> None:
    """
    If stop_button is True, stop the recording.

    Args:
        stop_button (bool): Indicates whether the stop button is pressed.

    Raises:
        ValueError: If stop_button is not a boolean value.
    """
    if not isinstance(stop_button, bool):
        raise ValueError("stop_button must be a boolean value")

    if stop_button:
        stop_recording(st.session_state.get("stop_event"))


import typing


def handle_transcribe(transcribe_button: bool, audio_filename: str, placeholder_1) -> None:
    """
    If transcribe_button is True, transcribe the audio in audio_filename and display the result.

    Args:
        transcribe_button (bool): Indicates whether the transcribe button is pressed.
        audio_filename (str): The name of the audio file to transcribe.
        placeholder_1: A Streamlit placeholder to display the transcription.

    Raises:
        ValueError: If transcribe_button is not a boolean value.
        TypeError: If placeholder_1 is not a Streamlit placeholder.
    """
    if not isinstance(transcribe_button, bool):
        raise ValueError("transcribe_button must be a boolean value")

    if not hasattr(placeholder_1, "empty") or not hasattr(placeholder_1, "success"):
        raise TypeError("placeholder_1 must be a Streamlit placeholder")

    if transcribe_button:
        transcription = transcribe_audio(audio_filename)
        st.session_state["transcription"] = transcription
        with placeholder_1:
            st.success(f"Transcription:\n{st.session_state.transcription}")

import typing


def handle_translate(translate_button: bool, target_lang: str, placeholder_1, placeholder_2) -> None:
    """
    If translate_button is True, translate the transcription in the Streamlit session state
    to the specified target language and display the results.

    Args:
        translate_button (bool): Indicates whether the translate button is pressed.
        target_lang (str): The target language for translation.
        placeholder_1: A Streamlit placeholder to display the transcription.
        placeholder_2: A Streamlit placeholder to display the translation.

    Raises:
        ValueError: If translate_button is not a boolean value or if target_lang is not a string.
        TypeError: If placeholder_1 or placeholder_2 is not a Streamlit placeholder.
    """
    if not isinstance(translate_button, bool):
        raise ValueError("translate_button must be a boolean value")

    if not isinstance(target_lang, str):
        raise ValueError("target_lang must be a string")

    if not hasattr(placeholder_1, "empty") or not hasattr(placeholder_1, "success"):
        raise TypeError("placeholder_1 must be a Streamlit placeholder")

    if not hasattr(placeholder_2, "empty") or not hasattr(placeholder_2, "info"):
        raise TypeError("placeholder_2 must be a Streamlit placeholder")

    if translate_button:
        transcription = st.session_state.get("transcription")
        if transcription is None:
            st.error("No transcription available for translation")
            return
        translation = translate_text(transcription, target_lang)
        st.session_state["translation"] = translation
        with placeholder_1:
            st.success(f"Transcription:\n{transcription}")
        with placeholder_2:
            st.info(f"Translation:\n{translation}")



def handle_read_translation(read_translation_button: bool, placeholder_1, placeholder_2) -> None:
    """
    If read_translation_button is True, read the translation in the Streamlit session state
    out loud and display the transcription and translation.

    Args:
        read_translation_button (bool): Indicates whether the read translation button is pressed.
        placeholder_1: A Streamlit placeholder to display the transcription.
        placeholder_2: A Streamlit placeholder to display the translation.

    Raises:
        ValueError: If read_translation_button is not a boolean value.
        TypeError: If placeholder_1 or placeholder_2 is not a Streamlit placeholder.
        KeyError: If transcription or translation is not available in the Streamlit session state.
    """
    if not isinstance(read_translation_button, bool):
        raise ValueError("read_translation_button must be a boolean value")

    if not hasattr(placeholder_1, "empty") or not hasattr(placeholder_1, "success"):
        raise TypeError("placeholder_1 must be a Streamlit placeholder")

    if not hasattr(placeholder_2, "empty") or not hasattr(placeholder_2, "info"):
        raise TypeError("placeholder_2 must be a Streamlit placeholder")

    if read_translation_button:
        transcription = st.session_state.get("transcription")
        if transcription is None:
            raise KeyError("Transcription not available in the Streamlit session state")
        translation = st.session_state.get("translation")
        if translation is None:
            raise KeyError("Translation not available in the Streamlit session state")
        read_the_translation()
        with placeholder_1:
            st.success(f"Transcription:\n{transcription}")
        with placeholder_2:
            st.info(f"Translation:\n{translation}")


if __name__ == "__main__":
    main()
