# AI-Assistant-Kira
Kira - A personal assistant powered with AI technology. Spoken user input is converted to text using Whisper. This text is fed to ChatGPT, and the response of that is converted to speech using a Google service. Kira is context-sensitive and takes the contents of the entire conversation into account when generating the next response.

## Usage
 - shift_r: Press and hold to record your prompt.
 - ctrl_r: Press while Kira is talking to interrupt her.
 
## Special Voice Commands
 - Quit: Say "quit" to exit the program.
 - Abort: Say "abort recording" anywhere in your recording to skip.

## Setup
 - OpenAI: Write your openAI API key to api_key.py
 - Google: Paste the content of your google credentials json file to google_credentials.json
 - create an pythion3.8 environment
 - install all the python requirements using `pip install -r requirements.txt`
