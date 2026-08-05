# SmartReco - Behavioral AI Recommendation Platform

A production-grade behavioral AI recommendation system for online learning marketplaces, powered by a **LangGraph multi-agent architecture**, **vector similarity retrieval**, and **real-time event telemetry**.

---

## 🚀 Overview

**SmartReco** is an intelligent e-learning recommendation platform that turns user behavioral signals (page views, course enrollments, category browsing, search queries, and dwell times) into personalized learning journeys. 

The system features a **6-agent LangGraph execution graph** that classifies learners into behavioral personas, constructs semantic vector search queries, ranks course candidates using multi-factor scoring, and generates tailored learning roadmaps with LLM narratives.

---

## 🏗️ Architecture & Monorepo Layout

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

## 📚 Rich Multi-Domain Course Catalog (95+ Courses)

SmartReco includes 95+ courses spanning 10 technology domains:
1. **AI/ML & LLM Agents** (10 courses) — PyTorch, Transformers, LangChain, Autonomous Agents, Prompt Fine-Tuning.
2. **Web Development** (10 courses) — React 18, Next.js 14, Node.js Microservices, Vue 3, GraphQL, WebSockets.
3. **Cyber Security & Ethical Hacking** (10 courses) — OWASP Top 10, Cloud Security, Ghidra Malware Analysis, DevSecOps.
4. **Blockchain & Web3** (10 courses) — Solidity, DeFi Protocols, Solana Rust, Zero-Knowledge zk-SNARKs, NFT Platforms.
5. **Mobile Development** (10 courses) — React Native, Flutter 3, iOS Swift, Android Kotlin Compose, KMP.
6. **System Design & Architecture** (10 courses) — High-Scale Design, Go Distributed Systems, Microservices Patterns, DB Internals.
7. **Data Science & Big Data** (10 courses) — Apache Spark, SQL Analytics, Snowflake, Airflow Orchestration, Kafka Streaming.
8. **Cloud Computing** (10 courses) — AWS Solutions Architect, Kubernetes, Azure DevOps, GCP, Terraform, Serverless.
9. **DevOps & SRE** (10 courses) — CI/CD Pipelines, Prometheus/Grafana, Ansible, GitOps ArgoCD, Service Mesh Istio.
10. **UI/UX & Product Design** (5 courses) — Figma Prototyping, Design Systems, Motion Graphics, WCAG Accessibility.

---

## 🤖 Agent Workflow & LangGraph Execution

The core recommendation engine executes a stateful **6-agent LangGraph workflow**:

```
                  ┌──────────────────────┐
                  │    Behavior Agent    │ (Analyzes interaction history & weighted intent)
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │    Persona Agent     │ (Classifies user into 1 of 6 behavioral personas)
                  └──────────┬───────────┘
                             │
                             ▼
               ┌───────────────────────────┐
               │    Recovery Agent Check   │ (Conditional Branching)
               └─────────────┬─────────────┘
                             │
             ┌───────────────┴───────────────┐
             │                               │
    [Risk / Low Engagement]         [Standard Path]
             │                               │
             ▼                               ▼
  ┌─────────────────────┐         ┌─────────────────────┐
  │   Recovery Mode     │         │   Retrieval Agent   │ (Hybrid ChromaDB + PostgreSQL fallback)
  │ (Re-engagement flow)│         └──────────┬───────────┘
  └─────────────────────┘                    │
                                             ▼
                                  ┌─────────────────────┐
                                  │    Ranking Agent    │ (6-Factor multi-score re-ranking)
                                  └──────────┬───────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │   Narrative Agent   │ (Mesh API LLM story & roadmap generation)
                                  └──────────┬───────────┘
```

---

## 🌐 100% Free Cloud Deployment Guide

You can deploy the complete SmartReco stack **100% FREE** on modern cloud platforms:

### 1. Database & Cache Tier (Free Services)
- **PostgreSQL Database**: Create a free PostgreSQL database on [Neon.tech](https://neon.tech) or [Supabase](https://supabase.com). Copy the async connection URL (`postgresql+asyncpg://...`).
- **Redis Cache**: Create a free Redis instance on [Upstash.com](https://upstash.com). Copy the TLS Redis URL (`rediss://...`).

### 2. FastAPI Backend Service (Render.com)
1. Push your repository to GitHub.
2. Sign up on [Render.com](https://render.com) (Free Web Service Tier).
3. Create a **New Web Service** and select your repository.
4. Set **Root Directory**: `smartreco/backend`.
5. Set **Build Command**: `pip install -r requirements.txt`.
6. Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
7. Environment Variables:
   - `DATABASE_URL`: Your Neon/Supabase PostgreSQL connection string.
   - `REDIS_URL`: Your Upstash Redis URL.
   - `MESH_API_KEY`: Your LLM API Gateway key.
   - `JWT_SECRET_KEY`: Random 32-character secret key.

### 3. React Frontend Application (Vercel)
1. Sign up on [Vercel.com](https://vercel.com).
2. Click **Import Project** and select your GitHub repository.
3. Set **Framework Preset**: `Vite`.
4. Set **Root Directory**: `smartreco/frontend`.
5. Environment Variables:
   - `VITE_API_BASE_URL`: `https://your-backend.onrender.com` (Your Render Backend URL).
6. Click **Deploy**. Vercel will build and host your app on global HTTPS CDN for free!

---

## 🔌 API Endpoint Reference

| Method | Path | Auth Required | Description |
|---|---|---|---|
| `GET` | `/health` | None | System health check (`{"status": "ok", "version": "1.0.0"}`) |
| `POST` | `/auth/register` | None | Register new user account |
| `POST` | `/auth/login` | None | Authenticate user and receive JWT bearer token |
| `GET` | `/auth/me` | User / Admin | Retrieve current user profile |
| `POST` | `/auth/refresh` | User / Admin | Refresh current JWT access token |
| `GET` | `/products` | None | Public course catalog search & category filtering |
| `GET` | `/products/{product_id}` | None | Retrieve course details by ID |
| `POST` | `/events/batch` | User / Admin | Submit batch of behavioral events (max 50) |
| `POST` | `/events/single` | User / Admin | Submit single behavioral event |
| `GET` | `/events/me` | User / Admin | Retrieve recent event history for current user |
| `GET` | `/events/me/hash` | User / Admin | Compute current behavioral event MD5 hash |
| `GET` | `/recommendations/me` | User / Admin | Get personalized recommendations, story & roadmap |
| `POST` | `/recommendations/refresh` | User / Admin | Force refresh recommendation and persona caches |
| `GET` | `/recommendations/history` | User / Admin | View recommendation history log |
| `POST` | `/products` | Admin Only | Create course, generate vector embedding & index in ChromaDB |
| `DELETE` | `/products/{product_id}` | Admin Only | Delete course from PostgreSQL & ChromaDB |

---

## 💻 Local Development Setup

```bash
# 1. Start PostgreSQL & Redis via Docker
docker-compose up -d postgres redis

# 2. Seed database with 95+ courses across 10 domains
cd smartreco/backend && python -m app.database.seed

# 3. Launch Backend Server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Launch Frontend Server
cd smartreco/frontend && npm run dev
```
