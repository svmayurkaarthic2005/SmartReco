# SmartReco — Behavioral AI Recommendation Agent & Learning Hub

> **Built for the Krish Naik Academy SmartReco Build Challenge 2026**  
> *Powered by **Mesh API** (Mandatory LLM Gateway) and **LangGraph Multi-Agent Architecture***

---

## 🏆 Hackathon Overview

**SmartReco** is an intelligent e-learning recommendation platform built for the **SmartReco Build Challenge 2026**. It continuously observes user behavioral telemetry (page views, course enrollments, category browsing, search queries, video module watches, lesson completions, un-enrollments, scroll depth, and dynamic dwell time), understands user intent via a 7-agent reasoning pipeline, retrieves catalog-grounded courses via vector RAG, and generates persuasive personalized learning roadmaps.

---

## 🖼️ User Interface Preview

### 🖥️ Personalized AI Recommendation Hub
![SmartReco AI Recommendations UI](docs/images/frontend_recommendations_ui.png)
*Figure 1: SmartReco AI Recommendation Hub displaying real-time persona classification (`Career Switcher`), multi-domain skill progression narrative, 98% AI Match Confidence score, and structured learning path cards with direct lecture access.*

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
    A["User Behavioral Events (Clicks, Views, Enroll, Unenroll)"] --> B["BehaviorAgent (Telemetry & Intent Weights)"]
    B --> C["PersonaAgent (Clustering & Confidence)"]
    B --> D["RecoveryAgent (Risk Check)"]
    B --> E["RetrievalPlanner (Semantic Query Construction)"]
    E --> F["VectorRetrievalAgent (ChromaDB + Embeddings)"]
    F --> G["RankingAgent (Multi-Factor Scoring & Penalties)"]
    G --> H["NarrativeAgent (Mesh API LLM & Roadmap Generation)"]
    H --> I["Personalized AI Learning Recommendations UI"]
