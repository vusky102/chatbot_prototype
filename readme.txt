RAG Chatbot - Terminal Prototype
================================

This repository contains a terminal chatbot in test.py.

The chatbot:

- Uses an OpenAI-compatible Chat Completions API for text answers.
- Keeps conversation history for the current terminal session.
- Retrieves answers from a small in-memory company knowledge base.
- Prints the assistant response as text.
- Converts each assistant response to speech with Microsoft Edge's online TTS
  service through the edge-tts Python package.
- Routes English and Vietnamese audio to configurable Microsoft neural voices.
- Autoplays generated audio on macOS with afplay.


Prerequisites
-------------

- Python 3.9 or newer
- pip
- macOS or Windows for automatic audio playback
- An API key for OpenAI or another OpenAI-compatible API
- The API base URL and model name supplied by your API provider
- Internet access whenever speech is generated with Edge TTS

Note:

The edge-tts package does not require a Microsoft API key or local model
downloads. It is an unofficial client for Microsoft Edge's online speech
service, so synthesis depends on that service and an active internet
connection.


1. Open a terminal in the project directory
-------------------------------------------

cd /path/to/chatbot_prototype


2. Create and activate a virtual environment
--------------------------------------------

macOS/Linux:

python3 -m venv .venv
source .venv/bin/activate

Windows PowerShell:

py -m venv .venv
.venv\Scripts\Activate.ps1


3. Install the dependencies
---------------------------

macOS/Linux:

python3 -m pip install -r requirements.txt

Windows:

py -m pip install -r requirements.txt

Installed packages include the OpenAI client, python-dotenv, edge-tts, and
langdetect.


4. Create the local .env file
-----------------------------

Create a file named .env in the same directory as test.py:

OPENAI_API_KEY=your_api_key
OPENAI_API_MODEL=your_model_name
OPENAI_API_BASEURL=https://your-provider-api-base-url

TTS_ENABLED=true
TTS_AUTOPLAY=true
TTS_DEFAULT_LANGUAGE=eng
TTS_AUDIO_DIR=generated_audio
TTS_VOICE_POSITION_ENG=0
TTS_VOICE_POSITION_VIE=0

Example for the official OpenAI API:

OPENAI_API_KEY=replace_with_your_real_key
OPENAI_API_MODEL=gpt-4.1-mini
OPENAI_API_BASEURL=https://api.openai.com/v1

TTS_ENABLED=true
TTS_AUTOPLAY=true
TTS_DEFAULT_LANGUAGE=eng
TTS_AUDIO_DIR=generated_audio
TTS_VOICE_POSITION_ENG=0
TTS_VOICE_POSITION_VIE=0

If the team uses another OpenAI-compatible provider, use the model name and
base URL supplied by that provider.

Important:

- Do not add quotation marks unless they are part of the actual value.
- Do not add spaces around the equals sign.
- Never commit or share the .env file.
- The repository's .gitignore excludes .env and generated_audio/.


5. Run the chatbot
------------------

macOS/Linux:

python3 test.py

Windows:

py test.py

When the prompt "You:" appears, type a question and press Enter.

Example English questions:

- How many annual leave days do employees receive?
- What should I do if my account is locked?
- What must a new employee complete?

Example Vietnamese questions:

- Nhan vien co bao nhieu ngay nghi phep moi nam?
- Nhân viên có bao nhiêu ngày nghỉ phép mỗi năm?
- Tôi nên làm gì nếu tài khoản bị khóa?

Type exit or quit to stop the chatbot. Ctrl+C also exits.


How TTS Works
-------------

After the assistant prints a text answer, test.py detects whether the answer
is English or Vietnamese.

- English responses use the voice selected by TTS_VOICE_POSITION_ENG.
- Vietnamese responses use the voice selected by TTS_VOICE_POSITION_VIE.
- Unknown or low-confidence language detection falls back to TTS_DEFAULT_LANGUAGE.

Voice positions are zero-based. Position 0 is the default female voice.

English voices:

0  en-US-AriaNeural          Female
1  en-US-JennyNeural         Female
2  en-US-GuyNeural           Male
3  en-US-ChristopherNeural   Male

Vietnamese voices:

0  vi-VN-HoaiMyNeural        Female
1  vi-VN-NamMinhNeural       Male

For example, select a male voice for each language with:

TTS_VOICE_POSITION_ENG=2
TTS_VOICE_POSITION_VIE=1

If a position is not an integer, is negative, or is outside the corresponding
list, the router prints a warning and uses position 0. The old TTS_MODEL_ENG
and TTS_MODEL_VIE settings are no longer used.

Edge TTS sends the text to Microsoft's online service for synthesis. Generated
MP3 files are written to generated_audio/ with timestamped names. On macOS,
TTS_AUTOPLAY=true plays the MP3 file automatically with afplay. On Windows,
the MP3 opens with the registered default application. On Linux, the file is
saved and its path is printed.

To temporarily disable audio:

TTS_ENABLED=false


Troubleshooting
---------------

ModuleNotFoundError: No module named 'openai'
    Activate the virtual environment and run:
    python3 -m pip install -r requirements.txt

ModuleNotFoundError: No module named 'edge_tts'
    Install the TTS dependencies:
    python3 -m pip install -r requirements.txt

Missing environment variables
    Confirm that .env is in the same directory as test.py and contains
    OPENAI_API_KEY, OPENAI_API_MODEL, and OPENAI_API_BASEURL.

Authentication error
    Check OPENAI_API_KEY and confirm that it is valid for the configured API
    provider.

Chat model not found
    Check OPENAI_API_MODEL. Model names depend on the API provider and account
    permissions.

Connection or endpoint error
    Check OPENAI_API_BASEURL. For the official OpenAI API, use:
    https://api.openai.com/v1

TTS warning during first audio response
    Edge TTS requires internet access for every audio response. Confirm that
    the machine can reach Microsoft's online speech service and try again.

TTS voice position warning
    Confirm TTS_VOICE_POSITION_ENG or TTS_VOICE_POSITION_VIE is a zero-based
    integer listed in the voice tables above. Invalid values fall back to 0.

No audio playback
    On macOS, confirm TTS_AUTOPLAY=true and that afplay is available. On
    Linux, this prototype saves the MP3 file but does not autoplay it. On
    Windows, confirm the system has an application associated with MP3 files.

Wrong TTS language
    The assistant is instructed to answer in the same language as the user.
    Very short or mixed-language responses can still be ambiguous. Set
    TTS_DEFAULT_LANGUAGE=vie if Vietnamese should be the fallback.


Current Scope
-------------

This is the terminal prototype only. The planned Streamlit, PDF ingestion,
LangChain, Pinecone, and Azure VM features described in plan.md are not yet
implemented in test.py.
