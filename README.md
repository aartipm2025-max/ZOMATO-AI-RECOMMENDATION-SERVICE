<p align="center">
  <h1 align="center">🍽️ Zomato AI Restaurant Recommendation Service</h1>
  <p align="center">
    An end-to-end <strong>AI-powered restaurant recommendation engine</strong> built with FastAPI, Groq LLM, and the Zomato dataset from Hugging Face.
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/FastAPI-0.132-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Groq_LLM-llama3--70b-orange?logo=ai&logoColor=white" alt="Groq" />
    <img src="https://img.shields.io/badge/SQLite-DB-003B57?logo=sqlite&logoColor=white" alt="SQLite" />
    <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white" alt="Docker" />
  </p>
</p>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Smart Filtering** | Filter by location, price range, rating, and cuisines |
| 🤖 **AI Recommendations** | Groq LLM generates natural-language explanations for each pick |
| 📊 **Heuristic Scoring** | Deterministic scoring engine ranks restaurants before LLM processing |
| 🧹 **Data Deduplication** | Duplicate restaurants are automatically removed |
| 📈 **Event Logging** | Every recommendation request is logged for analytics |
| 🌐 **Web UI** | Beautiful, responsive dark-mode interface |
| 📚 **Auto-generated API Docs** | Swagger UI at `/docs` |
| 🐳 **Docker Support** | One-command containerized deployment |

---

## 🏗️ Architecture

The service is built in **5 phases**, each adding a layer of functionality:

```
┌──────────────────────────────────────────────────────────────┐
│                         Phase 5: UI                          │
│         Beautiful web frontend + end-to-end pipeline         │
├──────────────────────────────────────────────────────────────┤
│                   Phase 4: Ranking & Events                  │
│           Deduplication + analytics event logging            │
├──────────────────────────────────────────────────────────────┤
│                  Phase 3: Groq LLM Integration               │
│      Prompt engineering → Groq API → Parse structured JSON   │
├──────────────────────────────────────────────────────────────┤
│                Phase 2: Backend & Filtering Logic             │
│        FastAPI + preference normalization + scoring           │
├──────────────────────────────────────────────────────────────┤
│                  Phase 1: Data Ingestion                     │
│       Hugging Face dataset → clean → SQLite storage          │
└──────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
ZOMATO-AI-RECOMMENDATION-SERVICE/
├── src/
│   └── zomato_ai/
│       ├── __init__.py               # Package init, loads .env
│       ├── data/                     # Data utilities
│       ├── phase1/
│       │   └── ingestion.py          # HuggingFace → SQLite ingestion
│       ├── phase2/
│       │   ├── api.py                # FastAPI app with all endpoints
│       │   ├── models.py             # Pydantic models (UserPreference, Restaurant)
│       │   ├── filtering.py          # Heuristic filtering & scoring engine
│       │   └── repository.py         # Database access layer
│       ├── phase3/
│       │   ├── groq_client.py        # Groq SDK wrapper
│       │   ├── prompt_builder.py     # LLM prompt construction
│       │   ├── orchestrator.py       # Filter → Groq → response orchestration
│       │   ├── parsing.py            # Parse LLM JSON output
│       │   └── models.py             # LLM response models
│       ├── phase4/
│       │   ├── dedup.py              # Name+location deduplication
│       │   └── events.py             # Recommendation analytics logging
│       └── phase5/
│           ├── pipeline.py           # End-to-end pipeline: User → Filter → LLM → Response
│           ├── models.py             # Pipeline response models
│           ├── ui.py                 # Mounts the web UI at /
│           └── ui/
│               └── index.html        # Frontend web interface
├── tests/
│   ├── conftest.py
│   ├── phase1/                       # Ingestion tests
│   ├── phase2/                       # API & filtering tests
│   ├── phase3/                       # Prompt & parsing tests
│   ├── phase4/                       # Dedup & events tests
│   └── phase5/                       # Pipeline & UI tests
├── .env.example                      # Environment variables template
├── .gitignore
├── ARCHITECTURE.md                   # Detailed architecture document
├── Dockerfile                        # Container image definition
├── docker-compose.yml                # One-command local deployment
├── pytest.ini                        # Test configuration
├── requirements.txt                  # Python dependencies
└── zomato_restaurants.db             # SQLite database (auto-generated)
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** installed
- A **Groq API key** (get one free at [console.groq.com](https://console.groq.com))

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/ZOMATO-AI-RECOMMENDATION-SERVICE.git
cd ZOMATO-AI-RECOMMENDATION-SERVICE
```