```

---

### 🔬 Agent Specifications & Exact Mathematical Formulas

#### 1. `BehaviorAgent` ([behavior_agent.py](file:///c:/proj/SmartReco/smartreco/backend/app/agents/behavior_agent.py))
Ingests user telemetry within a lookback window (default 72h) and calculates recency-weighted category intent scores.

* **Recency Weight Multiplier:**
  $$\text{recency\_weight} = 1.0 + \left(\frac{\text{idx} + 1}{\text{num\_events}}\right) \times 2.0 \quad (\text{Range: } 1.0\times \text{ to } 3.0\times)$$
* **Event Base Weights:**
  * `VIEW_PRODUCT` = **`3 pts`**
  * `ADD_TO_CART` / `WISHLIST` = **`5 pts`**
  * `LESSON_COMPLETE` / `MODULE_COMPLETE` = **`20 pts`** (increments category `completion_counts`)
  * `MODULE_WATCH` (watching tab video) = **`25 pts`** (increments category `completion_counts`)
  * `ENROLL` = **`50 pts`**
  * `RE_ENROLL` = **`60 pts`**
  * `UNENROLL` = Resets active intent points `summary.categories_explored[category] = 0`
* **Weighted Value Formula:**
  $$\text{weighted\_val} = \text{round}(\text{base\_weight} \times \text{recency\_weight})$$

#### 2. `PersonaAgent` ([persona_agent.py](file:///c:/proj/SmartReco/smartreco/backend/app/agents/persona_agent.py))
Classifies users into 6 personas (*Explorer, Focused Builder, Career Switcher, Overwhelmed Learner, Price Sensitive, Drop-Off Risk*):

* **Focused Builder Criteria:** Dominant category ratio $> 60\%$ (+2 pts) AND average dwell time $> 120\text{s}$ (+2 pts).
* **Confidence Range:** Calculated as $\text{confidence} = \min(0.95, \max(0.60, \text{base\_confidence} + \text{boost}))$, bounded between **60% and 95%**.
  * Total events $> 5$ or repeat visits $> 2$: **`+0.20 boost`**
  * Active enrollments present: **`+0.20 boost`**
  * Categories explored: **`+0.15 boost`**

#### 3. `RetrievalPlanner` & `VectorRetrievalAgent` ([retrieval_agent.py](file:///c:/proj/SmartReco/smartreco/backend/app/agents/retrieval_agent.py))
* Formulates semantic vector queries incorporating active enrolled courses, recently viewed titles, and top categories:
  $$\text{"Next recommendations after viewing: <Title>. Domain focus: <Category>"}$$
* Applies hard category filter when dominant category accounts for $\ge 40\%$ of total intent or $\ge 100$ points.
* Performs RAG vector search via ChromaDB using `all-MiniLM-L6-v2` embeddings with SQL fallback.

#### 4. `RankingAgent` ([ranking_agent.py](file:///c:/proj/SmartReco/smartreco/backend/app/agents/ranking_agent.py))
Re-ranks candidate courses using a 6-factor formula combined with domain boosts and exclusion penalties:

$$\text{Final Score} = S_{\text{semantic}} \cdot 0.35 + S_{\text{difficulty}} \cdot 0.20 + S_{\text{progression}} \cdot 0.15 + S_{\text{price}} \cdot 0.10 + S_{\text{tags}} \cdot 0.10 + S_{\text{freshness}} \cdot 0.10 + \text{Boosts} - \text{Penalties}$$

* **Enrolled / Dominant Category Boost:** **`+0.40`**
* **Learning Progression & Completion Boost:** **Up to `+0.30`**
  $$\text{completion\_boost} = \min\left(0.30, 0.15 + \frac{\text{completions}}{\text{total\_completions}} \times 0.15\right)$$
* **Already Enrolled Penalty:** **`-0.30`** (promotes next-step progression courses over owned courses)
* **Dropped Category Penalty:** **`-0.35`**
* **Dropped Course Hard Penalty:** **`-1.0`** (hard exclusion)

#### 5. `NarrativeAgent` ([narrative_agent.py](file:///c:/proj/SmartReco/smartreco/backend/app/agents/narrative_agent.py))
Uses OpenAI Mesh API (`gpt-4o`) to generate custom learning goals, match explanations, and structured 3-step learning roadmaps aligned with top recommendations.

---

## ⭐ Core Platform Features

- **Dynamic AI Recommendation Engine**: Updates recommendations live based on enrollments, module completions, views, and dropped courses.
- **Dual-Layer Un-Enrollment Reset**:
  1. *Behavioral Intent Reset*: Clears active category intent score (`categories_explored[category] = 0`).
  2. *Hard Penalty*: Applies `-1.0` hard penalty to the dropped course ID and `-0.35` penalty to the dropped category.
- **Interactive Course Learning Hub**: 15 technology tracks featuring 100% active, embeddable YouTube video lectures, downloadable source code, and module progress checklists across 56 video slots.
- **Real-Time Dwell Time & Route Telemetry**: Automatically measures dynamic dwell time on page visits (`RouteTracker`) and logs user navigation events.
- **Multi-Layer Cache & Lock Management**: Combines Redis in-memory key storage with PostgreSQL `recommendation_cache` and event-hash invalidation (`compute_event_hash`).

---

## 🌟 Implemented Bonus Features

| Bonus Feature | Implementation Details |
|---|---|
| ⭐ **Structured Agent Framework** | Built with **LangGraph** stateful execution graph ([workflow.py](file:///c:/proj/SmartReco/smartreco/backend/app/langgraph/workflow.py)) containing nodes for Behavior Analysis, Persona Classification, Recovery Check, Vector Retrieval, Multi-Factor Ranking, and Narrative Generation. |
| ⭐ **Scheduled Proactive Delivery** | Background **APScheduler** jobs ([scheduler.py](file:///c:/proj/SmartReco/smartreco/backend/app/scheduler/scheduler.py)) send scheduled email recommendation digests based on user activity. |
| ⭐ **Observability** | Integrated **LangSmith** end-to-end tracing ([langsmith_client.py](file:///c:/proj/SmartReco/smartreco/backend/app/observability/langsmith_client.py)) to monitor agent execution nodes, prompts, and latencies. |
| ⭐ **Retrieval Polish** | 6-factor mathematical re-ranking formula combining Semantic Vector Similarity, Difficulty Level Alignment, Learning Progression, Price/Budget Fit, Tag Overlap, Freshness, and Domain Category Boost. |

### 📊 LangSmith Agent Tracing & Observability Dashboard

SmartReco includes full **LangSmith** integration ([langsmith_client.py](file:///c:/proj/SmartReco/smartreco/backend/app/observability/langsmith_client.py)) to trace all 7 agent execution steps (`smartreco_workflow`, `behavior_analysis`, `persona_classification`, `recovery_detection`, `retrieval_planning`, `vector_retrieval`, `re_ranking`, `narrative_generation`), monitoring inputs/outputs, latencies, and token costs in real time:

![LangSmith Agent Tracing Dashboard](docs/images/langsmith_tracing.png)

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

### 2. Start PostgreSQL & Redis Services
```bash
docker-compose up -d postgres redis
```

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
