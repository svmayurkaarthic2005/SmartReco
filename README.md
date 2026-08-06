# SmartReco — Behavioral AI Recommendation Agent & Learning Hub

> **Built for the Krish Naik Academy SmartReco Build Challenge 2026**  
> *Powered by **Mesh API** (Mandatory LLM Gateway) and **LangGraph Multi-Agent Architecture***

---

## 🏆 Hackathon Overview

**SmartReco** is an intelligent e-learning recommendation platform built for the **SmartReco Build Challenge 2026**. It continuously observes user behavioral telemetry (page views, course enrollments, category browsing, search queries, lesson completions, un-enrollments, scroll depth, and dynamic dwell time), understands user intent via a 7-agent reasoning pipeline, retrieves catalog-grounded courses via vector RAG, and generates persuasive personalized learning roadmaps.

---

## 🎯 System Architecture & Design

> 📖 **Detailed Specifications**: For deep-dive technical specs on each of our 7 AI micro-agents and pipeline subsystems, read the complete **[Engine & Agent Architecture Guide](docs/ARCHITECTURE.md)**.

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                   SmartReco Monorepo                                      │
├─────────────────────────────────────────────┬─────────────────────────────────────────────┤
│                 Frontend                    │                   Backend                   │
│          (React 18 + Vite + TS)             │              (FastAPI + Python)            │
│  ┌───────────────────────────────────────┐  │  ┌───────────────────────────────────────┐  │
│  │ Learner Dashboard │ Activity Stream   │  │  │ API Layer (Auth, Events, Recs, Catalog)│  │
│  │ Course Catalog    │ AI Recommendations│  │  │ LangGraph Multi-Agent Workflow Engine │  │
│  │ Course Detail Hub │ My Courses        │  │  └───────────────────┬───────────────────┘  │
│  └───────────────────┬───────────────────┘  │                      │                      │
└──────────────────────┼──────────────────────┴──────────────────────┼──────────────────────┘
                       │ HTTP / REST API (JWT Bearer Auth)           │
                       ▼                                             ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Services & Data Layer                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │    PostgreSQL    │  │     Redis        │  │     ChromaDB     │  │     Mesh API     │  │
