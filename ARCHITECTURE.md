## AI Restaurant Recommendation Service – Architecture

This document describes the architecture for an **AI Restaurant Recommendation Service** that:
- Takes user preferences (price, place, rating, cuisine, etc.).
- Uses the **Zomato dataset from Hugging Face**: `https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation`.
- Calls a **Groq-hosted LLM** to generate clear, natural-language restaurant recommendations.
- Returns a structured JSON response suitable for API clients and a user-facing UI page.

---

## High-Level Concept

- **Input**: User preferences (structured filters + optional free-text, e.g., “date night, quiet, rooftop”).
- **Core Flow**:
  1. Validate and normalize preferences.
  2. Filter candidate restaurants from the Zomato dataset (by location, price, rating, cuisine).
  3. Optionally rank/sort candidates using heuristic or learned scoring.
  4. Send a compact set of candidate restaurants + user preferences to a **Groq LLM**.
  5. The Groq LLM produces a ranked explanation and reasons for top restaurants.
  6. Service returns both structured data (IDs, names, scores) and Groq LLM-generated text.
- **Output**: JSON with recommended restaurants, metadata, and human-readable explanation, consumed by an API and a UI page.

---

## Phased Architecture Overview

- **Phase 0**: Requirements & Data Understanding  
- **Phase 1**: Data Ingestion & Storage Layer  
- **Phase 2**: Core Backend & Filtering Logic  
- **Phase 3**: Groq LLM Orchestration & Prompting  
- **Phase 4**: Ranking, Evaluation & Feedback Loop  
- **Phase 5**: Interfaces (API & UI), Deployment & Observability  

Each phase builds on the previous ones and can be developed iteratively.

---

## Phase 0 – Requirements & Data Understanding

- **Objectives**
  - Understand the **Zomato dataset schema** (columns, missing values, encoding of price, rating, cuisines, locations).
  - Define the **user preference schema** (what fields/filters we support).
  - Decide on **non-functional requirements**: latency, throughput, cost constraints, and initial deployment strategy.

- **Key Artifacts**
  - **Data exploration notebook**: basic EDA on the Hugging Face dataset.
  - **Domain model**:
    - `Restaurant` (id, name, location, cuisines, price_range, rating, etc.).
    - `UserPreference` (location, max_distance_km, price_range, min_rating, cuisines, occasion, etc.).
  - **API contract draft**:
    - `POST /recommendations` request/response JSON schemas.

- **Testing**
  - After completing this phase, review all assumptions and validate that data schemas and API contracts are consistent and error-free before starting Phase 1.

---

## Phase 1 – Data Ingestion & Storage Layer

- **Objectives**
  - Pull the dataset from Hugging Face and load it into a **queryable store**.
  - Normalize and clean data for consistent querying and LLM context.

- **Components**
  - **Data Ingestion Job**
    - Reads dataset from Hugging Face (via `datasets` library or direct download).
    - Applies basic cleaning (trim strings, normalize categories, handle missing ratings).
    - Stores data into a persistent store.

  - **Storage Options (choose one)**
    - **Relational DB (recommended)**: e.g., PostgreSQL with a `restaurants` table.
    - Optionally add **pgvector** or another vector store later for semantic search.

- **Outputs**
  - Normalized `restaurants` table (or collection) with indexes that support:
    - Location-based queries (city, area).
    - Filter by price, rating, cuisine.
  - Data access layer interfaces, for example:
    - `RestaurantRepository.get_by_filters(preferences: UserPreference) -> List[Restaurant]`.

- **Testing**
  - After completing this phase, run ingestion and data-access unit tests, verify row counts and basic sample queries, and ensure there are no runtime errors before moving to Phase 2.

---

## Phase 2 – Core Backend & Filtering Logic

- **Objectives**
  - Implement a **backend service** that exposes an API and runs filtering logic before involving the Groq LLM.
  - Make recommendations **deterministic and reproducible** at the core data level.

- **Components**
  - **API Layer**
    - Backend framework (e.g., FastAPI, Express).
    - Endpoint: `POST /recommendations`
      - Request body: `UserPreference` JSON.
      - Response: structured recommendations plus Groq LLM explanation (Phase 3+).
    - Input validation and error handling.

  - **Preference Normalization Service**
    - Converts raw user input (strings, enums) to internal categories.
    - Maps “cheap / mid / expensive” to price buckets.
    - Standardizes location inputs (e.g., city names, zones).

  - **Filtering Engine**
    - Uses repository layer to fetch candidate restaurants by:
      - Location (city, area).
      - Price range.
      - Minimum rating.
      - Cuisine intersection with user preferences.
    - Applies heuristic scoring (optional), for example:
      - Score = \( w_1 \times rating + w_2 \times popularity - w_3 \times price\_penalty \).
    - Returns a bounded set of candidates (for example, top 50) for Groq LLM consumption.

- **Outputs**
  - A working **data-driven recommendation** endpoint (even without Groq LLM).
  - Reliable, testable filtering logic with unit tests.

- **Testing**
  - After completing this phase, run backend unit and integration tests on the core API (for example, `POST /recommendations` with sample inputs) to confirm correct behavior and no errors before enabling the Groq LLM layer in Phase 3.

---

## Phase 3 – Groq LLM Orchestration & Prompting

- **Objectives**
  - Integrate a **Groq-hosted LLM** to transform structured candidate data and user preferences into **natural, friendly explanations** and a refined ranking.
  - Ensure prompts are **robust, deterministic, and cost-aware** with Groq’s API.

