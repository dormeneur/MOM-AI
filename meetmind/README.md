# MeetMind — AI-Powered Meeting Assistant

MeetMind is an AI agent that joins Google Meet calls, transcribes speech, classifies sentences, extracts action items using NER, and emails personalised Minutes of Meeting (MOM) to each participant.

---

## Quick Demo (No Google Meet needed)

### 1. Install dependencies

```bash
cd meetmind
python -m pip install -r requirements.txt
```

### 2. Train the ML models (one-time, ~30 seconds)

```bash
python -m ml.classifier.train
```

### 3. Run the demo

```bash
python -m demo
```

This feeds a **synthetic meeting transcript** through the full pipeline:
- **Feature Engineering** — TF-IDF + handcrafted features (517 dims)
- **Classification** — Perceptron vs KNN vs MLP comparison table
- **NER Extraction** — BERT-based task/assignee/deadline detection
- **Summarisation** — BART abstractive summary
- **MOM Generation** — HTML reports saved to `demo_output/`

Open `demo_output/mom_global.html` in your browser to see the generated MOM.

---

## Run the Full App (API + Dashboard)

### Terminal 1 — API Server

```bash
cd meetmind
python -m uvicorn api.main:app --reload --port 8001
```

### Terminal 2 — Dashboard

```bash
cd meetmind/dashboard
npm install
npm run dev
```

Open **http://localhost:5173** → click **🧪 Demo Mode** to see live data.

---

## Project Structure

```
meetmind/
├── ml/                  # ML classifiers, NER, STT, diarization, summariser
├── api/                 # FastAPI backend (CRUD, WebSocket, pipeline)
├── bot/                 # Google Meet bot (Playwright, audio capture)
├── mom/                 # MOM generator & email sender
├── dashboard/           # React frontend (Vite + Tailwind)
├── demo.py              # Standalone demo script
├── demo_output/         # Generated MOM HTML files
├── data/                # Training data
├── tests/               # Test suite (pytest)
└── requirements.txt     # Python dependencies
```

## ML Pipeline

| Model | Type | Task |
|---|---|---|
| Perceptron | Linear (binary) | Action item detection baseline |
| KNN (k=5) | Instance-based | 5-class sentence classification |
| **MLP** | **Neural network** | **5-class classifier (production)** |
| BERT NER | Transfer learning | Task/assignee/deadline extraction |
| BART | Seq2Seq | Abstractive summarisation |

**F1 Score: Perceptron < KNN < MLP** (verified in training)

## Run Tests

```bash
cd meetmind
python -m pytest tests/ -v
```
