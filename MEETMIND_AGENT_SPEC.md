# MEETMIND — AI CODING AGENT BUILD SPECIFICATION
> **Read this entire document before writing a single line of code.**
> This is your source of truth. Every architectural decision, model choice, file location, API contract, and build sequence is specified here. Follow it exactly. When you face an ambiguous decision not covered here, choose the option that is simpler, more debuggable, and closer to what is described.

---

## WHAT YOU ARE BUILDING

MeetMind is an AI-powered Google Meet bot that:
1. **Joins a Google Meet call** as a virtual participant (headless browser)
2. **Captures all spoken audio** in real time via a virtual audio device
3. **Transcribes speech** using OpenAI Whisper
4. **Identifies who is speaking** using speaker diarization (pyannote.audio)
5. **Classifies every sentence** using an ML pipeline (Perceptron → KNN → MLP — all three built and compared)
6. **Extracts tasks, decisions, deadlines** using BERT NER
7. **Summarises the meeting** using BART
8. **Generates a personalised Minutes of Meeting (MOM)** for every participant
9. **Emails each participant** their own personalised MOM immediately after the meeting ends
10. **Shows a live dashboard** during the meeting with rolling transcript + emerging action items

This is an **ML class project**. The academic requirement is to demonstrate a clear ML pipeline that uses classical models (Perceptron, SLP, KNN, MLP) through to modern deep learning (Transformers). The code must be clean enough that a professor can trace each concept through the codebase. Every ML model must be trained, evaluated, and compared — not just used as a black box.

---

## PROJECT CONSTRAINTS & RULES

These are non-negotiable. Do not deviate.

- **Language**: Python (backend + ML). JavaScript/React (frontend only).
- **No shortcuts on ML models**: You must implement AND compare Perceptron, KNN, and MLP for sentence classification. Do not skip any of these — the comparison is graded.
- **All models must be serialisable**: Every trained model must be saveable as `.pkl` or `.pt` so it can be loaded without retraining on every run.
- **CPU-compatible inference**: All models must have a CPU fallback. Do not assume GPU availability at demo time.
- **SQLite for demo scope**: Use SQLite for the session database. Do not introduce PostgreSQL unless explicitly told to.
- **No auth system**: There is no login, OAuth, or user accounts. The host just opens the dashboard URL and uses it directly. Keep it simple.
- **English only**: No multilingual support.
- **One active session at a time**: The system only needs to handle one Google Meet session concurrently for the demo.
- **Fail loudly**: Every component should log errors with enough context to debug. Do not silently swallow exceptions.

---

## REPOSITORY STRUCTURE

Create this exact directory layout. Every file goes where specified.

```
meetmind/
│
├── README.md                        # Setup + run instructions
├── requirements.txt                 # All Python dependencies
├── .env.example                     # Template for environment variables
├── docker-compose.yml               # Optional: Redis for Celery if used
│
├── bot/
│   ├── __init__.py
│   ├── meet_bot.py                  # Playwright bot that joins Google Meet
│   ├── audio_capture.py             # Virtual audio device → FFmpeg → PCM chunks
│   └── participant_scraper.py       # Scrapes display names from Meet participants panel
│
├── ml/
│   ├── __init__.py
│   ├── stt/
│   │   ├── __init__.py
│   │   └── transcriber.py           # Whisper STT wrapper
│   ├── diarization/
│   │   ├── __init__.py
│   │   └── diarizer.py              # pyannote.audio wrapper
│   ├── classifier/
│   │   ├── __init__.py
│   │   ├── features.py              # TF-IDF + handcrafted feature extraction
│   │   ├── perceptron_model.py      # Scikit-learn Perceptron (binary: action item Y/N)
│   │   ├── knn_model.py             # Scikit-learn KNN (5-class)
│   │   ├── mlp_model.py             # Scikit-learn MLPClassifier (5-class, PRIMARY)
│   │   ├── train.py                 # Training script for all three classifiers
│   │   └── evaluate.py              # Generates comparison metrics + plots
│   ├── ner/
│   │   ├── __init__.py
│   │   └── task_extractor.py        # BERT NER wrapper for assignee/deadline extraction
│   └── summariser/
│       ├── __init__.py
│       └── summariser.py            # BART abstractive summarisation wrapper
│
├── api/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point
│   ├── database.py                  # SQLite setup, session/ORM models
│   ├── schemas.py                   # Pydantic request/response models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── sessions.py              # Session CRUD endpoints
│   │   ├── audio.py                 # Audio chunk ingestion endpoint
│   │   ├── bot.py                   # Bot launch/stop endpoints
│   │   └── websocket.py             # WebSocket live transcript push
│   └── services/
│       ├── __init__.py
│       ├── pipeline_service.py      # Orchestrates the full ML pipeline per audio chunk
│       └── finalize_service.py      # Post-meeting: summarise, generate MOMs, send emails
│
├── mom/
│   ├── __init__.py
│   ├── generator.py                 # Builds global + personalised MOM HTML strings
│   └── mailer.py                    # SMTP email sender
│
├── dashboard/                       # React frontend
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── TranscriptPanel.jsx  # Live rolling transcript by speaker
│   │   │   ├── ActionItemsPanel.jsx # Live action items sidebar
│   │   │   ├── ParticipantMap.jsx   # Editable speaker → email mapping
│   │   │   └── MeetingControls.jsx  # Launch bot, stop, finalize buttons
│   │   └── hooks/
│   │       └── useWebSocket.js      # WebSocket connection hook
│   └── public/
│
├── data/
│   ├── ami_samples/                 # AMI corpus excerpts (place downloaded files here)
│   ├── labelled/
│   │   └── sentences.csv            # Hand-labelled sentences for training
│   └── synthetic/
│       └── synthetic_meeting.csv    # GPT-generated labelled meeting data
│
├── experiments/
│   └── experiments.ipynb            # Model comparison notebook (graded)
│
└── tests/
    ├── test_classifier.py
    ├── test_ner.py
    ├── test_pipeline.py
    └── test_mom.py
```

