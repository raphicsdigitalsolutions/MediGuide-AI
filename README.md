# MediGuide AI

**AI-Powered Medical Symptom Assessment and Patient Guidance Assistant**

MediGuide AI is an educational Streamlit prototype built for a LangChain programming assignment. It accepts basic, user-entered symptom information and uses an OpenAI chat model through LangChain to produce structured, cautious educational guidance.

> **Medical safety notice:** This project is an educational prototype only. It is not a medical device, does not provide a diagnosis or treatment, and must not replace a licensed healthcare professional or emergency services. Use fictional information for demonstrations. Seek emergency help immediately for urgent symptoms.

## Features

- Patient age, gender, multiple symptoms, duration, self-reported severity, conditions, medications, and notes.
- English and Urdu response-language selection.
- OpenAI \`ChatOpenAI\` integration through LangChain.
- Reusable \`PromptTemplate\`, \`ChatPromptTemplate\`, and \`LLMChain\`.
- Demonstration of \`SystemMessage\`, \`HumanMessage\`, and \`AIMessage\`.
- Required structured JSON schema with safe parsing and validation.
- Live narrative streaming through \`llm.stream()\` and \`st.write_stream()\`.
- Off, in-memory, and SQLite model-cache options, plus current-session result replay.
- Dashboard for summary, educational possibilities, urgency estimate, next steps, clinician questions, and warning signs.
- Prominent medical safety notices and a best-effort emergency phrase fallback.

## Project structure

\`\`\`text
MediGuide-AI/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── .python-version
├── .streamlit/
│   └── config.toml
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── prompts.py
│   ├── chains.py
│   ├── cache_manager.py
│   ├── safety.py
│   └── utils.py
└── docs/
    ├── DEMO_SCRIPT.md
    └── SUBMISSION_GUIDE.md
\`\`\`

## Local setup (Windows PowerShell)

Python 3.10+ is required. Python 3.12 is selected by \`.python-version\`.

\`\`\`powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
\`\`\`

Add your own OpenAI API key to the local \`.env\` file:

\`\`\`dotenv
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
\`\`\`

Run the application:

\`\`\`powershell
streamlit run app.py
\`\`\`

Do not commit \`.env\`, \`.venv/\`, Streamlit secrets, or local cache files. The \`.env.example\` file contains placeholder text only.

## Streamlit Community Cloud deployment

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, create an app from this repository.
3. Set the branch to \`main\` and the main file to \`app.py\`.
4. In the app's **Settings → Secrets**, add:

\`\`\`toml
OPENAI_API_KEY = "your-openai-api-key"
OPENAI_MODEL = "gpt-4o-mini"
\`\`\`

5. Deploy and test with fictional data.

The application reads \`OPENAI_API_KEY\` from Streamlit secrets first, then from a local \`.env\` file. Never place an API key in source code or GitHub.

## Caching explanation

| Mode | Storage | Survives process restart? | Notes |
|---|---|---:|---|
| Off | No LangChain model cache | No | Avoids storing model prompts/replies in a cache. |
| In-memory | RAM | No | Fast; cleared when the app process stops. |
| SQLite | Local \`data/langchain_cache.db\` file | Yes, while that file persists | Persists across restarts but stores prompts/replies without encryption. |

The application also replays an identical completed request from the active Streamlit session when caching is enabled. This avoids repeating the visible result-generation process in the same session.

**Privacy warning:** Do not use real patient data. SQLite caching stores prompts and model responses locally in plaintext. Hosted app filesystems may be temporary, so SQLite persistence should not be assumed on Streamlit Community Cloud.

## Testing checklist

- Mild example: runny nose and sore throat, short duration, low reported severity.
- Fever and cough with moderate reported severity.
- Chest pain with shortness of breath: verify the emergency fallback.
- Submit the same fictional request twice with caching enabled.
- Submit without selecting a symptom: the app should warn without calling the API.
- Change the answer language to Urdu.

The emergency phrase check is intentionally narrow and is **not** a validated triage system. It cannot detect every emergency or rule one out.

## LangChain compatibility note

The project uses \`langchain-classic\` for the assignment's required \`LLMChain\` API because legacy chains were moved out of the main LangChain package in the LangChain 1.x line.

## Demo recording

See [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) for a short walkthrough. Never record an API key or real personal/medical information.