### 2. Install Dependencies

**Windows:**
```bash
py -m pip install -r requirements.txt
```

**macOS / Linux:**
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Then edit `.env` and add your real Groq API key:

```env
GROQ_API_KEY=gsk_your_real_key_here
GROQ_MODEL=llama3-70b-8192
```

### 4. Ingest the Zomato Dataset (First Time Only)

```bash
# Windows
py -c "from zomato_ai.phase1.ingestion import ingest_huggingface_dataset; print(f'Ingested {ingest_huggingface_dataset()} restaurants')"

# macOS / Linux
python -c "from zomato_ai.phase1.ingestion import ingest_huggingface_dataset; print(f'Ingested {ingest_huggingface_dataset()} restaurants')"
```

> Make sure you're in the project root directory and `src/` is on your Python path (or set `PYTHONPATH=src`).

### 5. Start the Server

```bash
# Windows
py -m uvicorn zomato_ai.phase2.api:app --reload --app-dir src

# macOS / Linux
uvicorn zomato_ai.phase2.api:app --reload --app-dir src
```

### 6. Open in Browser

| URL | Description |
|-----|-------------|
| [http://localhost:8000](http://localhost:8000) | 🌐 **Web UI** — Interactive recommendation interface |
| [http://localhost:8000/docs](http://localhost:8000/docs) | 📚 **Swagger UI** — Auto-generated API documentation |

---

## 🔌 API Endpoints

### `POST /recommendations`
> **Phase 2** — Pure data filtering (no LLM)

```json
{
  "location": "BTM",
  "min_rating": 4.0,
  "max_price": 1000,
  "preferred_cuisines": ["North Indian", "Chinese"],
  "limit": 5
}
```

### `POST /recommendations/llm`
> **Phase 3** — Groq LLM-enhanced recommendations

Same request body as above. Returns AI-generated explanations for each restaurant.

### `POST /recommendations/pipeline`
> **Phase 5** — Full end-to-end pipeline (used by the web UI)

Same request body. Returns enriched restaurant data with LLM reasons.

---

## 🧪 Running Tests

```bash
# Windows
py -m pytest -v

# macOS / Linux
pytest -v
```

**Test coverage across all 5 phases:**

| Phase | Tests |
|-------|-------|
| Phase 1 | Data ingestion, schema creation, deduplication |
| Phase 2 | API endpoint filtering (location, cuisine, price, rating) |
| Phase 3 | Prompt construction, LLM response parsing |
| Phase 4 | Dedup logic, empty result handling |
| Phase 5 | UI serving, end-to-end pipeline |

---

## 🐳 Docker

### Build & Run

```bash
docker compose up --build
```

The service will be available at [http://localhost:8000](http://localhost:8000).

### Environment Variables

Pass your Groq API key via `.env` (Docker Compose automatically reads it) or as a flag:

```bash
docker run -e GROQ_API_KEY=gsk_your_key -p 8000:8000 zomato-ai-api
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.10+ |
| **Web Framework** | FastAPI |
| **App Server** | Uvicorn |
| **Database** | SQLite (via SQLAlchemy) |
| **AI / LLM** | Groq (Llama 3 70B) |
| **Dataset** | [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) |
| **Data Validation** | Pydantic |
| **Testing** | Pytest |
| **Containerization** | Docker |
| **Frontend** | Vanilla HTML/CSS/JS |

---

## 📄 License

This project is for educational and portfolio purposes.

---

<p align="center"><em>Built with ❤️ using FastAPI + Groq LLM</em></p>
