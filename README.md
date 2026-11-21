# Cyber Threat Intelligence Platform

A Flask dashboard that collects cybersecurity news from RSS feeds, classifies articles by threat category/severity, highlights India-related items, and provides optional AI-assisted threat Q&A.

## Run in PyCharm (Windows)

1. Extract the ZIP file.
2. Open the **cyber-threat-intel** folder in PyCharm (`File → Open`).
3. Configure a Python 3.10–3.12 interpreter: `File → Settings → Project → Python Interpreter`.
4. Open PyCharm's Terminal and run:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Open `app.py` and click the green Run button, or run:

   ```powershell
   python app.py
   ```

6. Open http://127.0.0.1:5000 in your browser.

No MySQL installation or database password is needed. SQLite is used by default and the `cyber_threats.db` file is created automatically in the project folder.

## First use

The app does not scrape automatically on startup. This makes launching it quick and avoids startup failures when the network is unavailable. Use the **Scrape / Refresh** control in the dashboard to collect current articles. Internet access is required for RSS scraping. Articles are stored locally and duplicate URLs are ignored.

## Optional AI chat

The dashboard and threat feed work without an AI API key. To enable the AI chat, create your own CodeWords API key and set it as an environment variable before launching PyCharm:

```powershell
$env:CODEWORDS_API_KEY="your-own-api-key"
python app.py
```

Do not paste API keys into source files or commit them to Git. AI chat calls an external service and requires internet access.

## Optional settings

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_TYPE` | `sqlite` | Local database backend in this build |
| `DATABASE_URL` | `./cyber_threats.db` | SQLite file path |
| `CODEWORDS_API_KEY` | empty | Enables AI chat when set |
| `AUTO_SCRAPE_ON_STARTUP` | `false` | Set to `true` to scrape when the server starts |
| `SECRET_KEY` | development value | Set a private random value before deployment |

## Main features

- Threat feed with pagination
- Category and severity filters
- India-only and today's-threat filters
- Search across titles, descriptions and keywords
- Threat statistics
- RSS scraping from The Hacker News, Cybersecurity News, Krebs on Security and BleepingComputer
- Duplicate prevention by article URL
- Optional AI chat for a selected threat

## API endpoints

- `GET /` – dashboard
- `GET /api/threats` – paginated and filtered threats
- `GET /api/search?q=keyword` – search
- `GET /api/stats` – dashboard statistics
- `POST /api/scrape` – scrape configured RSS sources
- `POST /api/chat` – optional AI chat (`{"threat_id": 1, "question": "What is the impact?"}`)

## Troubleshooting

- **`ModuleNotFoundError`**: confirm PyCharm is using the project `.venv`, then run `pip install -r requirements.txt` in its Terminal.
- **Port 5000 already in use**: stop the other process using port 5000 before starting this app.
- **No articles appear**: use the scrape control and check your internet connection. RSS providers may occasionally be unavailable.
- **AI chat unavailable**: set `CODEWORDS_API_KEY`; the rest of the application does not depend on it.

## Project layout

```text
cyber-threat-intel/
├── app.py
├── config.py
├── database.py
├── scraper.py
├── requirements.txt
├── templates/index.html
└── static/
    ├── css/style.css
    └── js/main.js
```
