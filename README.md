# SmartReco — Behavioral AI Recommendation Agent

> **Built for the Krish Naik Academy SmartReco Build Challenge 2026**  
> *Powered by **Mesh API** (Mandatory LLM Gateway) and **LangGraph Multi-Agent Architecture***

---

## 🏆 Hackathon Overview

**SmartReco** is an intelligent e-learning recommendation platform built for the **SmartReco Build Challenge 2026**. It continuously observes user behavioral activity (page views, course enrollments, category browsing, search queries, scroll depth, and dwell time), understands user intent via a 6-agent reasoning pipeline, retrieves catalog-grounded courses via vector RAG, and generates persuasive personalized learning roadmaps.

---

## 🎯 Architecture & System Design

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                   SmartReco Monorepo                                      │
├─────────────────────────────────────────────┬─────────────────────────────────────────────┤
│                 Frontend                    │                   Backend                   │
│          (React 18 + Vite + TS)             │              (FastAPI + Python)            │
│  ┌───────────────────────────────────────┐  │  ┌───────────────────────────────────────┐  │
│  │ Learner Dashboard │ Activity Stream   │  │  │ API Layer (Auth, Events, Recs, Admin) │  │
│  │ Course Catalog    │ AI Recommendations│  │  │ LangGraph Multi-Agent Workflow Engine │  │
│  └───────────────────┬───────────────────┘  │  └───────────────────┬───────────────────┘  │
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

## ⭐ Key Challenge Requirements & Implementations

### 1. Web Platform Foundation
- **Role-Based Auth**: Simple JWT Bearer authentication with regular user (browsing, recommendations) and admin (product catalog management) roles.
- **Relational Data Model**: PostgreSQL schema connecting `User`, `Product`, `Event`, `Recommendation`, and `RecommendationCache`.

### 2. Dual-Write Product Management
- **SQL & Vector Store Sync**: Admin product operations (`POST /products` & `DELETE /products/{id}`) write to PostgreSQL and generate embeddings indexed into **ChromaDB Vector DB** simultaneously.

### 3. Non-Blocking Behavioral Event Tracking
- **Asynchronous Telemetry**: React tracking hooks ([useTracker.ts](file:///c:/proj/SmartReco/smartreco/frontend/src/tracker/useTracker.ts)) track page views, searches, course views, scroll depths, and dwell time.
- **Batching & Throttling**: High-frequency events are throttled and dispatched via `/events/batch` without blocking UI interactions.

### 4. Agentic Recommendation Engine
- **Mesh API Mandatory Integration**: All LLM calls route through Mesh API gateway (`https://api.meshapi.ai/v1`) using `openai.AsyncOpenAI`.
- **ChromaDB RAG Retrieval**: Grounded vector retrieval ensures recommended courses exist in the real database catalog.
- **Persuasive Narratives**: LLM generates custom learning goals, match explanations, and structured 3-step learning roadmaps.
- **MD5 Behavioral Hash Caching**: Computes a digital fingerprint over recent events to avoid unnecessary LLM calls and purge cache only when user interests shift.

---

## 🌟 Implemented Bonus Features

| Bonus Feature | Implementation Details |
|---|---|
| ⭐ **Structured Agent Framework** | Built with **LangGraph** stateful execution graph ([workflow.py](file:///c:/proj/SmartReco/smartreco/backend/app/langgraph/workflow.py)) containing nodes for Behavior Analysis, Persona Classification, Recovery Check, Vector Retrieval, Multi-Factor Ranking, and Narrative Generation. |
| ⭐ **Scheduled Proactive Delivery** | Background **APScheduler** jobs ([scheduler.py](file:///c:/proj/SmartReco/smartreco/backend/app/scheduler/scheduler.py)) send scheduled email recommendation digests based on user activity. |
| ⭐ **Observability** | Integrated **LangSmith** end-to-end tracing ([langsmith_client.py](file:///c:/proj/SmartReco/smartreco/backend/app/observability/langsmith_client.py)) to monitor agent execution nodes, prompts, and latencies. |
| ⭐ **Retrieval Polish** | 6-factor mathematical re-ranking formula combining Semantic Vector Similarity, Difficulty Level Alignment, Learning Progression, Price/Budget Fit, Tag Overlap, Freshness, and Domain Category Boost. |

---

## 📚 Course Catalog (95+ Courses Across 10 Domains)

Pre-seeded dataset with 95+ comprehensive technology courses:
- **AI/ML & LLM Agents** (10 courses) — LangChain, LangGraph, Transformers, PyTorch, Autonomous Agents.
- **Web Development** (10 courses) — React 18, Next.js 14 App Router, Node.js Microservices, GraphQL, WebSockets.
- **Cyber Security & Ethical Hacking** (10 courses) — OWASP Top 10, Cloud Security, Ghidra Malware Analysis, DevSecOps.
- **Blockchain & Web3** (10 courses) — Solidity, DeFi Protocols, Solana Rust Anchor, zk-SNARKs, NFT Platforms.
- **Mobile Development** (10 courses) — React Native, Flutter 3, iOS Swift, Android Kotlin Compose, KMP.
- **System Design & Architecture** (10 courses) — High-Scale System Design, Go Distributed Systems, Microservices, DB Internals.
- **Data Science & Big Data** (10 courses) — Apache Spark, SQL Analytics, Snowflake, Airflow, Kafka Streaming.
- **Cloud Computing** (10 courses) — AWS Solutions Architect, Kubernetes, Azure DevOps, GCP, Terraform, Serverless.
- **DevOps & SRE** (10 courses) — CI/CD Pipelines, Prometheus/Grafana, Ansible, GitOps ArgoCD, Service Mesh Istio.
- **UI/UX & Product Design** (5 courses) — Figma Prototyping, Design Systems, Motion Graphics, WCAG Accessibility.

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