---

## PHASE-BY-PHASE BUILD SEQUENCE

Build in this exact order. Do not start Phase 2 until Phase 1 is fully working. Each phase has a clear "done when" checkpoint.

---

## PHASE 1 — ML Models & Training Pipeline

**Goal**: All ML models trained, serialised, and evaluated. No server, no bot. Just models that work.

### 1.1 — Dataset Preparation (`data/`)

The training data is sentences from meeting transcripts, each labelled with one of five classes:

| Label | Integer | Description |
|---|---|---|
| `action_item` | 0 | A task assigned to someone ("Raj, please send the report by Friday") |
| `decision` | 1 | A decision made ("We've decided to go with option B") |
| `topic` | 2 | A topic being introduced ("Let's talk about the Q3 budget") |
| `deadline_mention` | 3 | A deadline referenced ("This needs to be done by Monday") |
| `general` | 4 | Everything else |

**Data sources to use** (in order of preference):
1. **AMI Meeting Corpus** — download the `ES2002a` scenario subset. Extract sentences from the transcript XML files. Manually label a minimum of 300 sentences.
2. **Synthetic data** — create `data/synthetic/synthetic_meeting.csv` with at least 200 rows. Use realistic meeting language. Ensure class balance (aim for ~40 rows per class minimum).
3. **Combined** — merge both sources. Final dataset should have at least 500 rows.

**CSV format** (`data/labelled/sentences.csv`):
```csv
sentence,label,speaker,has_modal,has_name,is_imperative
"Priya, can you finish the slides by Wednesday?",action_item,SPEAKER_01,1,1,0
"We have decided to postpone the launch.",decision,SPEAKER_02,0,0,0
"Let me now move on to the marketing update.",topic,SPEAKER_01,0,0,0
"The deadline for this is next Thursday.",deadline_mention,SPEAKER_00,0,0,0
"That sounds good to me.",general,SPEAKER_02,0,0,0
```

### 1.2 — Feature Engineering (`ml/classifier/features.py`)

Every sentence is converted to a **517-dimensional feature vector** before being passed to any classifier.

```python
# features.py must expose:
def extract_features(sentences: list[str]) -> np.ndarray:
    """
    Input:  list of N sentences
    Output: np.ndarray of shape (N, 517)
    
    Feature breakdown:
    - dims 0–511:   TF-IDF vector (max_features=512, sublinear_tf=True, ngram_range=(1,2))
    - dim 512:      has_modal_verb  (will/shall/should/must/need to/going to) → 1 or 0
    - dim 513:      has_person_name (any token that is Title Case and not a sentence start) → 1 or 0
    - dim 514:      is_imperative   (sentence starts with a base-form verb) → 1 or 0
    - dim 515:      has_deadline    (contains date/time words: monday/tuesday/.../by/before/until/EOD/EOW) → 1 or 0
    - dim 516:      sentence_length_norm (len(sentence.split()) / 50.0, clipped to 1.0) → float
    """
```

**Important**: The TF-IDF vectoriser must be **fit on the training set only** and then saved alongside the models. When loading models at inference time, load the same vectoriser. Never refit on inference data.

```python
# Save/load contract:
import joblib
joblib.dump(tfidf_vectorizer, 'ml/classifier/models/tfidf_vectorizer.pkl')
joblib.dump(mlp_model, 'ml/classifier/models/mlp_classifier.pkl')
joblib.dump(knn_model, 'ml/classifier/models/knn_classifier.pkl')
joblib.dump(perceptron_model, 'ml/classifier/models/perceptron_classifier.pkl')
```

### 1.3 — Perceptron Model (`ml/classifier/perceptron_model.py`)

This is the **baseline binary classifier**. It answers one question: "Is this sentence an action item? Yes or No?"

```python
from sklearn.linear_model import Perceptron

class PerceptronClassifier:
    """
    Binary classifier: action_item (1) vs not_action_item (0)
    Architecture: Single-layer perceptron with hinge loss
    Purpose: Baseline. Demonstrates linear decision boundary limitations.
    """
    
    def __init__(self):
        self.model = Perceptron(
            max_iter=1000,
            tol=1e-3,
            random_state=42,
            class_weight='balanced'   # handle class imbalance
        )
    
    def train(self, X_train, y_train):
        # Convert to binary: 1 if action_item, 0 otherwise
        y_binary = (y_train == 0).astype(int)
        self.model.fit(X_train, y_binary)
    
    def predict(self, X):
        return self.model.predict(X)
    
    def evaluate(self, X_test, y_test):
        # Returns dict with accuracy, precision, recall, f1
        ...
```

### 1.4 — KNN Model (`ml/classifier/knn_model.py`)

