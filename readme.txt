RAG Chatbot - Terminal Prototype
================================

This repository currently contains a simple terminal chatbot in test.py.
It uses an OpenAI-compatible Chat Completions API, keeps conversation history
for the current session, and retrieves information from a small in-memory
knowledge base.


Prerequisites
-------------

- Python 3.9 or newer
- pip
- An API key for OpenAI or another OpenAI-compatible API
- The API base URL and model name supplied by your API provider


1. Open a terminal in the project directory
--------------------------------------------

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


4. Create the local .env file
-----------------------------

Create a file named .env in the same directory as test.py:

OPENAI_API_KEY=your_api_key
OPENAI_API_MODEL=your_model_name
OPENAI_API_BASEURL=https://your-provider-api-base-url

Example for the official OpenAI API:

OPENAI_API_KEY=replace_with_your_real_key
OPENAI_API_MODEL=gpt-4.1-mini
OPENAI_API_BASEURL=https://api.openai.com/v1

If the team uses another OpenAI-compatible provider, use the model name and
base URL supplied by that provider.

Important:

- Do not add quotation marks unless they are part of the actual value.
- Do not add spaces around the equals sign.
- Never commit or share the .env file.
- The repository's .gitignore already excludes .env.


5. Run the chatbot
------------------

macOS/Linux:

python3 test.py

Windows:

py test.py

When the prompt "You:" appears, type a question and press Enter.

Example questions:

- How many annual leave days do employees receive?
- What should I do if my account is locked?
- What must a new employee complete?

Type exit or quit to stop the chatbot. Ctrl+C also exits.


Troubleshooting
---------------

ModuleNotFoundError: No module named 'openai'
    Activate the virtual environment and run:
    python3 -m pip install -r requirement.txt

Missing environment variables
    Confirm that .env is in the same directory as test.py and contains all
    three required keys exactly as shown above.

Authentication error
    Check OPENAI_API_KEY and confirm that it is valid for the configured API
    provider.

Model not found
    Check OPENAI_API_MODEL. Model names depend on the API provider and account
    permissions.

Connection or endpoint error
    Check OPENAI_API_BASEURL. For the official OpenAI API, use:
    https://api.openai.com/v1


Current Scope
-------------

This is the terminal prototype only. The planned Streamlit, PDF ingestion,
LangChain, Pinecone, and Azure VM features described in plan.md are not yet
implemented in test.py.
