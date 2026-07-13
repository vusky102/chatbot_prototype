RAG Chatbot - Terminal Prototype
================================

This repository contains a terminal chatbot in main.py.

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

Create a file named .env in the same directory as main.py. This file contains private API keys and configuration settings for the LLM providers, vision engines, fallback client, and Text-to-Speech system.

Here is a schema of all supported environment variables:

Primary OpenAI-Compatible Client
--------------------------------
- OPENAI_API_KEY        : The API Key for your primary chat model (e.g. OpenAI or a proxy portal).
- OPENAI_API_BASEURL    : The base URL of the primary API endpoint (e.g., https://api.openai.com/v1).
- OPENAI_API_MODEL      : The model name to use for standard interaction (e.g., GPT-4o-mini).

Vision AI API Client (Used for PDF visual elements / image extraction)
---------------------------------------------------------------------
- GEMINI_API_KEY        : Google Gemini API Key (recommended backend for layout analysis).
- GEMINI_MODEL          : Model name for layout analysis (defaults to gemini-2.5-flash).

Fallback OpenRouter Client (Configured automatically if primary fails)
----------------------------------------------------------------------
- OPENROUTER_API_KEY    : OpenRouter API key for fallback operations.
- OPENROUTER_BASE_URL   : The OpenRouter endpoint (typically https://openrouter.ai/api/v1).
- OPENROUTER_API_MODEL  : The fallback model name (e.g. google/gemma-4-31b-it:free).

Text-To-Speech (TTS) Settings
-----------------------------
- TTS_ENABLED           : Set to true to enable voice output, or false to disable (default: false).
- TTS_AUTOPLAY          : Automatically plays the generated audio (default: true).
- TTS_DEFAULT_LANGUAGE  : Default fallback language (eng / vie).
- TTS_AUDIO_DIR         : Directory where generated MP3s are stored (default: generated_audio).
- TTS_VOICE_POSITION_ENG: 0-indexed ID of the English voice to use.
- TTS_VOICE_POSITION_VIE: 0-indexed ID of the Vietnamese voice to use.

Example Configuration:

OPENAI_API_KEY=sk-proj-yourRealOpenAiKeyHere
OPENAI_API_BASEURL=https://api.openai.com/v1
OPENAI_API_MODEL=gpt-4o-mini

GEMINI_API_KEY=AIzaSyYourRealGeminiKeyHere
GEMINI_MODEL=gemini-2.5-flash

OPENROUTER_API_KEY=sk-or-v1-yourRealOpenRouterKeyHere
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_MODEL=google/gemma-4-31b-it:free

TTS_ENABLED=true
TTS_AUTOPLAY=true
TTS_DEFAULT_LANGUAGE=eng
TTS_AUDIO_DIR=generated_audio
TTS_VOICE_POSITION_ENG=0
TTS_VOICE_POSITION_VIE=0

Important:
- Quotes and spaces around environment variables are automatically trimmed/stripped by the python-dotenv parsing utilities.
- Never commit or share your .env file containing real API keys; it is excluded in .gitignore.


5. Run the chatbot
------------------

macOS/Linux:

python3 main.py

Windows:

py main.py

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

After the assistant prints a text answer, main.py detects whether the answer
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
    Confirm that .env is in the same directory as main.py and contains
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
implemented in main.py.