5-class classifier. Uses cosine distance because TF-IDF vectors have high dimensionality.

```python
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import normalize

class KNNClassifier:
    """
    5-class classifier (all five label types)
    k=5, metric=cosine (normalise vectors first, then use euclidean which == cosine on unit vectors)
    Purpose: Instance-based learning demo. Slower than MLP. Shows curse of dimensionality.
    """
    
    def __init__(self, k=5):
        self.model = KNeighborsClassifier(
            n_neighbors=k,
            metric='cosine',
            algorithm='brute',   # required for cosine distance
            n_jobs=-1
        )
    
    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)
    
    def predict(self, X):
        return self.model.predict(X)
    
    def predict_proba(self, X):
        return self.model.predict_proba(X)
```

### 1.5 — MLP Model (`ml/classifier/mlp_model.py`) — PRIMARY CLASSIFIER

This is the model that actually runs in production. All live inference uses this model.

```python
from sklearn.neural_network import MLPClassifier

class MLPSentenceClassifier:
    """
    5-class sentence classifier. This is the PRIMARY production classifier.
    Architecture: 517 → Dense(256, relu) → Dense(128, relu) → Dense(5, softmax)
    Equivalent in sklearn: hidden_layer_sizes=(256, 128)
    
    Concepts demonstrated: backpropagation, gradient descent, ReLU activation,
    dropout (via early stopping), softmax output, cross-entropy loss.
    """
    
    def __init__(self):
        self.model = MLPClassifier(
            hidden_layer_sizes=(256, 128),
            activation='relu',
            solver='adam',
            alpha=0.001,              # L2 regularisation (dropout equivalent for sklearn)
            batch_size=32,
            learning_rate='adaptive',
            max_iter=500,
            early_stopping=True,
            validation_fraction=0.1,
            random_state=42,
            verbose=True
        )
    
    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)
    
    def predict(self, X) -> list[str]:
        # Returns label strings, not integers
        int_preds = self.model.predict(X)
        return [INT_TO_LABEL[i] for i in int_preds]
    
    def predict_proba(self, X) -> np.ndarray:
        return self.model.predict_proba(X)

LABEL_TO_INT = {'action_item': 0, 'decision': 1, 'topic': 2, 'deadline_mention': 3, 'general': 4}
INT_TO_LABEL = {v: k for k, v in LABEL_TO_INT.items()}
```

### 1.6 — Training Script (`ml/classifier/train.py`)

This script is run once to produce all serialised models. It must:

1. Load `data/labelled/sentences.csv`
2. Split 70/15/15 train/val/test with `random_state=42`
3. Fit TF-IDF on train set only
4. Extract 517-dim features for all splits
5. Train Perceptron, KNN, MLP
6. Save all models + vectoriser to `ml/classifier/models/`
7. Print per-model metrics to stdout

```bash
# Run with:
python -m ml.classifier.train
```

### 1.7 — Evaluation Script (`ml/classifier/evaluate.py`)

This script produces the outputs needed for `experiments.ipynb`. It must generate:

1. **Comparison table** printed to stdout: Perceptron vs KNN vs MLP — Accuracy, Macro F1, Precision, Recall
2. **Confusion matrix** saved as PNG for each model: `ml/classifier/plots/confusion_matrix_{model}.png`
3. **F1 comparison bar chart**: `ml/classifier/plots/f1_comparison.png`
4. **Learning curves** for MLP: `ml/classifier/plots/mlp_learning_curve.png`

Expected output (target, not guaranteed):
```
Model        Accuracy   Precision   Recall     F1 (Macro)
-----------  ---------  ----------  ---------  ----------
Perceptron   0.71       0.68        0.65       0.66
KNN (k=5)    0.76       0.74        0.72       0.73
MLP          0.84       0.83        0.81       0.82     ← PRIMARY
```

The F1 must show clear progression: Perceptron < KNN < MLP. If it does not, investigate class imbalance in the training data.

### 1.8 — BERT NER (`ml/ner/task_extractor.py`)

Uses HuggingFace's `dslim/bert-base-NER` (pre-trained, no fine-tuning needed for demo scope).

```python
from transformers import pipeline

class TaskExtractor:
    """
    Extracts: PERSON (assignee), DATE/TIME (deadline), TASK_VERB (action verb)
    from sentences classified as action_item or deadline_mention.
    
    Model: dslim/bert-base-NER (HuggingFace)
    This uses transfer learning — BERT pre-trained on BookCorpus/Wikipedia,
    fine-tuned on CoNLL-2003 NER dataset. No additional training needed.
    """
    
    def __init__(self):
        self.ner_pipeline = pipeline(
            "ner",
            model="dslim/bert-base-NER",
            aggregation_strategy="simple",
            device=-1  # CPU; set to 0 for GPU
        )
    
    def extract(self, sentence: str, speaker_name: str = None) -> dict:
        """
        Returns:
        {
            "assignee": "Priya",          # or None
            "assignee_email": None,        # filled in later by identity mapper
            "deadline": "Wednesday",       # or None
            "task_verb": "finish",         # or None
            "task_description": "...",     # full cleaned sentence
            "confidence": 0.91
        }
        
        Fallback logic (CRITICAL — implement this):
        1. If NER finds a PERSON entity → use as assignee
        2. Elif sentence starts with "I will / I'll / I can" → assignee = speaker_name
        3. Elif sentence contains "we should/we need to" → assignee = "Team"
        4. Else → assignee = None (unassigned)
        """
```

