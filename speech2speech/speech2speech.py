import configparser
import os
import sys
import threading
import wave
from typing import Tuple

import openai
import psutil
import pyaudio
import pyautogui
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from pynput import keyboard
import markdown


# define a function to handle keyboard input
def on_press(key):
    if key == keyboard.Key.ctrl_l and not listener.recording:
        print("Recording... Press CTRL+E to stop recording.")
        listener.recording = True
    elif key == keyboard.Key.e and listener.recording:
        listener.recording = False
        return False


def check_file_exists(filepath, config_filename):
    """
    This function checks whether a file exists or not and returns a boolean value.

    Args:
    filepath (str): The path of the file to be checked.
    config_filename (str): the name of the config entry relative to this file

    Returns:
    """
    exists = os.path.exists(filepath) and os.path.isfile(filepath)
    if not exists:
        raise FileNotFoundError(f"The {config_filename} ("
                                f"{filepath}) does not exist")



# Main function
def main() -> None:
    """
    Main function to run the Speech2Speech app.
    """
    try:
        st.set_page_config(page_title="Speech2Speech")
        st.header("Speech2Speech")
        st.write("Speech2Speech is a Streamlit Web application that models all "
                 "phases of speech-to-speech translation, including recording "
                 "speech, speech-to-text, translation, "
                 "and translation-to-speech. "
                 "It can translate to and from 13 different languages and can "
                 "be configured for more, depending on the packages it depends "
                 "on. It automatically detects the source language used in "
                 "speech, making it easy for users with no technical expertise. "
                 "Speech2Speech creates a file for each phase of the workflow, "
                 "and advanced users can insert their own files in the data "
                 "subdirectory and modify the config.ini file. Overall, it is "
                 "a highly accessible tool for speech-to-speech translation. "
                 "**You need to [get an OpenAI API key]("
                 "https://www.howtogeek.com/885918/how-to-get-an-openai-api"
                 "-key/#autotoc_anchor_0) in order to use this app**. For "
                 "more info, please visit the [speech2speech Gihub site]("
                 "https://github.com/rcdalj/speech2speech).")

        read_config()
        col1, col2 = st.columns([1,2])
        st.session_state.disabled = False
        st.session_state.recording_stopped = False

        with col1:
            user_secret = st.text_input(
                label=":blue[OpenAI API Key]",
                placeholder="Paste your openAI API key, sk-",
                type="password",
            )
            if user_secret:
                openai.api_key = user_secret
            record_button = st.button(
                "Record Audio",
                key="record",
                use_container_width=True,
            )
            placeholder_1 = st.empty()
            placeholder_2 = st.empty()

            transcribe_button = st.button(
                "Transcribe",
                use_container_width=True,
            )

            placeholder_3 = st.empty()
            placeholder_4 = st.empty()

            target_lang = st.selectbox(
                "Target Language",
                st.session_state.lang_codes,
                key="target_lang",
            )

            translate_button = st.button(
                "Translate",
                use_container_width=True
            )

            placeholder_5 = st.empty()
            placeholder_6 = st.empty()
            placeholder_7 = st.empty()

            read_translation_button = st.button(
                "Read Translation",
                use_container_width=True,
            )
            placeholder_8 = st.empty()
            placeholder_9 = st.empty()

            if st.button("Exit App", use_container_width=True):
                st.write("App is now closing ...")
                exit_app()
        with col2:
            help = st.button("Help",
                             use_container_width=True)
            if help:
                try:
                    with open("../browser_help.md", 'r') as f:
                        content = f.read()
                    html = markdown.markdown(content)
                    st.markdown(html, unsafe_allow_html=True)
                except FileNotFoundError:
                    st.error("File README.md not found.")

        if record_button:
            placeholder_1.warning("Recording... Press CTRL+E to stop "
                                 "recording.")
            stop_event = threading.Event()
            st.session_state.stop_event = stop_event
            handle_record()
            placeholder_1.warning(f"Recording saved to"
                                f" {st.session_state.source_lang_audio_filename}")
        if transcribe_button:
            handle_transcribe(placeholder_3, placeholder_4)
        if translate_button:
            handle_translate(target_lang, placeholder_5,
                             placeholder_6, placeholder_7)
        if read_translation_button:
            handle_read_translation(placeholder_8,
                                    placeholder_9)
    except Exception as e:
        st.write("Error: ", e)


def read_config() -> Tuple[str, int, int, int, str, str, str, str]:
    """
    Reads the configuration values from the 'config.ini' file.

    Args:

    Returns:

    Raises:
        configparser.Error: If there is an error reading the configuration file.
        ValueError: If any of the configuration values are invalid.
    """
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')

        channels = config.getint('audio', 'channels')
        rate = config.getint('audio', 'rate')
        chunk = config.getint('audio', 'chunk')
        source_lang_audio_filename = config.get('audio',
                                                'source_lang_audio_filename')
        transcript_filename = config.get('files', 'transcript_filename')
        translation_filename = config.get('files', 'translation_filename')
        target_lang_audio_filename = config.get('files',
                                                'target_lang_audio_filename')
        check_file_exists(target_lang_audio_filename,
                          "target_lang_audio_filename")
        lang_codes = config.get('languages', 'lang_codes')
        log = config.getint('debugging', 'log')

        if not isinstance(channels, int) or channels <= 0:
            raise ValueError("'channels' must be a positive integer.")
        if not isinstance(rate, int) or rate <= 0:
            raise ValueError("'rate' must be a positive integer.")
        if not isinstance(chunk, int) or chunk <= 0:
            raise ValueError("'chunk' must be a positive integer.")
        st.session_state.channels = channels
        st.session_state.rate = rate
        st.session_state.chunk = chunk
        st.session_state.source_lang_audio_filename \
            = source_lang_audio_filename
        st.session_state.transcript_filename \
            = transcript_filename
        st.session_state.translation_filename \
            = translation_filename
        st.session_state.target_lang_audio_filename \
            = target_lang_audio_filename
        st.session_state.lang_codes = lang_codes.split(",")
        st.session_state.log = log

    except configparser.Error as e:
        raise configparser.Error(f"Error reading configuration file: {e.args}")

    except ValueError as e:
        raise ValueError(f"Invalid configuration value: {e.args}")


