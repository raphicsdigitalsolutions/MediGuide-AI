# MediGuide AI demo script

Use fictional values only. Do not show `.env`, an API key, or real patient information in the recording.

## Suggested 2–3 minute walkthrough

1. **Opening (20 seconds):** Show the 3D API connection dialog. Use the configured app connection for the demo; do not reveal or record any API key. Then show the MediGuide hero and animated orb. Switch Day theme on and off in the sidebar to show both clinical palettes, then point out the educational disclaimer.
2. **Form (20 seconds):** Enter a fictional example from the assignment, such as age 25, runny nose and sore throat, duration 1–3 days, severity 2/10.
3. **Streaming (20–30 seconds):** Submit and let the plain-language guidance stream into the result area.
4. **Dashboard (30 seconds):** Show the urgency estimate, symptom summary, Possible conditions, Next steps, Ask a professional, and Warning signs tabs.
5. **Caching (20 seconds):** Keep Model cache on In-memory and submit the identical form again. Show the cached guidance label.
6. **Urdu (20 seconds):** Switch Answer language to Urdu and submit the same fictional example.
7. **SQLite (optional, 20 seconds):** Select SQLite and point out the sidebar storage notice. Use fictional details only because this cache stores prompts and replies locally.
8. **Close (5 seconds):** End on the medical disclaimer and remind viewers this is an educational prototype.

The connection dialog can also be previewed during a later session with **Connect or change API key** in the sidebar. A visitor-provided key is session-only; do not capture the key field in the recording.

## Recording on Windows

Use Snipping Tool screen recording or another recorder available on your computer. Capture the browser window only, keep the sidebar visible for the cache/language steps, and avoid recording the terminal after `.env` has been opened.

