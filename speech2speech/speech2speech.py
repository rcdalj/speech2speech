import configparser
import os
import queue
import sys
import threading
import time
import wave
from typing import Optional
from typing import Tuple

import openai
import psutil
import pyaudio
import pyautogui
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play


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


def exit_app():
    """Closes the currently focused browser tab and terminates a running Streamlit process.

    Returns:
        None
    """
    pid = None

    # Find the process ID associated with the Streamlit port
    for proc in psutil.process_iter():
        try:
            if "streamlit" in proc.name():
                pid = proc.pid
                break
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass

    if pid:
        # Close the browser tab
        if sys.platform.startswith('win'):
            pyautogui.hotkey('ctrl', 'w')
        elif sys.platform.startswith('darwin'):
            pyautogui.hotkey('command', 'w')
        else:
            pyautogui.press('ctrl+w')
            pyautogui.hotkey('ctrl', 'w')

        # Terminate the Streamlit process
        try:
            os.kill(pid, 9)
            print(f"Streamlit process with PID {pid} has been terminated.")
        except OSError as e:
            print(f"Error: {e}")
    else:
        print("Streamlit process not found")


def file_exists(file_path):
    """
    This function checks whether a file exists or not and returns a boolean value.

    :param file_path: The path of the file to be checked.
    :type file_path: str
    :return: True if the file exists, False otherwise.
    :rtype: bool
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)


def read_config() -> Tuple[str, int, int, int, str, str, str, str]:
    """
    Reads the configuration values from the 'config.ini' file.

    Returns:
        A tuple containing the source language audio filename (str), number of
        channels (int), sample rate (int), and chunk size (int),
        transcript filename (str), translation filename (str),
        target language audio filename (str) and language codes (str)

    Raises:
        configparser.Error: If there is an error reading the configuration file.
        ValueError: If any of the configuration values are invalid.
    """
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')

        source_lang_audio_filename = config.get('audio',
                                                'source_lang_audio_filename')
        channels = config.getint('audio', 'channels')
        rate = config.getint('audio', 'rate')
        chunk = config.getint('audio', 'chunk')
        transcript_filename = config.get('files', 'transcript_filename')
        translation_filename = config.get('files', 'translation_filename')
        target_lang_audio_filename = config.get('files',
                                                'target_lang_audio_filename')
        lang_codes = config.get('languages', 'lang_codes')
        log = config.getint('debugging', 'log')

        if channels <= 0:
            raise ValueError("'channels' must be a positive integer.")
        if rate <= 0:
            raise ValueError("'rate' must be a positive integer.")
        if chunk <= 0:
            raise ValueError("'chunk' must be a positive integer.")
        st.session_state.source_lang_audio_filename \
            = os.path.join("data", source_lang_audio_filename)
        st.session_state.transcript_filename = os.path.join("data",
                                                            transcript_filename)
        print(st.session_state.transcript_filename)
        st.session_state.translation_filename = os.path.join("data",
                                                             translation_filename)
        st.session_state.target_lang_audio_filename = os.path.join("data",
                                                                   target_lang_audio_filename)
        st.session_state.lang_codes = lang_codes.split(",")
        st.session_state.log = log

        return source_lang_audio_filename, channels, rate, chunk, \
            transcript_filename, translation_filename, \
            target_lang_audio_filename, lang_codes

    except configparser.Error as e:
        raise configparser.Error(f"Error reading configuration file: {e.args}")

    except ValueError as e:
        raise ValueError(f"Invalid configuration value: {e.args}")


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


def record_audio(channels: int, rate: int, chunk: int, filename: str,
                 stop_event: threading.Event,
                 audio_queue: queue.Queue) -> None:
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


def stream_record(source_lang_audio_filename: str, channels: int, chunk: int,
                  rate: int) -> None:
    """Record audio from microphone and save to file.

    Args:
        source_lang_audio_filename (str): Name of the output audio file.
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
                                               chunk,
                                               st.session_state.source_lang_audio_filename,
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


