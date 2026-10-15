# JobPilot – free personal job-hunt copilot

Finds jobs from free public job APIs, scores them against your resume,
tracks every application, writes cover letters, and auto-fills
Greenhouse / Lever application forms (you review and press Submit).

## What it does
- **Find jobs** from Remotive, Arbeitnow and any company on Greenhouse or Lever (public APIs, no scraping)
- **Match score** (0–100) from the skills in your resume vs. the job, with a penalty for senior roles
- **Skill gap**: "You have" vs. "They want" for every job
- **Tracker**: new → applied → interview / skipped / rejected, with the date you applied
- **Cover letters**: Gemini AI if you add a free key, otherwise a clean template
- **Auto-fill** (on your own computer): opens the form, fills your details and resume, you press Submit

## Run on your computer
```bash
pip install -r requirements-local.txt
playwright install chromium
streamlit run app.py
```
1. Put your resume as `resume.pdf` in this folder (or upload it from the dashboard).
2. Edit `config.yaml` (keywords, locations, company boards).
3. Optional: `set PROFILE_PHONE=your_number` (used in cover letters and forms)
   and `set GEMINI_API_KEY=your_key` (free from aistudio.google.com) for AI cover letters.

Terminal commands:
```bash
python main.py fetch          # find + score jobs
python main.py list           # top new matches
python main.py apply <job_id> # auto-fill the form
```

## Run online (Streamlit Community Cloud, free)
The online dashboard does everything except auto-fill, which needs a real browser on your computer.

1. Deploy this repo on [share.streamlit.io](https://share.streamlit.io) with `app.py` as the main file.
2. In **App settings → Secrets**, paste the keys from `.streamlit/secrets.toml.example`:
   - `APP_PASSWORD` – locks the dashboard so only you can use it
   - `DATABASE_URL` – a free Neon Postgres URL, so your tracker survives app restarts
   - `PROFILE_PHONE`, optional `GEMINI_API_KEY`
3. Open the app, upload your resume, press **Find new jobs**.

To use auto-fill on jobs found online, run the app locally with the same `DATABASE_URL`.

## Adding companies
Any company whose careers page is `boards.greenhouse.io/<slug>` or
`jobs.lever.co/<slug>` can be added to `config.yaml` using that slug.

## Privacy
Your phone number, resume, password and database URL never go into this repo:
they live in environment variables / Streamlit secrets (see `.gitignore`).
