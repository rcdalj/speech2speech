# Speech2Speech
<img src="speech2speech/imgs/speech2speech.png" alt="image of main screen" 
height="762" width="723">

The Speech2Speech Python package is a Streamlit Web application that **models 
all phases of speech-to-speech translation**, including:
- recording speech in the source language, 
- converting the source language speech to source language text, 
- translating the source language text to target language text, and 
- converting the translated text to speech in the target language. 

As a web application, it can be accessed through any web browser and is 
**compatible with Linux, Mac, and Windows operating systems**.

Speech2Speech is currently **configured to translate to and from 13 different 
languages**. Although the quality of  translation may vary depending on the 
target language, it is pretty good for popular languages such as English, 
French, Portuguese, Spanish, German, Dutch and Italian. Speech2Speech **can be 
configured for many more than just these languages** (specified in the config.
ini file), as long as they are supported by Whisper AI, Chat-GPT and gtts, 
the packages on which it depends.


Speech2Speech is designed to be accessible to a **broad audience**. One of 
the key advantages of Speech2Speech is that it's incredibly easy to use:
- The package **automatically detects the source language used in speech**. The 
user therefore is not asked to specify it.
- There is **no need to train the software or the user before actually using 
the product**. It works well straight out of the box with no further tuning 
or configuration required. 
This makes it a highly accessible tool that anyone can use, regardless of 
their technical expertise or experience with speech recognition and machine 
translation technology. 

It is also hoped that this technology could be leveraged to develop 
products specifically designed for **persons with visual impairments**. It 
can empower them to have texts read aloud or dictate their texts 
and listen to them being read out loud before forwarding them to their 
intended recipients.

Each phase of the workflow creates a file, whose name is defined in the 
config.ini file. Advanced users can **start and/or interrupt the workflow 
wherever they need** by inserting their own files in the `speech2speech/data` 
subdirectory and adapting the config.ini file to refer to them. 

Prerequisites
-----------------------------------------------------------------------------
You need to [get an OpenAI API key](https://www.howtogeek.com/885918/how-to-get-an-openai-api-key/#autotoc_anchor_0) in order to use this app.
   
Speech2Speech local installation
--------------------------
In order to launch Speech2Speech locally follow these steps:

1. Make sure the microphone and speakers of your device are on.

2. Enter the following URL in your browser to download the project as a zip 
   file:
- `https://github.com/rcdalj/speech2speech/archive/refs/heads/master.zip`
3. Extract the contents of the zip file, thereby creating a local copy of 
   the project directory
4. In the terminal or command prompt, place yourself in the root of the 
   local copy of the project directory (where you find, namely, the requirements.txt file)
- `cd <full name of root of local project directory>`
3. Create a virtual environment:

3.1. On Mac and Linux:
- `python3 -m pip install --user virtualenv`
- `python3 -m venv venv`

3.2. On Windows:
- `py -m pip install --user virtualenv`
- `py -m venv env`
4. Activate the virtual environment:

4.1. On Mac and Linux
- `source venv/bin/activate`

4.2. On Windows:
- `.\env\Scripts\activate`
5. Install project dependencies:
- `pip install -r requirements.txt`
6. Type the following commands in the terminal to launch Speech2Speech:
- `cd speech2speech`
- `streamlit run speech2speech.py`


Workflow
----------
Here's a step-by-step guide on how to use the full workflow of Speech2Speech:

1. Copy your OpenAI API key and paste it into the text box below the label 
   "OpenAI API Key". The API key you enter will not be visible on 
   the screen by default.
2. Click the "Record Audio" button to start recording.
3. Begin speaking or reading aloud. When your dictation is finished, press 
   CTRL+E to stop recording it. Chat-GPT can 
   automatically detect the 
   language you're speaking (as long as it also supports it), so there's no 
   need to specify it.
4. Click the "Transcribe" button to convert your dictation into text.
5. Select your desired target language from the dropdown menu under "Target 
   Language".
6. Click the "Translate" button to translate the transcription into your 
   chosen target language. The translated text will appear on a blue 
   background after a few seconds.
7. Click the "Read Translation" button to listen to the translated text.
8. If you want to repeat the process with a new dictation, click the "Refresh 
   Page" button to reset the page.
   
As indicated above, you can also use just parts of this full workflow by specifying the name(s) of the file(s) you want to use in the config.ini file and by clicking the relevant button of the user interface.

What to do if you encounter issues
-------------------------------

If Chat-GPT or Speech2Speech get stuck or you encounter any issues, simply 
refresh the browser page. ChatGPT may, however, have lots of users at certain times 
of the day and be poorly responsive for a while.
