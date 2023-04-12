# speech2speech

Purpose:
--------
- Vocal recognition of your speech followed by translation to a target 
language of your choice and finally read thay same translation with a good quality voice.

- As long as your speech is in one of the many languages that chat-gpt can 
transcribe, you do not have to indicate which is the source language you are using

Prerequisites: OpenAI Account Signup, API Key Creation, and Environment Variable Setup
-----------------------------------------------------------------------------
This README file provides a step-by-step guide on how to sign up for an OpenAI account, create an API key, and set up an environment variable to use the API in a Ubuntu, Mac, or Windows environment.

### 1. Signup and Create an OpenAI Account

Go to the [OpenAI website](https://platform.openai.com/account/api-keys) and click on the "Sign up" button in the top 
right corner.

Enter your name, email address, and password in the provided fields, and click on the "Sign up" button.

Once you have signed up, you will be directed to the OpenAI dashboard.

### 2. Create an OpenAI API Key

Click on Personal at the right upper corner and on the "View API Keys" tab in 
the OpenAI dashboard.

Click on the "Create new secret key" button.

Give your API key a name and select the type of API key you want to create (restricted or full).

Once you have created your API key, copy it to your clipboard. Make sure to keep your API key secure, as it provides access to powerful computing resources and data.

### 3. Create an Environment Variable to Load Your OpenAI API Key
#### 3.1. Ubuntu and Mac

Open your terminal.

Type the following command to open your shell profile file:

    nano ~/.bashrc

Scroll to the bottom of the file and add the following line:


    export OPENAI_API_KEY=YOUR_API_KEY

Replace YOUR_API_KEY with the API key you created in the previous section.

Save and close the file by pressing Ctrl + X, then Y, and then Enter.

Type the following command to apply the changes:

    source ~/.bashrc

#### 3.2. Windows
Right-click on the "Start" button and select "System".

Click on "Advanced system settings".

Click on "Environment Variables".

Under "User variables", click on "New".

Enter "OPENAI_API_KEY" in the "Variable name" field.

Enter your API key in the "Variable value" field.

Click on "OK" to save the changes.

And that's it! You now have an OpenAI account, an API key, and an environment variable set up to use the OpenAI API in your Ubuntu, Mac, or Windows environment.

Speech2Speech installation
--------------------------
    pip install speech2speech

Speech2Speech launch in the terminal
------------------------------------
### 1. Windows:

Open the Command Prompt by pressing Win + R and typing "cmd" in the Run dialog box.

Navigate to the directory where your Streamlit program is located using the cd command. For example, if your program is in C:\Users\username\Documents\MyStreamlitApp, you would type cd C:\Users\username\Documents\MyStreamlitApp.

Once you're in the correct directory, type 

    streamlit run speech2speech.py 

and press Enter to launch your Streamlit app.

### 2. Mac:

Open the Terminal app by navigating to Applications > Utilities > Terminal.

Navigate to the directory where your Streamlit program is located using the cd command. For example, if your program is in /Users/username/Documents/MyStreamlitApp, you would type cd /Users/username/Documents/MyStreamlitApp.

Once you're in the correct directory, type

    streamlit run speech2speech.py

and press Enter to launch your Streamlit app.

### 3. Ubuntu:

Open the terminal by pressing Ctrl + Alt + T.

Navigate to the directory where your Streamlit program is located using the cd command. For example, if your program is in /home/username/Documents/MyStreamlitApp, you would type cd /home/username/Documents/MyStreamlitApp.

Once you're in the correct directory, type 

    streamlit run speech2speech.py 
and press Enter to launch your Streamlit app.

These steps assume that you already have Streamlit installed on your system. If you haven't installed Streamlit yet, you can do so by running pip install streamlit in the terminal.




Workflow
---------
1. Make sure the microphone and speakers of your device are on.
2. Click the Record Audio button.
3. Start speaking or reading what you want to transcribe into text. You do 
   not need to tell Chat-GPT which language are you using, as long as it 
   supports it: Chat-GPT will identify automatically your language.
4. Once finished, click the Stop Recording button
5. To transcribe your speech into text, click the Transcribe button. After 
   a few seconds. The transcription will appear in text on a green background.
6. In the selectbox under Target Language, choose the target language in which 
   the translation will be made.
7. Now click the Translate button to translate the transcription. After a 
   few seconds, it will appear below this button in a blue background.
8. Now click the Read Translation button and the translation made above 
   will be read aloud
9. Before clicking again the Record Audio to repeat the procedure with a 
   different dictation of yours, click the Refresh Page button.

What to do if stuck
--------------------
There may be occasions in which Chat-GPT gets stuck. In that case, click 
the Refresh Page button to reload the page with the default settings