### 1.9 — BART Summariser (`ml/summariser/summariser.py`)

```python
from transformers import pipeline

class MeetingSummariser:
    """
    Generates a 3–5 sentence abstractive summary of the full meeting transcript.
    Model: sshleifer/distilbart-cnn-12-6 (lighter than bart-large-cnn, CPU-viable)
    
    Concept demonstrated: Seq2Seq, encoder-decoder attention, beam search decoding.
    """
    
    def __init__(self):
        self.summariser = pipeline(
            "summarization",
            model="sshleifer/distilbart-cnn-12-6",
            device=-1
        )
    
    def summarise(self, full_transcript: str) -> str:
        """
        full_transcript: concatenated string of all speaker-attributed sentences.
        e.g. "Priya: Let's start with the budget.\nRaj: The Q3 numbers look good..."
        
        If transcript > 900 tokens, chunk it with 100-token overlap and summarise each chunk,
        then summarise the chunk summaries (two-pass).
        
        Returns: 3–5 sentence summary string.
        """
```

---

## PHASE 2 — Audio Pipeline & Bot

**Goal**: The bot can join a real Google Meet, capture audio, and return a diarised + transcribed text stream.

### 2.1 — Google Meet Bot (`bot/meet_bot.py`)

The bot joins Google Meet using Playwright (Python). This is the trickiest part of the project.

```python
# Key implementation requirements:

# 1. Use playwright.async_api (async)
# 2. Launch with these args to avoid bot detection:
browser = await playwright.chromium.launch(
    headless=True,
    args=[
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-blink-features=AutomationControlled',
        '--use-fake-ui-for-media-stream',  # auto-approve mic/camera
        '--use-fake-device-for-media-stream',
        '--disable-web-security',
    ]
)

# 3. Set a real user-agent string (Chrome on Windows)
context = await browser.new_context(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
    permissions=["microphone", "camera"]
)

# 4. Navigate to the Meet URL
# 5. Fill in the "Your name" field with "MeetMind Bot"
# 6. Click "Ask to join" or "Join now"
# 7. Poll until joined (check for the meeting controls bar appearing)
# 8. Start audio capture subprocess
# 9. Periodically call participant_scraper to update name list
```

**Bot account**: The bot needs a real Google account to join Google Meet. Store credentials in `.env` as `GOOGLE_BOT_EMAIL` and `GOOGLE_BOT_PASSWORD`. Log in to Google before navigating to the Meet URL.

**Bot detection mitigation**:
- Use `playwright-stealth` Python package to mask automation signals
- Randomise join timing (sleep 2–5 seconds before clicking join)
- Set a realistic display name ("MeetMind Bot" not "BOT_USER_01")

### 2.2 — Audio Capture (`bot/audio_capture.py`)

On Linux, use PulseAudio virtual sink. On macOS, use BlackHole. Provide setup instructions in README.

```python
# Audio capture pipeline:
# 1. Create a virtual audio sink that the browser routes audio to
# 2. FFmpeg reads from that sink and outputs 16kHz mono PCM chunks
# 3. Each chunk is 5 seconds of audio = 5 * 16000 * 2 bytes = 160KB per chunk

import subprocess
import asyncio

class AudioCapture:
    def __init__(self, session_id: str, api_base_url: str):
        self.session_id = session_id
        self.api_base_url = api_base_url
    
    async def start(self):
        # FFmpeg command (Linux/PulseAudio):
        cmd = [
            'ffmpeg',
            '-f', 'pulse',
            '-i', 'virtual_sink.monitor',
            '-ar', '16000',         # 16kHz sample rate (Whisper requirement)
            '-ac', '1',             # mono
            '-f', 'segment',
            '-segment_time', '5',   # 5-second chunks
            '-segment_format', 'wav',
            'chunk_%03d.wav'
        ]
        # Watch for new chunk files and POST them to /api/sessions/{id}/audio
```

**Important**: Each audio chunk must be POSTed to the backend as a multipart form upload, not raw bytes. The backend processes it asynchronously so the bot doesn't have to wait.

### 2.3 — Participant Scraper (`bot/participant_scraper.py`)

```python
async def get_participants(page) -> list[dict]:
    """
    Scrapes the Google Meet participants panel to get display names.
    
    Returns:
    [
        {"display_name": "Aditya Kumar", "email_guess": "aditya.kumar@gmail.com"},
        {"display_name": "Priya Singh", "email_guess": None},
    ]
    
    Strategy:
    1. Click the "People" / participants icon in Meet
    2. Find all participant name elements (CSS selector varies by Meet version — use aria-label)
    3. If display name looks like an email address, extract it
    4. Otherwise return the name with email_guess=None (host fills in manually via dashboard)
    """
```

### 2.4 — Whisper STT (`ml/stt/transcriber.py`)

