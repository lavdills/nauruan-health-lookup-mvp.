# Nauruan Health Vocabulary Lookup & Validation MVP

This is a Streamlit deployment package for testing the Nauruan health vocabulary lookup prototype with native-speaker reviewers.

## Files

- `app.py` — Streamlit web application.
- `requirements.txt` — Python dependencies.
- `data/health_lookup_records.csv` — current vocabulary and phrase records.

## Local test

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Quick deployment: Streamlit Community Cloud

1. Create a GitHub repository, for example `nauruan-health-lookup-mvp`.
2. Upload `app.py`, `requirements.txt`, and the `data/` folder.
3. Sign into Streamlit Community Cloud.
4. Create a new app from the GitHub repository.
5. Set the app entrypoint to `app.py`.
6. Deploy and share the generated `.streamlit.app` URL with reviewers.

## Alternative deployment: Hugging Face Spaces

1. Create a new Hugging Face Space.
2. Choose Streamlit as the SDK.
3. Upload `app.py`, `requirements.txt`, and the `data/` folder.
4. The Space will build and provide a public URL.

## Validation workflow

This MVP does not use a persistent database. Review decisions are stored in browser session memory and must be exported as CSV before the reviewer closes or refreshes the page.

For proper multi-reviewer production use, connect the review form to Google Sheets, Supabase, Airtable, or another database.

## Safety note

This is a prototype. Do not use it for clinical care, consent, medication instructions, or safety-critical public communication until native-speaker and clinical validation is complete.
