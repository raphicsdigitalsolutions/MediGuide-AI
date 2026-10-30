# Submission guide

The assignment asks for a GitHub repository and a short screen recording or live demo. Submit the repository URL and the demo through the course's required channel.

## Before uploading to GitHub

1. Run the app locally with the steps in `README.md`.
2. Keep your real API key only in `.env`. Do not add `.env` to GitHub.
3. Use fictional patient details in the app and in the recording.
4. Leave `data/langchain_cache.db` out of the repository. `.gitignore` already excludes it.
5. Review the staged file list and ensure it contains `.env.example`, not `.env`.

For a hosted Streamlit demo, keep the key in the host's secret settings (`OPENAI_API_KEY`), not in the repository. The opening dialog then lets visitors use the app-configured key without seeing it. The alternative personal-key option sends that key through the app host and should only be used on a deployment the visitor trusts.

## Create and push a repository

Create a new repository in your GitHub account, then run these commands from the project folder. Replace the example URL with your own repository URL.

```powershell
git init
git add .
git status --short
git commit -m "Build MediGuide AI assignment prototype"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/Medical_AI_Assignment.git
git push -u origin main
```

Choose a public repository only if your course allows it; otherwise use a private repository and share access with the instructor. Never paste your API key into a commit, issue, chat, or screen recording.

## Demo outline

Show the safety notices, enter fictional symptoms, submit and show the live narrative stream and results dashboard. Demonstrate Urdu output, the empty-symptom warning, an emergency fallback phrase, and a repeated identical request with a cache enabled. Keep the recording short and avoid showing `.env`, API keys, account pages, or real patient information.

