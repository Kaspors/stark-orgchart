# The Optimistic Weather App

A deliberately optimistic weather forecast app — because the most likely outcome is always the best one. Aggregates data from four weather models and picks the most favourable reading for each data point. Deployed via GitHub Pages.

**Live app:** https://kaspors.github.io/stark-orgchart/

---

## Features

- Fetches real forecasts from four Open-Meteo models (`best_match`, `ecmwf_ifs025`, `gfs_seamless`, `icon_seamless`)
- **Optimistic aggregation**: highest max temp, lowest precipitation probability, best sky condition across all models
- **Fix Weather**: locks the forecast to an activity-appropriate preset (skiing, barbecue, beach, festival, hiking, running) or a pleasant default
- **Customise Weather**: three-question AI chat that adjusts the forecast based on what you're planning — powered by OpenAI via a server-side proxy
- **Liability Disclaimer**: full legal coverage naming Kasper and Jan as non-responsible for wet socks and failed barbecues

---

## Setup

### Frontend only

The app is a static HTML file (`docs/index.html`) deployed to GitHub Pages. No build step needed. The weather data comes from [Open-Meteo](https://open-meteo.com/) — no API key required.

### Backend (required for "Customise Weather")

The AI personalisation feature calls OpenAI server-side so the API key is never exposed to the browser.

**1. Clone and install dependencies**

```bash
git clone https://github.com/kaspors/stark-orgchart.git
cd stark-orgchart
pip install -r requirements.txt
```

**2. Set environment variables**

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Edit `.env`:

```
OPENAI_API_KEY=your-openai-api-key-here
ADMIN_KEY=your-admin-key-here
```

`.env` is listed in `.gitignore` and will never be committed.

**3. Run the backend**

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

**4. Configure the frontend backend URL**

In `docs/index.html`, update the `BACKEND_URL` constant near the top of the `<script>` block to point to your deployed backend:

```js
const BACKEND_URL = 'https://your-backend-url.example.com';
```

For local development, the default `http://localhost:8000` works as-is.

> **Mobile use:** For "Customise Weather" to work on mobile, the backend must be publicly accessible (e.g. deployed to Railway, Fly.io, or a VPS). GitHub Pages can only serve the static frontend.

---

## Deployment

The `docs/` folder is automatically deployed to GitHub Pages via GitHub Actions on every push to `main`. See `.github/workflows/deploy-pages.yml`.

---

## Disclaimer

The Optimistic Weather App is not a legally binding meteorological instrument. Kasper and Jan accept no responsibility for rain, wet socks, ruined hair, failed barbecues, cancelled picnics, laundry left outside, or any other weather-adjacent inconvenience.