```python
import faster_whisper  # Use faster-whisper, not openai-whisper (much faster on CPU)

class WhisperTranscriber:
    """
    Model: faster-whisper medium (good balance of speed and accuracy on CPU)
    Falls back to 'small' if memory is constrained.
    
    Install: pip install faster-whisper
    """
    
    def __init__(self, model_size: str = "medium"):
        from faster_whisper import WhisperModel
        self.model = WhisperModel(
            model_size,
            device="cpu",          # change to "cuda" if GPU available
            compute_type="int8"    # quantised for CPU speed
        )
    
    def transcribe(self, audio_path: str) -> list[dict]:
        """
        Input:  path to a .wav file (16kHz mono PCM)
        Output: list of segments
        [
            {"start": 0.0, "end": 2.4, "text": "Let's talk about the budget.", "confidence": 0.93},
            ...
        ]
        """
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        return [
            {"start": seg.start, "end": seg.end, "text": seg.text.strip(), "confidence": seg.avg_logprob}
            for seg in segments
        ]
```

### 2.5 — Speaker Diarization (`ml/diarization/diarizer.py`)

```python
# Install: pip install pyannote.audio
# Requires HuggingFace token for model access (set HF_TOKEN in .env)

from pyannote.audio import Pipeline

class SpeakerDiarizer:
    """
    Assigns a speaker label to each transcript segment.
    
    Model: pyannote/speaker-diarization-3.1
    Internals (document these in experiments.ipynb):
    - ECAPA-TDNN neural speaker embedding model
    - Spectral clustering on cosine similarity matrix of embeddings
    - Silhouette score used for optimal number of speakers
    
    ML concept: Unsupervised clustering (connects to KNN/distance metric theme)
    """
    
    def __init__(self):
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=os.environ["HF_TOKEN"]
        )
    
    def diarize(self, audio_path: str) -> list[dict]:
        """
        Returns list of speaker-time segments:
        [
            {"speaker": "SPEAKER_00", "start": 0.0, "end": 3.2},
            {"speaker": "SPEAKER_01", "start": 3.5, "end": 7.1},
        ]
        """
    
    def align(self, transcript_segments: list[dict], diarization_segments: list[dict]) -> list[dict]:
        """
        Merges Whisper output with diarization output by matching time ranges.
        Returns:
        [
            {"speaker": "SPEAKER_00", "text": "Let's talk about the budget.", "start": 0.0, "end": 2.4},
        ]
        
        Matching rule: assign transcript segment to whichever speaker label has the
        most overlap with that segment's time range.
        """
```

---

## PHASE 3 — FastAPI Backend

**Goal**: A running API server that accepts audio chunks, runs the ML pipeline, stores results, and pushes live updates.

### 3.1 — Database Schema (`api/database.py`)

Use SQLAlchemy with SQLite. Create these tables:

```python
# Session — one row per Google Meet call
class Session(Base):
    __tablename__ = "sessions"
    id: str              # UUID, primary key
    meet_url: str
    status: str          # 'pending' | 'active' | 'processing' | 'complete' | 'error'
    created_at: datetime
    ended_at: datetime | None
    host_email: str

# Participant — one row per person in the meeting
class Participant(Base):
    __tablename__ = "participants"
    id: str              # UUID
    session_id: str      # FK → sessions.id
    display_name: str    # From Google Meet
    email: str | None    # Filled in by host or scraped
    speaker_label: str   # 'SPEAKER_00', 'SPEAKER_01', etc.

# TranscriptSegment — one row per sentence/utterance
class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    id: str              # UUID
    session_id: str      # FK → sessions.id
    speaker_label: str
    text: str
    start_time: float    # seconds from meeting start
    end_time: float
    label: str           # output of MLP: 'action_item' | 'decision' | 'topic' | 'deadline_mention' | 'general'
    label_confidence: float
    created_at: datetime

# ActionItem — one row per extracted task
class ActionItem(Base):
    __tablename__ = "action_items"
    id: str              # UUID
    session_id: str      # FK → sessions.id
    segment_id: str      # FK → transcript_segments.id
    assigned_to_name: str | None
    assigned_to_email: str | None
    assigned_by_name: str | None
    task_description: str
    deadline: str | None
    confidence: float
    created_at: datetime
```

### 3.2 — API Endpoints

Implement all of these in `api/routers/`. Every endpoint returns JSON.

```
POST   /api/sessions
       Body: { meet_url, host_email }
       Returns: { session_id, status: "pending" }

POST   /api/sessions/{session_id}/bot/launch
       Body: {}
       Action: starts the Playwright bot as a background subprocess
       Returns: { bot_status: "joining", meet_url }

POST   /api/sessions/{session_id}/bot/stop
       Action: gracefully stops the bot, triggers finalization
       Returns: { status: "processing" }

POST   /api/sessions/{session_id}/audio
       Body: multipart/form-data with audio_file (.wav)
       Action: runs full ML pipeline on this chunk asynchronously
               (STT → diarize → classify → NER → store → push to WebSocket)
       Returns: { accepted: true, chunk_id }

GET    /api/sessions/{session_id}/transcript
       Returns: [ { speaker_label, display_name, text, label, start_time }, ... ]

GET    /api/sessions/{session_id}/action_items
       Returns: [ { task_description, assigned_to_name, assigned_to_email, deadline, confidence }, ... ]

GET    /api/sessions/{session_id}/participants
       Returns: [ { display_name, email, speaker_label }, ... ]

PUT    /api/sessions/{session_id}/participants/{participant_id}
       Body: { email }
       Action: updates participant email and re-resolves action item assignments
       Returns: { updated: true }

POST   /api/sessions/{session_id}/finalize
       Action: runs BART summarisation, generates MOMs, sends emails
       Returns: { mom_generated: true, emails_sent: N }

GET    /api/sessions/{session_id}/mom
       Returns: { global_mom_html, personalised_moms: { "email@x.com": "html..." } }

WS     /ws/sessions/{session_id}
       Server pushes JSON messages on each new transcript segment:
       { type: "segment", data: { speaker_label, display_name, text, label } }
       { type: "action_item", data: { task_description, assigned_to_name, deadline } }
       { type: "finalized", data: { mom_url } }
```

