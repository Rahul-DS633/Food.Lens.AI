# FoodLens AI — Deployment Guide 🚀

This guide explains how to deploy **FoodLens AI** to the cloud so anyone can access it via a public URL.

---

## Architecture Overview
FoodLens AI has two deployment components:
1. **Streamlit Web UI (`app/Home.py`)**: The interactive multi-page frontend (Scanner, Results, Compare, Quests, Claims, Sugar Detector, Family Fit).
2. **FastAPI REST Backend (`api/main.py`)**: The programmatic API service.

---

## Method 1: Streamlit Community Cloud (Recommended — Free & 2 Minutes)
Streamlit Community Cloud is the easiest, zero-cost way to host the interactive web app directly from your GitHub repository.

### Step-by-Step Instructions:
1. **Visit Streamlit Community Cloud**:
   Go to [https://share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account (`Rahul-DS633`).

2. **Create New App**:
   - Click **"Create app"** or **"Deploy an app"**.
   - Choose **"I already have an app"**.

3. **Configure App Settings**:
   - **Repository**: `Rahul-DS633/Food.Lens.AI`
   - **Branch**: `main`
   - **Main file path**: `app/Home.py`
   - **App URL**: Choose a custom subdomain (e.g. `foodlens-ai.streamlit.app`) or leave default.

4. **Add Environment Secrets**:
   - Click **"Advanced settings..."** before deploying.
   - In the **Secrets** box (TOML format), enter your Gemini API key (optional, used for AI explanations):
     ```toml
     GEMINI_API_KEY = "your-actual-gemini-api-key"
     ```
   - Click **Save**.

5. **Deploy**:
   - Click **"Deploy!"**.
   - Streamlit Cloud will read `packages.txt` for OCR/barcode system libraries and `requirements.txt` for Python dependencies.
   - Your live app will be accessible at `https://<your-app-name>.streamlit.app`!

---

## Method 2: Render.com (Free Web Services)
Render offers free cloud hosting for both web apps and Docker containers.

### Deploying Streamlit UI:
1. Create a free account at [render.com](https://render.com).
2. Click **"New +"** -> **"Web Service"**.
3. Connect your GitHub repository: `Rahul-DS633/Food.Lens.AI`.
4. Configure:
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app/Home.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
5. Under **Environment Variables**, add:
   - `GEMINI_API_KEY` = `your-api-key`
6. Click **"Create Web Service"**.

### Deploying FastAPI Backend:
1. Repeat the steps above for a second Web Service.
2. Set **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
3. Click **"Create Web Service"**.

---

## Method 3: Hugging Face Spaces (Free Streamlit Hosting)
1. Go to [huggingface.co/spaces](https://huggingface.co/spaces).
2. Click **"Create new Space"**.
3. Choose:
   - **Space SDK**: `Streamlit`
   - **License**: `MIT` or `Apache 2.0`
4. Connect or duplicate your GitHub repository `Rahul-DS633/Food.Lens.AI`.
5. Under Settings -> **Variables and secrets**, add `GEMINI_API_KEY`.
6. Set the entrypoint to `app/Home.py`.

---

## Method 4: Docker & Docker Compose (VPS / AWS / GCP / DigitalOcean)
For self-hosting on any Ubuntu/Debian server or cloud VM:

### 1. Clone & Setup
```bash
git clone https://github.com/Rahul-DS633/Food.Lens.AI.git
cd Food.Lens.AI
cp .env.example .env
# Edit .env and paste your GEMINI_API_KEY
nano .env
```

### 2. Build & Run with Docker Compose
```bash
docker compose up -d --build
```
This automatically starts:
- **Streamlit UI** on `http://<your-server-ip>:8501`
- **FastAPI Backend** on `http://<your-server-ip>:8000`
- Persistent SQLite database volume stored in `data/`

### 3. Running a Single Container (Streamlit Only)
```bash
docker build -t foodlens-ai .
docker run -d -p 8501:8501 -e APP_MODE=streamlit -e GEMINI_API_KEY="your-key" foodlens-ai
```

---

## Environment Variables Reference
| Variable | Required | Description | Default |
| :--- | :---: | :--- | :--- |
| `GEMINI_API_KEY` | Optional | Google Gemini API key for grounded nutritional AI explanations | None |
| `APP_MODE` | Optional (Docker) | `streamlit`, `api`, or `both` | `streamlit` |
| `PORT` | Auto (Cloud) | Port assigned by hosting provider (Render, Railway, etc.) | `8501` / `8000` |
