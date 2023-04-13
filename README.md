# Speech2Speech

Speech2Speech is a Python package that performs vocal recognition of 
your speech, followed by translation to a target language of your choice, 
which is then read out loud by a high-quality voice.

As long as your speech is in one of the many languages that Chat-GPT can transcribe, you do not have to indicate the source language you are using.

Prerequisites
-----------------------------------------------------------------------------
Before using Speech2Speech, you need to sign up for an OpenAI account, create an API key, and set up an environment variable. Here's how to do it:

1. **Signup and Create an OpenAI Account**: Go to the OpenAI website and 
   click on 
the "Sign up" button in the top right corner. Enter your name, email address, and password in the provided fields, and click on the "Sign up" button. Once you have signed up, you will be directed to the OpenAI dashboard.

2. **Create an OpenAI API Key**: Click on Personal at the right upper corner 
   and 
on the "View API Keys" tab in the OpenAI dashboard. Click on the "Create new secret key" button. Give your API key a name and select the type of API key you want to create (restricted or full). Once you have created your API key, copy it to your clipboard. Make sure to keep your API key secure, as it provides access to powerful computing resources and data.

3. **Create an Environment Variable to Load Your OpenAI API Key**:

   A. **Ubuntu and Mac**
   
   Open your terminal. Type the following command to open your shell profile file:
      
         nano ~/.bashrc
      
   Scroll to the bottom of the file and add the following line:
   
         export OPENAI_API_KEY=<YOUR_API_KEY>
      
   Replace <YOUR_API_KEY> with the API key you created in the previous section. Save and close the file by pressing Ctrl + X, then Y, and then Enter. Type the following command to apply the changes:
         
         source ~/.bashrc
         
   B. **Windows**
   Right-click on the "Start" button and select "System".
   
   Click on "Advanced system settings".
   
   Click on "Environment Variables".
   
   Under "User variables", click on "New".
   
   Enter "OPENAI_API_KEY" in the "Variable name" field.
   
   Enter your API key in the "Variable value" field.
   
   Click on "OK" to save the changes.
   
   
Speech2Speech installation
--------------------------
To install Speech2Speech, open your terminal and run the following command:

    pip install speech2speech

Launch Speech2Speech
------------------------------------
To launch Speech2Speech, follow these steps:

1. Make sure the microphone and speakers of your device are on.

2. Navigate to the directory where your Speech2Speech program is located 
using the cd command.

3. Type the following command in the terminal to launch Speech2Speech:


      streamlit run speech2speech.py

Workflow
----------
Here's a step-by-step guide on how to use Speech2Speech:

1. Click the "Record Audio" button to start recording.
2. Begin speaking or reading aloud. As long as it supports it, Chat-GPT can 
   automatically detect the 
   language you're speaking, so there's no need to specify it.
3. Click the "Stop Recording" button to end the recording.
4. Click the "Transcribe" button to convert your speech into text. The 
   transcription will appear on a green background after a few seconds.
5. Select your desired target language from the dropdown menu under "Target 
   Language".
6. Click the "Translate" button to translate the transcription into your 
   chosen target language. The translated text will appear on a blue 
   background after a few seconds.
7. Click the "Read Translation" button to listen to the translated text.
8. If you want to repeat the process with a new dictation, click the "Refresh 
   Page" button to reset the page.

What to do if you encounter issues
-------------------------------

If Chat-GPT gets stuck or you encounter any issues, simply click the "Refresh Page" button to reload the page with the default settings.