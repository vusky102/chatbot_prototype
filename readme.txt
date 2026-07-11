RAG Chatbot - Terminal Prototype
================================

This repository contains a terminal chatbot in test.py.

The chatbot:

- Uses an OpenAI-compatible Chat Completions API for text answers.
- Keeps conversation history for the current terminal session.
- Retrieves answers from a small in-memory company knowledge base.
- Prints the assistant response as text.
- Converts each assistant response to speech with local Hugging Face MMS TTS.
- Routes English audio to facebook/mms-tts-eng.
- Routes Vietnamese audio to facebook/mms-tts-vie.
- Autoplays generated audio on macOS with afplay.


Prerequisites
-------------

- Python 3.9 or newer
- pip
- macOS for automatic audio playback through afplay
- An API key for OpenAI or another OpenAI-compatible API
- The API base URL and model name supplied by your API provider
- Internet access the first time Hugging Face TTS models are downloaded

Note:

The MMS TTS models are licensed CC-BY-NC 4.0. Treat this prototype as
non-commercial unless you have separate permission for commercial use.


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

python3 -m pip install -r requirement.txt

Windows:

py -m pip install -r requirement.txt

Installed packages include the OpenAI client, python-dotenv, Transformers,
PyTorch, SciPy, Accelerate, and langdetect.


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
TTS_MODEL_ENG=facebook/mms-tts-eng
TTS_MODEL_VIE=facebook/mms-tts-vie

Example for the official OpenAI API:

OPENAI_API_KEY=replace_with_your_real_key
OPENAI_API_MODEL=gpt-4.1-mini
OPENAI_API_BASEURL=https://api.openai.com/v1

TTS_ENABLED=true
TTS_AUTOPLAY=true
TTS_DEFAULT_LANGUAGE=eng
TTS_AUDIO_DIR=generated_audio
TTS_MODEL_ENG=facebook/mms-tts-eng
TTS_MODEL_VIE=facebook/mms-tts-vie

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

- English responses use facebook/mms-tts-eng.
- Vietnamese responses use facebook/mms-tts-vie.
- Unknown or low-confidence language detection falls back to TTS_DEFAULT_LANGUAGE.

Models are loaded lazily. The first English answer downloads and loads the
English model. The first Vietnamese answer downloads and loads the Vietnamese
model. Later answers reuse the loaded model during the same process.

Generated WAV files are written to generated_audio/ with timestamped names.
On macOS, TTS_AUTOPLAY=true plays the WAV file automatically with afplay.
On other operating systems, the audio file is saved and its path is printed.

To temporarily disable audio:

TTS_ENABLED=false


Troubleshooting
---------------

ModuleNotFoundError: No module named 'openai'
    Activate the virtual environment and run:
    python3 -m pip install -r requirement.txt

ModuleNotFoundError: No module named 'transformers'
    Install the TTS dependencies:
    python3 -m pip install -r requirement.txt

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
    The app may need to download the Hugging Face model files. Confirm that the
    machine has internet access and that the model names in .env are correct.

No audio playback
    On macOS, confirm TTS_AUTOPLAY=true and that afplay is available. On
    Windows/Linux, this prototype saves the WAV file but does not autoplay it.

Wrong TTS language
    The assistant is instructed to answer in the same language as the user.
    Very short or mixed-language responses can still be ambiguous. Set
    TTS_DEFAULT_LANGUAGE=vie if Vietnamese should be the fallback.


Current Scope
-------------

This is the terminal prototype only. The planned Streamlit, PDF ingestion,
LangChain, Pinecone, and Azure VM features described in plan.md are not yet
implemented in test.py.
