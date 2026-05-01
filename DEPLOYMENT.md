# Deployment Notes

This project is Streamlit Cloud ready.

## Build

Streamlit Cloud installs dependencies from `requirements.txt` automatically.

## App Entry Point

```text
app.py
```

## Required Secrets

```toml
GROQ_API_KEY = "your_key_here"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@gmail.com"
SMTP_PASSWORD = "your_gmail_app_password"
DEFAULT_RECIPIENT = "recipient@example.com"
```

## Local Command

```powershell
streamlit run app.py
```