# Transcribe audio
def transcribe_audio() -> str:
    """Transcribes an audio file using OpenAI's API.

    Args:

    Returns:
        str: The transcribed text.
    """
    try:
        with open(st.session_state.source_lang_audio_filename,
                  "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            with open(st.session_state.transcript_filename, "w") as f:
                f.write(transcript["text"])
            return transcript["text"]
    except Exception as e:
        st.error(f"Error transcribing audio: {e}")
        return ""


def translate_text(target_lang: str) -> str:
    """
    Translates the given text into the specified target language using OpenAI's GPT-3 API.

    Args:
        target_lang (str): The ISO 639-1 language code for the target language.

    Returns:
        str: The translated text.
    """
    # Validate input
    if not target_lang:
        raise ValueError("'target_lang' argument is required.")

    try:
        with open(st.session_state.transcript_filename) as f:
            text = f.read()
    except Exception as e:
        print(f"Error reading transcript file: {e.args}")

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
        try:
            with open(st.session_state.translation_filename, "w") as f:
                f.write(response.choices[0].text.strip())
        except Exception as e:
            print(f"Error writing translation file: {e.args}")
        return response.choices[0].text.strip()
    except openai.Error as e:
        # Catch specific OpenAI errors
        st.write("OpenAI Error: ", e)
        return ""
    except Exception as e:
        # Catch all other errors
        st.write("Error: ", e)
        return ""


def read_the_translation() -> None:
    """
    Converts the translated text to speech and plays the audio file.

    Returns:
        None.
    """
    if not st.session_state.translation_filename:
        raise ValueError("A file with the text to be read must exist")
    if not st.session_state.target_lang:
        raise ValueError("'target_lang' must be chosen.")

    # Generate speech from translated text
    try:
        with open(st.session_state.translation_filename) as f:
            translation = f.read()
    except Exception as e:
        print(f"Error opening the translation file: {e.args}")
    myobj = gTTS(text=translation, lang=st.session_state.target_lang,
                 slow=False)

    # Save speech to MP3 file
    try:
        myobj.save(st.session_state.target_lang_audio_filename)
    except Exception as e:
        # Handle file save errors
        print(f"Error saving audio file: {e}")
        return None

    # Play MP3 file
    try:
        audio_file = AudioSegment.from_file(
            st.session_state.target_lang_audio_filename,
            format="mp3")
        # Play the MP3 file
        play(audio_file)
    except Exception as e:
        # Handle file play errors
        print(f"Error playing audio file: {e}")
        return None


def set_state():
    st.session_state.disabled = True


# Main function
def main() -> None:
    """
    Main function to run the Speech2Speech app.
    """
    try:
        st.set_page_config(page_title="Speech2Speech")
        st.header("Speech2Speech")
        source_lang_audio_filename, channels, rate, chunk, \
            transcript_filename, \
            translation_filename, target_lang_audio_filename, \
            lang_codes = read_config()
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

            target_lang = st.selectbox(
                "Target Language",
                st.session_state.lang_codes,
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

            if st.button("Exit App", use_container_width=True):
                st.write("App is now closing ...")
                exit_app()

        handle_record(record_button, source_lang_audio_filename, channels,
                      chunk, rate)
        handle_stop(stop_button)
        handle_transcribe(transcribe_button, source_lang_audio_filename,
                          placeholder_1)
        handle_translate(translate_button, target_lang, placeholder_1,
                         placeholder_2)
        handle_read_translation(read_translation_button, placeholder_1,
                                placeholder_2)
    except Exception as e:
        st.write("Error: ", e)


def handle_record(record_button: bool, source_lang_audio_filename: str,
                  channels: int, chunk: int, rate: int) -> None:
    """
    If record_button is True, record audio and save it to source_lang_audio_filename.

    Args:
        record_button (bool): Indicates whether the record button is pressed.
        source_lang_audio_filename (str): The name of the audio file to save.
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
        stream_record(st.session_state.source_lang_audio_filename, channels,
                      chunk, rate)


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


def handle_transcribe(transcribe_button: bool, source_lang_audio_filename: str,
                      placeholder_1) -> None:
    """
    If transcribe_button is True, transcribe the audio in source_lang_audio_filename and display the result.

    Args:
        transcribe_button (bool): Indicates whether the transcribe button is pressed.
        source_lang_audio_filename (str): The name of the audio file to transcribe.
        placeholder_1: A Streamlit placeholder to display the transcription.

    Raises:
        ValueError: If transcribe_button is not a boolean value.
        TypeError: If placeholder_1 is not a Streamlit placeholder.
    """
    if not isinstance(transcribe_button, bool):
        raise ValueError("transcribe_button must be a boolean value")

    if not hasattr(placeholder_1, "empty") or not hasattr(placeholder_1,
                                                          "success"):
        raise TypeError("placeholder_1 must be a Streamlit placeholder")

    if transcribe_button:
        transcription = transcribe_audio()
        st.session_state.transcription = transcription
        with placeholder_1:
            st.success(f"Transcription:\n{st.session_state.transcription}")
        try:
            with open(st.session_state.transcript_filename, "w") as f:
                f.write(st.session_state.transcription)
        except Exception as e:
            print(f"Error saving transcript file: {e.args}")


def handle_translate(translate_button: bool, target_lang: str, placeholder_1,
                     placeholder_2) -> None:
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

    if not hasattr(placeholder_1, "empty") or not hasattr(placeholder_1,
                                                          "success"):
        raise TypeError("placeholder_1 must be a Streamlit placeholder")

    if not hasattr(placeholder_2, "empty") or not hasattr(placeholder_2,
                                                          "info"):
        raise TypeError("placeholder_2 must be a Streamlit placeholder")

    if translate_button:
        transcript_filename = st.session_state.get("transcript_filename")
        try:
            with open(st.session_state.transcript_filename) as f:
                transcription = f.read()
                st.session_state.transcription = transcription
                print(st.session_state.transcription)
        except Exception as e:
            print(f"Error reading transcript file: {e.args}")
        if transcription is None:
            st.error("No transcription available for translation")
            return
        translation = translate_text(target_lang)
        st.session_state["translation"] = translation
        with placeholder_1:
            st.success(f"Transcription:\n{transcription}")
        with placeholder_2:
            st.info(f"Translation:\n{translation}")
        try:
            with open(st.session_state.translation_filename, "w") as f:
                f.write(translation)
        except Exception as e:
            print(f"Error saving translation file: {e.args}")


def handle_read_translation(read_translation_button: bool, placeholder_1,
                            placeholder_2) -> None:
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

    if not hasattr(placeholder_1, "empty") or not hasattr(placeholder_1,
                                                          "success"):
        raise TypeError("placeholder_1 must be a Streamlit placeholder")

    if not hasattr(placeholder_2, "empty") or not hasattr(placeholder_2,
                                                          "info"):
        raise TypeError("placeholder_2 must be a Streamlit placeholder")

    if read_translation_button:
        transcription = st.session_state.get("transcription")
        if transcription is None:
            raise KeyError(
                "Transcription not available in the Streamlit session state")
        translation = st.session_state.get("translation")
        if translation is None:
            raise KeyError(
                "Translation not available in the Streamlit session state")
        read_the_translation()
        with placeholder_1:
            st.success(f"Transcription:\n{transcription}")
        with placeholder_2:
            st.info(f"Translation:\n{translation}")


if __name__ == "__main__":
    main()