### 3.3 — Pipeline Service (`api/services/pipeline_service.py`)

This is the core orchestrator. Called for every audio chunk.

```python
async def process_audio_chunk(session_id: str, audio_path: str, db: Session):
    """
    Full pipeline for one 5-second audio chunk:
    
    1. transcriber.transcribe(audio_path) → raw segments
    2. diarizer.diarize(audio_path) → speaker labels
    3. diarizer.align(transcript, diarization) → speaker-attributed segments
    4. For each segment:
        a. features = feature_extractor.extract([segment.text])
        b. label = mlp_classifier.predict(features)[0]
        c. confidence = mlp_classifier.predict_proba(features).max()
        d. Save TranscriptSegment to DB
        e. If label in ['action_item', 'deadline_mention']:
              task = task_extractor.extract(segment.text, speaker_name)
              resolve assignee against participants table
              Save ActionItem to DB
              push WebSocket message: { type: "action_item", data: task }
        f. push WebSocket message: { type: "segment", data: segment }
    
    IMPORTANT: Steps 1–3 are slow. Run them synchronously.
    Steps 4a–4f can be parallelised across segments using asyncio.gather.
    Total target latency for one chunk: < 8 seconds on CPU.
    """
```

### 3.4 — Finalize Service (`api/services/finalize_service.py`)

Called once when the meeting ends.

```python
async def finalize_session(session_id: str, db: Session):
    """
    1. Load all TranscriptSegments for this session
    2. Build full transcript string: "DisplayName: sentence\n..."
    3. Run summariser.summarise(full_transcript)
    4. Collect all ActionItems grouped by assigned_to_email
    5. Collect all decisions (segments with label='decision')
    6. Collect all topics (segments with label='topic')
    7. Call mom_generator.generate_global(summary, decisions, topics, all_action_items)
    8. For each participant with an email:
           mom_generator.generate_personalised(participant, summary, decisions, topics, their_action_items)
           mailer.send(participant.email, personalised_mom_html)
    9. Send global MOM to host_email
    10. Update session status to 'complete'
    """
```

---

## PHASE 4 — MOM Generator & Email

### 4.1 — MOM Generator (`mom/generator.py`)

The MOM is an HTML string. No external template engine needed — build it with Python f-strings.

**Global MOM structure** (exact sections, in this order):
1. Header with meeting title, date, duration, participant list
2. Executive Summary (BART output)
3. Key Topics Discussed (list of topic-labelled segments)
4. Decisions Made (list of decision-labelled segments with speaker attribution)
5. All Action Items (HTML table: Task | Assigned To | Assigned By | Deadline | Confidence)
6. Unresolved Items (action items where assigned_to is None)
7. Footer with "Generated by MeetMind"