│  │(Users, Products, │  │(Cache, Lock,     │  │ (Vector Store &  │  │ (LLM Narrative   │  │
│  │ Events, Recs)    │  │ Persona Keys)    │  │ Similarity Search│  │    Generation)   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 LangGraph Multi-Agent AI Pipeline (7 Specialized Agents)

SmartReco orchestrates 7 specialized AI agents in an explicit state graph ([workflow.py](file:///c:/proj/SmartReco/smartreco/backend/app/langgraph/workflow.py)) to analyze intent, calculate multi-factor progression scores, and generate learning roadmaps:

```mermaid
graph TD
    A["User Behavioral Events (Clicks, Views, Enroll, Unenroll)"] --> B["BehaviorAgent (Aggregation & Decay)"]
    B --> C["PersonaAgent (Clustering)"]
    B --> D["RecoveryAgent (Risk Check)"]
    B --> E["RetrievalPlanner (Semantic Query)"]
    E --> F["VectorRetrievalAgent (ChromaDB + Embeddings)"]
    F --> G["RankingAgent (6-Factor Scoring)"]
    G --> H["NarrativeAgent (Mesh API LLM)"]
    H --> I["Personalized AI Learning Recommendations UI"]
```

1. **`BehaviorAgent`**: Ingests user telemetry events, computes recency-weighted category intent, applies instant un-enrollment category wipes, and tracks progression.
2. **`PersonaAgent`**: Classifies users into 6 behavioral personas (*Explorer, Focused Builder, Career Switcher, Overwhelmed Learner, Price Sensitive, Drop-Off Risk*).
3. **`RecoveryAgent`**: Detects churn signals, inactivity, and exit events to trigger engagement recovery mechanisms.
4. **`RetrievalPlanner`**: Formulates intent-focused vector search queries while excluding enrolled and explicitly dropped courses.
5. **`VectorRetrievalAgent`**: Executes semantic RAG searches via ChromaDB with SentenceTransformers (`all-MiniLM-L6-v2`) and PostgreSQL fallbacks.
6. **`RankingAgent`**: Re-ranks candidate courses using a 6-factor mathematical formula:
   $$\text{Final Score} = S_{\text{semantic}} \cdot 0.35 + S_{\text{difficulty}} \cdot 0.20 + S_{\text{progression}} \cdot 0.15 + S_{\text{price}} \cdot 0.10 + S_{\text{tags}} \cdot 0.10 + S_{\text{freshness}} \cdot 0.10 + \text{Boosts} - \text{Penalties}$$
7. **`NarrativeAgent`**: Uses OpenAI Mesh API (`gpt-4o`) to generate custom learning goals, match explanations, and structured 3-step learning roadmaps aligned with top recommendations.

---

## ⭐ Core Platform Features

- **Dynamic AI Recommendation Engine**: Updates recommendations live based on enrollments, module completions, views, and dropped courses.
- **Un-Enrollment Intent Reset**: Dropping a course instantly purges category dominance (`categories_explored = 0`) and applies a hard score clamp (`final_score = 0.0`) so un-enrolled tracks don't linger in recommendations.
- **Interactive Course Learning Hub**: 15 distinct technology tracks featuring full HD 1080p embeddable YouTube video lectures, downloadable source code, and lecture notes across all 4 module levels.
- **Real-Time Dwell Time & Route Telemetry**: Automatically measures exact dynamic dwell time on page visits (`RouteTracker`) and logs user navigation shifts to PostgreSQL.
- **Multi-Layer Cache & Lock Management**: Combines Redis in-memory key storage with PostgreSQL `recommendation_cache` and event-hash invalidation (`compute_event_hash`).

---

## 🌟 Implemented Bonus Features

| Bonus Feature | Implementation Details |
|---|---|
| ⭐ **Structured Agent Framework** | Built with **LangGraph** stateful execution graph ([workflow.py](file:///c:/proj/SmartReco/smartreco/backend/app/langgraph/workflow.py)) containing nodes for Behavior Analysis, Persona Classification, Recovery Check, Vector Retrieval, Multi-Factor Ranking, and Narrative Generation. |
| ⭐ **Scheduled Proactive Delivery** | Background **APScheduler** jobs ([scheduler.py](file:///c:/proj/SmartReco/smartreco/backend/app/scheduler/scheduler.py)) send scheduled email recommendation digests based on user activity. |
| ⭐ **Observability** | Integrated **LangSmith** end-to-end tracing ([langsmith_client.py](file:///c:/proj/SmartReco/smartreco/backend/app/observability/langsmith_client.py)) to monitor agent execution nodes, prompts, and latencies. |
| ⭐ **Retrieval Polish** | 6-factor mathematical re-ranking formula combining Semantic Vector Similarity, Difficulty Level Alignment, Learning Progression, Price/Budget Fit, Tag Overlap, Freshness, and Domain Category Boost. |

---

## 📚 Course Catalog (95+ Courses Across 15 Domains)

Pre-seeded dataset with 95+ comprehensive technology courses:
- **AI/ML & LLM Agents** — LangChain, LangGraph, Transformers, PyTorch, Autonomous Agents.
- **Fullstack Web Development** — React 18, Next.js 14 App Router, Node.js Microservices, GraphQL, WebSockets.
- **Android App Development** — Kotlin Syntax, Jetpack Compose UI, Room Database, Retrofit MVVM.
- **iOS App Development** — Swift 5, SwiftUI Declarative UI, CoreData, Xcode Cloud CI/CD.
- **Flutter & Cross-Platform** — Dart Essentials, Flutter Widgets, Provider State, Firebase.
- **React Native & Expo** — Mobile Component Styling, React Navigation, Play Store Deployment.
- **Tailwind CSS & Design Systems** — CSS Grid, Flexbox, Tailwind Tokens, Micro-Interactions.
- **Cyber Security & Ethical Hacking** — OWASP Top 10, Wireshark, Metasploit, Ghidra Reverse Engineering.
- **Blockchain & Web3** — Solidity, Smart Contracts, DeFi Protocols, Solana Rust Anchor.
- **System Design & Architecture** — High-Scale System Design, Microservices, Distributed Caching.
- **Data Engineering & Big Data** — Apache Spark, SQL Analytics, Snowflake, Airflow, Kafka Streaming.
- **Database Architecture** — PostgreSQL Query Tuning, MongoDB Document Store, Redis Caching.
- **Cloud Computing & DevOps** — AWS Solutions Architect, Docker, Kubernetes, Terraform.
- **Game Development** — C# Unity Engine, 2D/3D Physics, Unreal Engine 5 Environment.
- **UI/UX & Product Design** — Figma Prototyping, Wireframing, Motion Design, Accessibility.

---

## 💻 Local Setup & Execution Guide

### 1. Environment Configuration (`backend/.env`)
```env
# Database & Redis
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/smartreco
REDIS_URL=redis://localhost:6379/0

# Mesh API (Mandatory LLM Gateway)
MESH_API_KEY=your_mesh_api_key_here
MESH_API_BASE_URL=https://api.meshapi.ai/v1
MESH_MODEL=openai/gpt-4o

# LangSmith Observability (Optional)
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=smartreco-hackathon
```

### 2. Database & Supabase Setup
- **Local PostgreSQL**: Run `docker-compose up -d postgres redis`.
- **Supabase Cloud**: Copy and run the complete SQL script from **[`docs/supabase_schema.sql`](docs/supabase_schema.sql)** directly in your Supabase SQL Editor. This initializes all tables (`users`, `products`, `courses`, `events`, `recommendations`, `recommendation_cache`), enums, and indexes.

### 3. Backend Setup & Database Seeding
```bash
cd backend
pip install -r requirements.txt
python -m app.database.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup & Launch
```bash
cd frontend
npm install
npm run dev
```

---

## 🤖 GitHub Actions Automated Checks

This repository contains the official hackathon automated CI workflow:
- Workflow Path: `.github/workflows/smartreco-checks.yml`

To enable automated checks on GitHub:
1. Go to repository **Settings** ➔ **Secrets and variables** ➔ **Actions**.
2. Add secrets:
   - `MESH_API_KEY`: Your Mesh API Key (`rsk_...`).
   - `SUBMISSION_TOKEN`: Your hackathon submission token.