def handle_record() -> None:
    """Launches the recording of audio from the microphone.

    Args:

    Raises:
        Exception: Raised if there is an error while recording audio.

    """
    try:
        p = pyaudio.PyAudio()

        # open the stream
        stream = p.open(format=pyaudio.paInt16,
                        channels=st.session_state.channels,
                        rate=st.session_state.rate,
                        input=True,
                        frames_per_buffer=st.session_state.chunk)

        # start recording
        frames = []
        while listener.running:
            if listener.recording:
                data = stream.read(st.session_state.chunk)
                frames.append(data)

        # stop the stream and PyAudio
        stream.stop_stream()
        stream.close()
        p.terminate()

        # save the recording to a file
        file_name = st.session_state.source_lang_audio_filename
        wf = wave.open(file_name, "wb")
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(st.session_state.rate)
        wf.writeframes(b"".join(frames))
        wf.close()

    except Exception as e:
        print(f"Error: {e.args}")


def handle_transcribe(placeholder_3, placeholder_4) -> None:
    """
    If transcribe_button is clicked, transcribe the audio in
    source_lang_audio_filename and display it.

    Args:
        placeholder_3: A Streamlit placeholder to display the transcript.
        placeholder_4: A Streamlit placeholder to display the
            location of the transcript file.
    """
    check_file_exists(st.session_state.source_lang_audio_filename,
                      "source_lang_audio_filename")
    st.session_state.transcription = transcribe_audio()
    with placeholder_3:
        st.success(f"Transcription:\n{st.session_state.transcription}")
    try:
        with open(st.session_state.transcript_filename, "w") as f:
            f.write(st.session_state.transcription)
    except Exception as e:
        print(f"Error saving transcript file: {e.args}")
    placeholder_4.warning(
        f"Transcription saved to "
        f"{st.session_state.transcript_filename}")


def transcribe_audio() -> str:
    """Transcribe an audio file using OpenAI's Whisper API.

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


def handle_translate(target_lang: str, placeholder_5, placeholder_6,
                     placeholder_7) -> None:
    """
    If translate_button is clicked, translate the transcription in the
    Streamlit session state to the specified target language and display the results.

    Args:
        target_lang (str): The target language for translation.
        placeholder_5: A Streamlit placeholder to display the transcript text.
        placeholder_6: A Streamlit placeholder to display the translation text.
        placeholder_7: A Streamlit placeholder to display the
        location of the translation file.

    Raises:
        ValueError: If target_lang is not a string.
    """
    if not isinstance(target_lang, str):
        raise ValueError("target_lang must be a string")

    check_file_exists(st.session_state.transcript_filename,
                      "transcript_filename")
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
    with placeholder_5:
        st.success(f"Transcription:\n{transcription}")
    with placeholder_6:
        st.info(f"Translation:\n{translation}")
    try:
        with open(st.session_state.translation_filename, "w") as f:
            f.write(translation)
        placeholder_7.warning(
            f"Translation saved to "
            f"{st.session_state.translation_filename}")
    except Exception as e:
        print(f"Error saving translation file: {e.args}")


def translate_text(target_lang: str) -> str:
    """
    Translates the given text into the specified target language using
    OpenAI's GPT-3 API.

    Args:
        target_lang (str): The ISO 639-1 language code for the target language.

    Returns:
        str: The translated text.

    Raises:
        ValueError if target_lang not chosen
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
            temperature=0,
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


def handle_read_translation(placeholder_8,
                            placeholder_9) -> None:
    """
    If read_translation_button is clicked, read out the translation aloud and
    display both the transcription (source language text) and its translation.

    Args:
        placeholder_8: A Streamlit placeholder to display the transcription.
        placeholder_9: A Streamlit placeholder to display the translation.

    Raises:
        KeyError: If transcription or translation filenames not available
        in the Streamlit session state.
    """
    transcription = st.session_state.get("transcription")
    check_file_exists(st.session_state.translation_filename,
                      "translation_filename")
    translation = st.session_state.get("translation")
    with placeholder_8:
        st.info(f"Translation:\n{translation}")
    if not transcription or not translation:
        raise KeyError("The transcript_filename or translation_filename are "
                       "absent or empty.")
    read_the_translation()
    placeholder_9.warning(
        f"Target language audio file saved to "
        f"{st.session_state.target_lang_audio_filename}")


def read_the_translation() -> None:
    """
    Converts the translated text to speech and plays the resulting audio file
    using Google gtts.

    Raises:
        ValueError if the translation does not exist or if the target_lang not
        chosen
    """
    if not st.session_state.translation_filename:
        raise ValueError("A file with the text to be read must exist")
    if not st.session_state.target_lang:
        raise ValueError("The 'target_lang' must be chosen.")

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


if __name__ == "__main__":
    # create a listener to capture keyboard input
    listener = keyboard.Listener(on_press=on_press)
    listener.recording = False
    listener.start()
    main()