**Personalised MOM structure** (exact sections, in this order):
1. "Hi [FirstName]," greeting
2. Meeting Summary (same BART output)
3. Key Decisions (same as global)
4. **YOUR Action Items** (only tasks where assigned_to_email == this participant's email)
   - Formatted as a clear task list with checkboxes (HTML `☐` character)
   - Deadline highlighted in red if deadline is within 48 hours
5. "Full meeting notes available at [dashboard link]"
6. Footer

```python
def generate_personalised(participant: dict, summary: str, decisions: list, topics: list, tasks: list) -> str:
    """
    participant: { display_name, email }
    tasks: list of ActionItem objects assigned to this participant only
    Returns: complete HTML string ready to send as email body
    """
```

### 4.2 — Mailer (`mom/mailer.py`)

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Mailer:
    """
    Sends personalised MOM emails via SMTP.
    Config from .env:
    - SMTP_HOST (e.g., smtp.gmail.com)
    - SMTP_PORT (587)
    - SMTP_USER
    - SMTP_PASSWORD
    - FROM_NAME = "MeetMind Bot"
    
    For demo: use Gmail SMTP with an App Password (not the real password).
    """
    
    def send(self, to_email: str, subject: str, html_body: str):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"MeetMind Bot <{os.environ['SMTP_USER']}>"
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html'))
        # Send via SMTP_SSL or STARTTLS
```

**Email subject line format**:
- Personalised: `[MeetMind] Your action items from today's meeting`
- Global (to host): `[MeetMind] Full MOM — [date] meeting`

---

## PHASE 5 — React Dashboard

**Goal**: A browser-based UI the host uses to launch the bot and watch the meeting unfold.

### 5.1 — Stack

```
React 18 + Vite
TailwindCSS (utility classes only)
No other UI component library needed
```

### 5.2 — Layout

```
┌─────────────────────────────────────────────────────────────┐
│  MeetMind                          [ Session: Active ⏱ 12:34]│
├──────────────────────┬──────────────────────────────────────┤
│                      │  Action Items                         │
│  Live Transcript     │  ┌────────────────────────────────┐  │
│                      │  │ 🔴 Priya: finish slides by Wed │  │
│  PRIYA:              │  │ 🔵 Raj: send budget report     │  │
│  Let's talk about    │  │ 🟡 Team: review Q3 numbers     │  │
│  the Q3 budget...    │  └────────────────────────────────┘  │
│                      │                                       │
│  RAJ:                │  Participants                         │
│  The numbers show    │  ┌────────────────────────────────┐  │
│  a 12% increase...   │  │ SPEAKER_00 → priya@co.com  ✏️  │  │
│                      │  │ SPEAKER_01 → raj@co.com    ✏️  │  │
│                      │  │ SPEAKER_02 → [email?]      ✏️  │  │
│                      │  └────────────────────────────────┘  │
├──────────────────────┴──────────────────────────────────────┤
│  [Enter Meet URL: _______________] [🚀 Launch Bot] [⏹ Stop] │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 — WebSocket Hook (`dashboard/src/hooks/useWebSocket.js`)

```javascript
export function useWebSocket(sessionId) {
    const [segments, setSegments] = useState([]);
    const [actionItems, setActionItems] = useState([]);
    
    useEffect(() => {
        if (!sessionId) return;
        const ws = new WebSocket(`ws://localhost:8000/ws/sessions/${sessionId}`);
        
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === 'segment') {
                setSegments(prev => [...prev, msg.data]);
            } else if (msg.type === 'action_item') {
                setActionItems(prev => [...prev, msg.data]);
            }
        };
        
        return () => ws.close();
    }, [sessionId]);
    
    return { segments, actionItems };
}
```

### 5.4 — Colour-Code Action Items by Assignee

Assign a consistent colour to each participant. When an action item appears in the sidebar, the left border colour matches the participant's colour. Use a fixed palette of 8 colours, assigned in order as new speakers appear.

---

## PHASE 6 — Experiments Notebook

`experiments/experiments.ipynb` is **graded separately**. It must contain:

1. **Introduction cell**: Explain the ML pipeline and the purpose of comparing models
2. **Data loading and EDA**: Class distribution, sentence length distribution, sample sentences per class
3. **Feature engineering**: Show TF-IDF vocabulary size, most informative features per class
4. **Perceptron training and evaluation**: Train, show decision boundary concept, confusion matrix
5. **KNN training and evaluation**: Train with k=3,5,7 — show effect of k, confusion matrix
6. **MLP training and evaluation**: Training loss curve, confusion matrix, per-class F1
7. **Model comparison**: Side-by-side bar chart of F1 scores — must show Perceptron < KNN < MLP
8. **Error analysis**: 10 misclassified examples and why they were hard
9. **NER demonstration**: 5 example sentences with extracted entities shown
10. **Summarisation demo**: One full test transcript → BART summary
11. **Curriculum mapping table**: Maps each ML concept to where it appears in the codebase

---

## ENVIRONMENT VARIABLES (`.env`)

```bash
# Google Bot Account
GOOGLE_BOT_EMAIL=meetmindbot@gmail.com
GOOGLE_BOT_PASSWORD=your_app_password

# HuggingFace (for pyannote.audio model access)
HF_TOKEN=hf_xxxxxxxxxxxxxxxx

# Email / SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=meetmindbot@gmail.com
SMTP_PASSWORD=your_smtp_app_password

# App
API_HOST=0.0.0.0
API_PORT=8000
DASHBOARD_URL=http://localhost:5173
DEBUG=true

# ML Models
WHISPER_MODEL_SIZE=medium
CLASSIFIER_MODEL_PATH=ml/classifier/models/mlp_classifier.pkl
TFIDF_VECTORIZER_PATH=ml/classifier/models/tfidf_vectorizer.pkl
```

---

## DEPENDENCIES (`requirements.txt`)

```txt
# API
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9
sqlalchemy==2.0.30
aiofiles==23.2.1
pydantic==2.7.1

# Bot
playwright==1.44.0
playwright-stealth==1.0.6

# Audio
ffmpeg-python==0.2.0

# ML — STT
faster-whisper==1.0.1

# ML — Diarization
pyannote.audio==3.1.1
torch>=2.0.0

# ML — Classifiers
scikit-learn==1.5.0
numpy==1.26.4
scipy==1.13.0
joblib==1.4.2

# ML — NLP
transformers==4.41.1
tokenizers==0.19.1

# Utilities
python-dotenv==1.0.1
httpx==0.27.0

# Experiments
jupyter==1.0.0
matplotlib==3.9.0
seaborn==0.13.2
pandas==2.2.2
```

---

## RUNNING THE PROJECT

### First-time setup

```bash
# 1. Clone and install
git clone ...
cd meetmind
pip install -r requirements.txt
playwright install chromium

# 2. Configure environment
cp .env.example .env
# Edit .env with your values

# 3. Train ML models (do this once)
python -m ml.classifier.train
# Verify: ml/classifier/models/ should now contain .pkl files

# 4. Start the API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 5. Start the dashboard
cd dashboard
npm install
npm run dev
# Dashboard: http://localhost:5173

# 6. (Optional) Run model evaluation
python -m ml.classifier.evaluate
```

### Running a demo meeting

1. Open `http://localhost:5173`
2. Enter the Google Meet URL and click Launch Bot
3. The bot joins the meeting — watch the transcript appear live
4. Conduct a 5–10 minute meeting, assigning tasks verbally
5. End the meeting — bot exits automatically
6. Within 90 seconds, check participant emails for personalised MOMs

---

## KNOWN HARD PROBLEMS & HOW TO SOLVE THEM

