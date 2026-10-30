# MediGuide AI

An educational Streamlit prototype for the **AI-Powered Medical Symptom Assessment and Patient Guidance Assistant** assignment. It demonstrates LangChain prompts, `LLMChain`, ChatOpenAI, structured JSON parsing, streaming, switchable model caching, and a safety-focused dashboard. The interface offers day and night clinical palettes, layered glass-like panels, an animated 3D guidance orb, and a 3D API-connection dialog.

## Safety and privacy

This is a course prototype, not a medical device. It does not provide diagnosis or treatment. It must not be used to make care decisions. Every screen displays the medical disclaimer. The app asks users to contact local emergency services for urgent symptoms and uses a small keyword check to bypass the model for a few emergency phrases. That check is not exhaustive and cannot rule out an emergency.

For non-emergency submissions, the app sends the entered form information to the configured OpenAI API. Use only fictional demonstration data. Do not enter names, contact details, or real patient information. The SQLite cache stores model prompts and replies in a local database without encryption; keep caching off for sensitive information. `.env*` files and the local database are excluded from Git by `.gitignore`.

On a new Streamlit session, a connection dialog appears. The app owner can configure `OPENAI_API_KEY` in Streamlit Community Cloud's Secrets settings (or another host's secret manager); then visitors can use that app connection. A visitor may instead enter a personal key, which is held in that active Streamlit session's memory and sent through the app host to OpenAI. Only enter a personal key on a deployment you trust. Personal-key requests run with caching off. The dialog can also be dismissed without a key; emergency keyword guidance remains available, while regular model requests require a connection. The app never writes a visitor key to `.env`, a database, or GitHub.

## Features mapped to the assignment

- Patient age, gender, symptoms, duration, severity, conditions, medications, notes, and answer language.
- `ChatOpenAI`, `PromptTemplate`, `ChatPromptTemplate`, `SystemMessage`, `HumanMessage`, `AIMessage`, and a reusable `LLMChain`.
- Exact JSON fields with safe parsing and friendly handling of invalid output.
- A plain-language narrative streamed through `llm.stream()` and `st.write_stream()`, with a safety filter that withholds medication/product suggestions and specific temperature or dose values.
- Off, `InMemoryCache`, and `SQLiteCache` modes. Identical completed requests can also be replayed from the current Streamlit session for a visibly quicker second display.
- Results dashboard with urgency, possible conditions for education only, next steps, questions for a professional, and warning signs.
- English and Urdu answer language selection.
- A Day theme switch in the sidebar; Night mode uses the default dark clinical palette.

LangChain v1 moved legacy chains such as `LLMChain` to the `langchain-classic` package. This project uses that package because the assignment explicitly requires `LLMChain`.

## Requirements

- Python 3.10 or later. Python 3.11 or 3.12 is a practical choice for a course environment.
- An OpenAI API key for non-emergency requests.
- Internet access while installing packages and calling the configured model.

## Setup on Windows PowerShell

From this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

In `.env`, replace the placeholder with your own key:

```dotenv
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

Save `.env` locally, then run:

```powershell
streamlit run app.py
```

The browser opens the Streamlit app and shows the API connection dialog. For local `.env` configuration, choose **Continue with the app connection**. Or enter a personal key for the active session only. Use fictional details for a classroom demonstration. An empty symptom submission is stopped before an API call. A few recognized emergency phrases trigger a static emergency warning without waiting for the model.

## Deployment secrets

Do not upload `.env` to GitHub. In Streamlit Community Cloud, add `OPENAI_API_KEY` in the app's **Settings → Secrets** field; visitors can then use the app-configured connection from the opening dialog. Keep `.streamlit/secrets.toml` out of Git as well. See Streamlit's [Secrets management guide](https://docs.streamlit.io/develop/concepts/connections/secrets-management) and [Community Cloud secrets guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## Caching explanation

| Cache | Stored in | Survives app restart? | Notes |
|---|---|---:|---|
| Off | Nowhere in LangChain cache | No | Recommended when you do not need a cache. |
| In-memory | Running Python process | No | Fast, but model prompts and replies remain in process memory until it stops. |
| SQLite | `data/langchain_cache.db` | Yes | Model prompts and replies are stored locally in plaintext. Do not use with real patient information. |

LangChain's cache is registered with `set_llm_cache(...)`. The app also keeps completed results in the current Streamlit session when caching is enabled, so repeating the same form can reuse the already generated narrative without another API request. Use the sidebar button to clear the selected LangChain cache.

## Classroom demonstration

Use synthetic examples from the assignment: mild runny nose and sore throat; fever and cough; chest pain with shortness of breath; a repeated request with caching enabled; and an Urdu response. Show the empty-symptom warning without submitting patient information. The emergency phrase path is a demonstration safety fallback, not a clinical triage service.

## Submission files

- `app.py` — Streamlit UI and run entry point.
- `src/` — prompts, chain, cache, safety, configuration, and parsing logic.
- `requirements.txt` — dependencies.
- `.env.example` — placeholder configuration only.
- `docs/Medical_AI_Assignment.pdf` — original assignment brief.
- `docs/SUBMISSION_GUIDE.md` — repository and demo handoff steps.
- `docs/DEMO_SCRIPT.md` — a short walkthrough for the screen recording.

## References

- [LangChain v1 migration guide](https://docs.langchain.com/oss/python/migrate/langchain-v1/) — legacy chains moved to `langchain-classic`.
- [LangChain `SQLiteCache` reference](https://reference.langchain.com/python/langchain-community/cache/SQLiteCache).
- [LangChain `set_llm_cache` reference](https://reference.langchain.com/python/langchain-core/globals/set_llm_cache).
- [Streamlit `st.write_stream` reference](https://docs.streamlit.io/develop/api-reference/write-magic/st.write_stream).
- [Streamlit `st.dialog` reference](https://docs.streamlit.io/develop/api-reference/execution-flow/st.dialog).
- [NHS chest pain guidance](https://www.nhs.uk/symptoms/chest-pain/) — includes immediate help guidance for chest pain with shortness of breath.
- [London Ambulance Service emergency guidance](https://www.londonambulance.nhs.uk/our-services/emergency-care/calling-999/) — examples of life-threatening emergencies. The app avoids hard-coding a country-specific emergency number.

