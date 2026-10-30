# Submission guide

The course submission requires a GitHub repository and a short screen recording or live demo.

## Before submission

1. Install dependencies and run the app locally using the steps in the repository README.
2. Confirm that \`.env\` contains your local API key and is not committed.
3. Use fictional patient details only. Do not enter real names, contact details, or medical information.
4. Test the empty-symptom warning, a routine example, the emergency fallback, Urdu output, streaming, and repeated requests with caching enabled.
5. Review the GitHub file list to confirm that source files, \`requirements.txt\`, \`.env.example\`, and documentation are present.

## Streamlit deployment

For Streamlit Community Cloud, select this repository, branch \`main\`, and main file \`app.py\`. Add \`OPENAI_API_KEY\` (and optionally \`OPENAI_MODEL\`) in the app's Settings → Secrets. Never store credentials in the repository.

## Demo outline

1. Show the app name and the medical safety notice.
2. Enter a fictional example such as age 25, runny nose and sore throat, duration 1–3 days, severity 2/10.
3. Submit and show the live narrative streaming into the app.
4. Show the dashboard tabs: summary, possible conditions for education only, next steps, clinician questions, and warning signs.
5. Switch to Urdu and demonstrate an Urdu response.
6. Repeat an identical request with caching enabled and explain the in-memory/SQLite distinction.
7. Show the emergency phrase fallback using the assignment's chest-pain and breathing-difficulty example.

Keep the recording focused. Do not reveal the API key, terminal environment variables, private account details, or real patient data.
