# CLOUD DEPLOYMENT & OPERATION GUIDE
**Autonomous NSE Quantitative Research Engine**

---

## 1. Cloud Architecture Overview

* **GitHub Repository:** Version control, automated continuous testing (`.github/workflows/ci.yml`).
* **Render / Railway (Persistent Worker):** Runs `src/scheduler/autonomous_worker.py` 24/7 in the cloud without requiring your local PC or Antigravity to stay open.
* **Vercel / Render (Web Service):** Hosts the responsive web dashboard and FastAPI endpoints (`src/dashboard/api.py`), providing phone and desktop access anywhere.
* **Remote MCP Endpoints:** Both `nse-bhavcopy` and `cm-market` are hosted remotely at `https://mcp.nseindia.in`, allowing seamless HTTPS connectivity from any cloud container.

---

## 2. One-Click Deploy to Render

1. Push your repository to **GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Autonomous NSE Quant Engine"
   git remote add origin https://github.com/your-username/stcks_predictor.git
   git push -u origin main
   ```
2. Log into **[render.com](https://render.com)**.
3. Click **New +** -> **Blueprint**.
4. Select your `stcks_predictor` GitHub repository.
5. Render will automatically parse `deploy/render.yaml` and provision:
   * **`nse-quant-research-worker`**: Persistent background worker running research cycles every 24 hours.
   * **`nse-quant-dashboard`**: Web service providing your public HTTPS dashboard URL.

---

## 3. Alternative: Run via Docker Compose Locally or on a VPS

To run the entire engine with the web dashboard and persistent worker:
```bash
cd stcks_predictor
docker-compose -f deploy/docker-compose.yml up --build -d
```
* Dashboard will be live at: `http://localhost:8000`
* Research PDF report will auto-generate to: `reports/Autonomous_NSE_Quant_Research_Report.pdf`

---

## 4. Local Execution Commands

* **Run Research Discovery Cycle Once:**
  ```bash
  python run_research.py
  ```
* **Start Web Dashboard Locally:**
  ```bash
  uvicorn src.dashboard.api:app --reload --port 8000
  ```
* **Start Continuous Background Worker:**
  ```bash
  python src/scheduler/autonomous_worker.py
  ```