- **Components**
  - **Groq LLM Client**
    - Adapter around the Groq LLM API.
    - Handles:
      - Groq API key and config from environment.
      - Model selection (for example, `llama3-70b` or similar, depending on availability).
      - Retries, timeouts, and rate limiting specific to Groq.
      - Observability (logging, latency, token usage, Groq request IDs).

  - **Prompt Builder**
    - Constructs system and user messages:
      - System: “You are a restaurant recommendation assistant that only recommends from the given list of restaurants.”
      - User: includes user preferences in plain language.
      - Context: includes summarized candidate restaurants (name, cuisine, rating, key attributes).
    - Ensures context size stays within Groq model limits:
      - Include only top N candidates and truncated descriptions.
      - Use a compact, tabular representation of candidates.

  - **LLM Orchestrator**
    - Input: `UserPreference`, `List[Restaurant]` candidates.
    - Builds prompt, calls the Groq LLM, parses response into:
      - Ranked list of restaurant IDs.
      - Explanation text (per restaurant and overall).
    - Validates the Groq LLM output:
      - Ensures restaurant IDs exist in candidate set.
      - Provides fallback behavior if parsing fails (for example, default ranking without LLM refinement).

  - **Safety & Guardrails**
    - Restrict Groq LLM to:
      - Only recommend from provided candidates.
      - Avoid fabricating new restaurants or details.
    - Prompt-level constraints (for example, “If you are unsure, say that you are unsure and defer to the data filters.”).

- **Outputs**
  - Enriched response format:
    - `recommendations`: list of `{restaurant_id, score, reason}`.
    - `summary`: overall explanation paragraph.
  - Clear separation between:
    - **Deterministic filtering logic**.
    - **Groq LLM-based narrative and reranking**.

- **Testing**
  - After completing this phase, run integration tests against the Groq LLM (or mocks/stubs where appropriate) to ensure prompt construction, response parsing, and fallbacks work without errors before proceeding to Phase 4.

---

## Phase 4 – Ranking, Evaluation & Feedback Loop

- **Objectives**
  - Improve recommendation quality via metrics, A/B testing of prompts, and user feedback.
  - Introduce optional **learning-based ranking** beyond simple heuristics.

- **Components**
  - **Scoring & Ranking Module**
    - Combines:
      - Heuristic score (rating, distance, price).
      - Groq LLM-indicated relevance (for example, implicit scores or ranking signals in the output).
    - Produces final ranking score per candidate.

  - **Evaluation & Metrics**
    - Log anonymized interactions:
      - User preferences.
      - Candidate set.
      - Final recommended list.
      - Optional “clicked” or “accepted” restaurant from user.
    - Metrics dashboard (for example, via Prometheus/Grafana or cloud monitoring):
      - Latency, error rate.
      - Token usage and Groq LLM cost.
      - Simple engagement metrics if UI exists.

  - **Feedback Loop (optional)**
    - Use feedback to:
      - Adjust heuristic weights.
      - Tune Groq prompts (for example, emphasize budget sensitivity).
      - Train a lightweight ranking model if and when needed.

- **Outputs**
  - Instrumented system with **measurable** recommendation performance.
  - Mechanisms to iteratively improve ranking and prompts.

- **Testing**
  - After completing this phase, verify that metrics, logging, and any ranking changes behave as expected using automated tests and small offline evaluation runs, ensuring no regressions or errors before Phase 5.

---

## Phase 5 – Interfaces (API & UI), Deployment & Observability

- **Objectives**
  - Provide clean interfaces (REST API and a user-facing UI page).
  - Deploy in a reproducible, observable way, with clear separation of concerns between backend and frontend.

- **Components**
  - **External Interfaces**
    - **REST API**
      - `POST /recommendations`: main endpoint used by the UI and external clients.
      - `GET /restaurants/{id}` (optional): fetch details for a specific restaurant.
    - **UI Page (Web Frontend)**
      - Single-page or simple multi-page web UI (for example, React, Next.js, or a lightweight vanilla JS page) that:
        - Collects user preferences (location, budget, cuisines, rating, free-text notes).
        - Submits a request to `POST /recommendations`.
        - Renders a list of recommended restaurants with:
          - Name, location, cuisine, price range, rating.
          - LLM-generated explanation (“why this place?”).
        - Allows basic filtering/sorting on the client side (for example, sort by rating or price).
      - UI communicates with backend via JSON over HTTPS.
      - Basic state management (for example, local component state or simple global store) to handle loading, errors, and results.

  - **Configuration & Secrets**
    - `.env` or secret manager for:
      - DB credentials.
      - Groq API keys and model configuration.
      - Feature flags (for example, enable/disable Groq LLM layer).

  - **Deployment**
    - Containerization with Docker.
    - Environments:
      - `dev`: with mock/small data subset and optional Groq test/stub mode.
      - `prod`: full dataset and real Groq LLM.
    - CI workflow:
      - Run tests and lint on push.
      - Build and publish image.
      - Deploy to chosen environment (for example, cloud service).

  - **Logging & Tracing**
    - Structured logs:
      - Request ID, user preference hash (not PII).
      - Candidate count, Groq LLM latency, outcome status.
    - Error monitoring (for example, Sentry).
    - Optional tracing (OpenTelemetry) for backend and, optionally, UI requests.

- **Outputs**
  - End-to-end solution:
    - Users interact via a **web UI page**.
    - UI calls the backend API.
    - Backend performs filtering, calls the **Groq LLM**, and returns structured recommendations.
  - Deployed and observable system ready for iterative improvement.

- **Testing**
  - After completing this phase, run full end-to-end tests (UI + API + Groq LLM), smoke tests in each environment, and automated regression tests to confirm there are no errors before each release.

