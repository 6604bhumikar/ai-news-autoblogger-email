# AI News Auto-Blogger & Email Automation

A Streamlit app that fetches the latest AI news with SerpAPI, uses Groq LLM through LangChain to generate a blog article and email newsletter, then sends the email through SMTP.

## Features

- Latest AI news search using SerpAPI Google News
- Groq LLM blog generation
- Editable blog post and email preview
- Live SMTP/Gmail email sending
- n8n workflow JSON included for automation architecture
- Streamlit Cloud ready secrets configuration

## Local Setup

```powershell
cd D:\ai-news-autoblogger-email
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
SERPAPI_API_KEY = "your_key_here"
GROQ_API_KEY = "your_key_here"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@gmail.com"
SMTP_PASSWORD = "your_gmail_app_password"
DEFAULT_RECIPIENT = "recipient@example.com"
```

For Gmail, use a Gmail app password rather than your normal account password.

Run the app:

```powershell
streamlit run app.py
```

## Streamlit Cloud Deployment

1. Push this folder to its own GitHub repository.
2. Open Streamlit Community Cloud.
3. Create a new app and select this repository.
4. Set the main file path to `app.py`.
5. Add all required secrets in Streamlit Cloud app secrets.
6. Deploy.

## n8n Workflow

The included `n8n_workflow.json` models the assignment workflow:

```text
Cron Trigger -> News API -> Filter AI News -> Groq Blog Generator -> Email Formatter -> Gmail/SMTP
```

Import the JSON into n8n and replace placeholder credentials with your own API keys and email account.