These are the parts most likely to break. Read these before starting.

### Problem 1: Google Meet bot gets rejected
Google Meet detects automation signals and shows "Can't join" or just hangs on the lobby.

**Solution**:
- Use `playwright-stealth` — it patches all the JS fingerprinting checks
- Log into Google first via Playwright (navigate to google.com/accounts, sign in, then go to Meet)
- Use `--use-fake-ui-for-media-stream` flag (bot appears to have camera/mic)
- Add randomised delays: `await page.wait_for_timeout(random.randint(2000, 4000))` before each click

### Problem 2: Audio and transcript are out of sync
The diarization runs on the same 5-second chunk as transcription but may give slightly different time ranges.

**Solution**:
- In `diarizer.align()`, use a threshold of 0.5 second overlap for matching, not exact equality
- Accumulate a 30-second rolling buffer for re-diarization to keep speaker labels consistent across chunks

### Problem 3: Action items assigned to the wrong person or nobody
The NER model may miss informal names or only output "he/she" pronouns.

**Solution**:
- After NER, run a simple name matcher: check if any participant's `display_name` (or first name) appears anywhere in the sentence
- Implement the three-rule fallback system in `task_extractor.py` (NER → speaker self-assignment → "Team")
- Log all unresolved cases to the dashboard so the host can manually reassign

### Problem 4: TF-IDF dimensionality mismatch at inference
If the vectoriser was fit on training data and a new word appears at inference time, it gets ignored (not an error). But if you accidentally refit the vectoriser at inference time, dimension counts may differ.

**Solution**:
- Save the vectoriser with `joblib.dump` immediately after fitting
- In `features.py`, have a `load_vectorizer()` function that checks if the `.pkl` exists — if yes, load it; if no, raise an error (do not silently refit)
- Write a test in `tests/test_classifier.py` that loads the vectoriser from disk and verifies output shape is (N, 517)

### Problem 5: Whisper too slow on CPU
`whisper-large` on CPU takes 20–40 seconds per 5-second chunk. Unacceptable.

**Solution**:
- Use `faster-whisper` with `compute_type="int8"` — this is 4–8x faster
- Use model size `medium` not `large`
- Process chunks concurrently: while chunk N is transcribing, the bot is already capturing chunk N+1

---

## ML CONCEPTS — QUICK REFERENCE FOR DOCUMENTATION

When writing docstrings, comments, or the experiments notebook, use these explanations exactly:

| Concept | Where Used | One-Line Explanation |
|---|---|---|
| Perceptron | `perceptron_model.py` | Linear classifier; learns a weighted sum of inputs with a threshold activation |
| SLP | Same as Perceptron | Single-layer perceptron — one layer of weights, no hidden representation |
| MLP | `mlp_model.py` | Multiple layers; hidden layers learn non-linear feature combinations via backpropagation |
| KNN | `knn_model.py` | Classifies by majority vote among k nearest training examples in feature space |
| TF-IDF | `features.py` | Weighs words by frequency in the sentence and rarity across all sentences |
| Backpropagation | MLP training | Gradient of loss propagated backward through layers to update weights |
| Softmax | MLP output | Converts raw output scores to a probability distribution over classes |
| Transfer Learning | BERT NER, BART | Use weights pre-trained on large data, adapt to the specific task |
| NER | `task_extractor.py` | Sequence labelling — tags each token as PERSON, DATE, ORG, or O (other) |
| BIO Tagging | Inside BERT NER | B-tag = beginning of entity, I-tag = inside entity, O = outside any entity |
| Spectral Clustering | pyannote internals | Groups speaker embeddings by eigendecomposition of the similarity matrix |
| Seq2Seq | BART summariser | Encoder reads full input, decoder generates output token by token |
| Beam Search | BART decoding | Keeps top-k candidate output sequences at each step to avoid greedy suboptima |

---

## FINAL CHECKLIST BEFORE SUBMISSION

Before you consider this project complete, verify every item:

- [ ] `python -m ml.classifier.train` runs without errors and saves `.pkl` files
- [ ] Perceptron F1 < KNN F1 < MLP F1 in the evaluation output
- [ ] MLP macro F1 >= 0.80 on test set
- [ ] Bot joins a Google Meet call and the host sees "MeetMind Bot" in the participants list
- [ ] Live transcript appears on dashboard within 8 seconds of speech
- [ ] Action items appear in the sidebar during the meeting
- [ ] Participant email mapping is editable from the dashboard
- [ ] `POST /api/sessions/{id}/finalize` completes in under 90 seconds
- [ ] Each participant receives an email containing only their assigned tasks
- [ ] Global MOM contains all 6 sections (summary, topics, decisions, all tasks, unresolved, metadata)
- [ ] `experiments.ipynb` runs top-to-bottom without errors
- [ ] All three model confusion matrices are saved as PNGs
- [ ] F1 comparison bar chart is saved as PNG
- [ ] All `.pkl` model files are in `ml/classifier/models/`
- [ ] `.env.example` is committed; `.env` is in `.gitignore`
- [ ] `README.md` contains setup and run instructions
- [ ] Tests in `tests/` pass: `pytest tests/`

---

*This document is the complete build specification for MeetMind. Every decision made here is final unless explicitly overridden by the project owner. Build in phase order, verify each checkpoint, and do not proceed to the next phase until the current one passes its checkpoint criteria.*
