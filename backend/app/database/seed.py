"""Database seeding script with 105+ comprehensive courses across 10 domains"""

import asyncio
from datetime import datetime

from app.database.base import AsyncSessionLocal
from app.models import User, Product, UserRole, DifficultyLevel, EmbeddingStatus
from app.auth.password import hash_password


async def seed_database():
    """Seed the database with initial data"""
    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import select
            existing_admin = await session.execute(select(User).where(User.email == "admin@smartreco.com"))
            if not existing_admin.scalar_one_or_none():
                admin_password_hash = hash_password("Admin@123")
                admin_user = User(
                    name="Admin User",
                    email="admin@smartreco.com",
                    password_hash=admin_password_hash,
                    role=UserRole.ADMIN,
                    created_at=datetime.utcnow()
                )
                session.add(admin_user)

            # Check if products already seeded
            from sqlalchemy import delete
            existing_products = await session.execute(select(Product))
            if existing_products.scalars().first():
                print("[INFO] Products already exist in database. Clearing first...")
                await session.execute(delete(Product))
                await session.commit()
            
            # Sample courses data (105 courses across 10 domains)
            courses = [
                # ── 1. AI/ML & LLM Agents (10 courses) ──────────────────────────────────
                {
                    "title": "Introduction to Machine Learning with Python",
                    "description": "Learn the fundamentals of machine learning using Python, scikit-learn, and real-world datasets. Cover supervised and unsupervised learning, model evaluation, and deployment strategies.",
                    "category": "AI/ML",
                    "price": 49.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 12.5,
                    "tags": ["python", "machine-learning", "scikit-learn", "data-science", "supervised-learning"]
                },
                {
                    "title": "Deep Learning Specialization: Neural Networks & TensorFlow",
                    "description": "Master deep learning with hands-on projects covering CNNs, RNNs, LSTMs, and Transformers. Build image classifiers, sequence models, and generative AI applications.",
                    "category": "AI/ML",
                    "price": 89.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 40.0,
                    "tags": ["deep-learning", "tensorflow", "neural-networks", "cnn", "rnn", "transformers"]
                },
                {
                    "title": "Natural Language Processing with Transformers",
                    "description": "Learn state-of-the-art NLP techniques using Hugging Face Transformers. Build chatbots, sentiment analyzers, and text generation models with BERT, GPT, and T5.",
                    "category": "AI/ML",
                    "price": 79.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 25.0,
                    "tags": ["nlp", "transformers", "bert", "gpt", "huggingface", "chatbot"]
                },
                {
                    "title": "Computer Vision Masterclass: From Basics to Advanced",
                    "description": "Comprehensive computer vision course covering image processing, object detection, segmentation, and face recognition using OpenCV and PyTorch.",
                    "category": "AI/ML",
                    "price": 69.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 30.0,
                    "tags": ["computer-vision", "opencv", "pytorch", "object-detection", "image-processing"]
                },
                {
                    "title": "Reinforcement Learning: Theory and Practice",
                    "description": "Dive into reinforcement learning algorithms including Q-learning, DQN, Policy Gradients, and PPO. Build agents that learn from interaction with environments.",
                    "category": "AI/ML",
                    "price": 94.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 35.0,
                    "tags": ["reinforcement-learning", "q-learning", "dqn", "ppo", "ai-agents"]
                },
                {
                    "title": "Building Autonomous AI Agents with LangChain & LangGraph",
                    "description": "Architect autonomous AI agent workflows, multi-agent orchestrations, custom tools, stateful memory, and RAG pipelines using LangChain and LangGraph.",
                    "category": "AI/ML",
                    "price": 99.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 28.0,
                    "tags": ["ai-agents", "langchain", "langgraph", "llm", "rag", "autonomous-agents"]
                },
                {
                    "title": "Prompt Engineering & Fine-Tuning LLMs Masterclass",
                    "description": "Master advanced prompt engineering techniques, LoRA/QLoRA fine-tuning, RLHF, and local deployment of open-source models like Llama 3 and Mistral.",
                    "category": "AI/ML",
                    "price": 74.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 22.0,
                    "tags": ["prompt-engineering", "fine-tuning", "llm", "llama", "lora", "generative-ai"]
                },
                {
                    "title": "Generative AI & AI Art Generation with Stable Diffusion",
                    "description": "Learn generative AI model architectures, diffusion models, ControlNet, and PyTorch implementations for text-to-image and video synthesis.",
                    "category": "AI/ML",
                    "price": 59.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 18.0,
                    "tags": ["generative-ai", "stable-diffusion", "diffusion-models", "pytorch", "ai-art"]
                },
                {
                    "title": "MLOps: Production Machine Learning & Model Monitoring",
                    "description": "Deploy, scale, and monitor machine learning models in production using MLflow, Feast Feature Store, DVC, Kubernetes, and Evidently AI.",
                    "category": "AI/ML",
                    "price": 84.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 32.0,
                    "tags": ["mlops", "mlflow", "feature-store", "kubernetes", "model-monitoring", "deployment"]
                },
                {
                    "title": "Math for Machine Learning: Linear Algebra & Calculus",
                    "description": "Master essential mathematics for AI/ML: matrix operations, eigenvalues, partial derivatives, probability distributions, and gradient descent optimization.",
                    "category": "AI/ML",
                    "price": 39.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 15.0,
                    "tags": ["mathematics", "linear-algebra", "calculus", "probability", "gradient-descent"]
                },
                
                # ── 2. Web Development (10 courses) ─────────────────────────────────────
                {
                    "title": "Full Stack Web Development Bootcamp",
                    "description": "Become a full-stack developer by mastering HTML, CSS, JavaScript, React, Node.js, Express, and MongoDB. Build 10 real-world projects.",
                    "category": "Web Dev",
                    "price": 59.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 50.0,
                    "tags": ["html", "css", "javascript", "react", "nodejs", "mongodb", "fullstack"]
                },
                {
                    "title": "Modern React with Redux and TypeScript",
                    "description": "Learn React 18, Redux Toolkit, TypeScript, and modern hooks. Build scalable applications with best practices for state management and component architecture.",
                    "category": "Web Dev",
                    "price": 54.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 28.0,
                    "tags": ["react", "redux", "typescript", "hooks", "frontend"]
                },
                {
                    "title": "Advanced Node.js: Microservices & Event-Driven Architecture",
                    "description": "Build scalable backend systems with Node.js microservices, RabbitMQ, Redis, and Docker. Learn event-driven design patterns and API gateway implementation.",
                    "category": "Web Dev",
                    "price": 84.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 38.0,
                    "tags": ["nodejs", "microservices", "rabbitmq", "redis", "docker", "backend"]
                },
                {
                    "title": "Next.js 14 & React Server Components Masterclass",
                    "description": "Master Next.js 14 App Router, Server Actions, SSR, SSG, Tailwind CSS, Prisma, and NextAuth. Build enterprise-grade fullstack web applications.",
                    "category": "Web Dev",
                    "price": 69.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 30.0,
                    "tags": ["nextjs", "react", "server-components", "tailwind", "prisma", "ssr"]
                },
                {
                    "title": "Vue.js 3 Complete Course with Composition API",
                    "description": "Master Vue.js 3 and the Composition API. Build modern SPAs with Vuex, Vue Router, and Pinia. Includes Nuxt.js for server-side rendering.",
                    "category": "Web Dev",
                    "price": 49.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 24.0,
                    "tags": ["vuejs", "composition-api", "vuex", "nuxtjs", "frontend", "spa"]
                },
                {
                    "title": "GraphQL API Development with Apollo Server",
                    "description": "Learn to design and build GraphQL APIs with Apollo Server, TypeScript, and Prisma. Cover subscriptions, authentication, and performance optimization.",
                    "category": "Web Dev",
                    "price": 64.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 22.0,
                    "tags": ["graphql", "apollo", "typescript", "prisma", "api", "backend"]
                },
                {
                    "title": "FastAPI & Modern Async Python Web Backend",
                    "description": "Build blazingly fast async RESTful APIs with FastAPI, Pydantic, SQLAlchemy 2.0, PostgreSQL, and JWT security.",
                    "category": "Web Dev",
                    "price": 49.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 18.0,
                    "tags": ["fastapi", "python", "async", "pydantic", "sqlalchemy", "backend"]
                },
                {
                    "title": "Frontend Web Performance & Optimization Studio",
                    "description": "Master web performance metrics (LCP, FID, CLS), Bundle splitting, tree-shaking, Web Workers, Service Workers, and PWA architecture.",
                    "category": "Web Dev",
                    "price": 59.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 20.0,
                    "tags": ["web-performance", "core-web-vitals", "pwa", "webpack", "vite", "optimization"]
                },
                {
                    "title": "Tailwind CSS & Modern CSS Layout Masterclass",
                    "description": "Design responsive, highly interactive web applications using CSS Grid, Flexbox, Tailwind CSS v3, CSS variables, and modern animations.",
                    "category": "Web Dev",
                    "price": 34.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 14.0,
                    "tags": ["tailwind", "css", "flexbox", "grid", "responsive-design", "frontend"]
                },
                {
                    "title": "WebSockets & Real-Time Web Application Engineering",
                    "description": "Build real-time collaborative applications, live chat systems, and real-time dashboards with WebSockets, Socket.io, Redis Pub/Sub, and WebRTC.",
                    "category": "Web Dev",
                    "price": 74.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 26.0,
                    "tags": ["websockets", "socketio", "webrtc", "real-time", "redis", "concurrency"]
                },

                # ── 3. Cyber Security & Ethical Hacking (10 courses) ─────────────────────
                {
                    "title": "Ethical Hacking & Penetration Testing Bootcamp",
                    "description": "Learn ethical hacking from scratch. Master Nmap, Metasploit, Wireshark, Burp Suite, privilege escalation, and network penetration testing.",
                    "category": "Cyber Security",
                    "price": 69.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 42.0,
                    "tags": ["ethical-hacking", "penetration-testing", "metasploit", "nmap", "wireshark", "security"]
                },
                {
                    "title": "Web Application Security & OWASP Top 10",
                    "description": "Master web vulnerability assessment: SQL Injection, XSS, CSRF, SSRF, IDOR, and authentication bypasses. Learn secure coding guidelines.",
                    "category": "Cyber Security",
                    "price": 64.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 24.0,
                    "tags": ["owasp", "web-security", "sqli", "xss", "burp-suite", "cyber-security"]
                },
                {
                    "title": "CompTIA Security+ (SY0-701) Complete Exam Prep",
                    "description": "Prepare for the CompTIA Security+ certification. Covers threats, cryptography, identity management, network defense, and risk management.",
                    "category": "Cyber Security",
                    "price": 49.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 28.0,
                    "tags": ["comptia", "security+", "certification", "network-security", "cryptography"]
                },
                {
                    "title": "Cloud Security Architecture: AWS & Azure Hardening",
                    "description": "Design secure cloud environments. Master AWS IAM, Security Groups, GuardDuty, KMS encryption, Azure Sentinel, and zero-trust architecture.",
                    "category": "Cyber Security",
                    "price": 89.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 35.0,
                    "tags": ["cloud-security", "aws-security", "iam", "zero-trust", "kms", "azure-security"]
                },
                {
                    "title": "Reverse Engineering & Malware Analysis Studio",
                    "description": "Analyze malicious binaries using Ghidra, IDA Pro, x64dbg, and Cuckoo Sandbox. Uncover trojans, ransomware, and rootkits.",
                    "category": "Cyber Security",
                    "price": 99.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 38.0,
                    "tags": ["reverse-engineering", "malware-analysis", "ghidra", "assembly", "binary-analysis"]
                },
                {
                    "title": "Network Security & Packet Analysis with Wireshark",
                    "description": "Deep dive into TCP/IP protocol suite, packet inspection, TLS/SSL decrypting, intrusion detection (Snort/Suricata), and firewall rule design.",
                    "category": "Cyber Security",
                    "price": 54.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 20.0,
                    "tags": ["network-security", "wireshark", "snort", "suricata", "tcp-ip", "firewall"]
                },
                {
                    "title": "Digital Forensics & Incident Response (DFIR)",
                    "description": "Conduct forensic investigations on Windows/Linux systems. Collect memory dumps, analyze registry hives, timelines, and investigate breach incidents.",
                    "category": "Cyber Security",
                    "price": 84.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 32.0,
                    "tags": ["digital-forensics", "dfir", "incident-response", "memory-forensics", "volatility"]
                },
                {
                    "title": "DevSecOps: Integrating Security into CI/CD Pipelines",
                    "description": "Automate security testing in DevOps workflows. Implement SAST, DAST, dependency scanning, container scanning (Trivy), and Secrets detection.",
                    "category": "Cyber Security",
                    "price": 74.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 25.0,
                    "tags": ["devsecops", "sast", "dast", "trivy", "security-automation", "cicd"]
                },
                {
                    "title": "Practical Cryptography & Public Key Infrastructure",
                    "description": "Learn symmetric/asymmetric encryption, SHA hashing, RSA, ECC, Digital Signatures, PKI certificates, TLS 1.3, and post-quantum cryptography.",
                    "category": "Cyber Security",
                    "price": 44.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 16.0,
                    "tags": ["cryptography", "encryption", "rsa", "pki", "tls", "security"]
                },
                {
                    "title": "Red Team Attack Simulation & OSINT Investigations",
                    "description": "Simulate adversary tactics (MITRE ATT&CK framework), OSINT recon, spear phishing, Cobalt Strike operations, and evasive payload delivery.",
                    "category": "Cyber Security",
                    "price": 94.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 36.0,
                    "tags": ["red-team", "osint", "mitre-attack", "cobalt-strike", "evasion", "cyber-warfare"]
                },

                # ── 4. Blockchain & Web3 (10 courses) ──────────────────────────────────
                {
                    "title": "Ethereum & Solidity Smart Contract Development",
                    "description": "Build decentralized applications (dApps) on Ethereum. Write, test, and deploy Solidity smart contracts using Hardhat, Remix, and Ethers.js.",
                    "category": "Blockchain",
                    "price": 64.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 28.0,
                    "tags": ["blockchain", "ethereum", "solidity", "ethersjs", "hardhat", "web3"]
                },
                {
                    "title": "DeFi Protocol Architecture & Smart Contract Security",
                    "description": "Analyze Decentralized Finance protocols: AMMs (Uniswap), Lending (Aave), Staking, Flash Loans, and smart contract audit techniques.",
                    "category": "Blockchain",
                    "price": 94.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 36.0,
                    "tags": ["defi", "solidity-security", "uniswap", "flash-loans", "smart-contract-audit"]
                },
                {
                    "title": "Solana & Rust Web3 Development Masterclass",
                    "description": "Build high-throughput dApps on Solana using Rust and Anchor framework. Create custom Solana programs, tokens (SPL), and React frontends.",
                    "category": "Blockchain",
                    "price": 79.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 30.0,
                    "tags": ["solana", "rust", "anchor", "web3", "crypto", "spl-tokens"]
                },
                {
                    "title": "Zero-Knowledge Proofs & zk-SNARKs Engineering",
                    "description": "Master zero-knowledge cryptography, zk-SNARKs, zk-STARKs, Circom, and Layer 2 rollups (zkSync, Starknet) for privacy and scaling.",
                    "category": "Blockchain",
                    "price": 99.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 34.0,
                    "tags": ["zk-proofs", "zksnarks", "circom", "layer2", "starknet", "privacy"]
                },
                {
                    "title": "NFT Marketplace Development with ERC-721 & ERC-1155",
                    "description": "Create complete NFT platforms: smart contract minting, IPFS metadata storage, royalty management, OpenSea integrations, and React UI.",
                    "category": "Blockchain",
                    "price": 54.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 20.0,
                    "tags": ["nft", "erc721", "erc1155", "ipfs", "opensea", "web3"]
                },
                {
                    "title": "Hyperledger Fabric Enterprise Blockchain Architecture",
                    "description": "Design permissioned enterprise blockchains with Hyperledger Fabric, chaincode in Go/Node.js, channel configuration, and consensus mechanisms.",
                    "category": "Blockchain",
                    "price": 84.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 32.0,
                    "tags": ["hyperledger", "enterprise-blockchain", "chaincode", "go", "permissioned-ledger"]
                },
                {
                    "title": "Bitcoin Core Architecture & Scripting Fundamentals",
                    "description": "Understand Bitcoin consensus, proof-of-work, UTXO model, Bitcoin Script, Lightning Network micropayments, and node operations.",
                    "category": "Blockchain",
                    "price": 49.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 16.0,
                    "tags": ["bitcoin", "crypto", "utxo", "lightning-network", "blockchain-basics"]
                },
                {
                    "title": "DAO Governance & Tokenomics Design Studio",
                    "description": "Architect Decentralized Autonomous Organizations: ERC-20 voting tokens, Governor contracts, Snapshot voting, treasury management, and incentive design.",
                    "category": "Blockchain",
                    "price": 69.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 22.0,
                    "tags": ["dao", "tokenomics", "governance", "erc20", "snapshot", "crypto-economics"]
                },
                {
                    "title": "Web3 Frontend Development with Wagmi & Viem",
                    "description": "Build sleek Web3 user interfaces connecting to MetaMask, WalletConnect, and Coinbase Wallet using Wagmi, Viem, Next.js, and RainbowKit.",
                    "category": "Blockchain",
                    "price": 59.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 24.0,
                    "tags": ["wagmi", "viem", "rainbowkit", "metamask", "react", "web3-frontend"]
                },
                {
                    "title": "Cosmos SDK & Polkadot Substrate Chain Building",
                    "description": "Build custom application-specific blockchains using Cosmos SDK (Tendermint BFT) and Polkadot Substrate in Rust.",
                    "category": "Blockchain",
                    "price": 89.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 38.0,
                    "tags": ["cosmos", "substrate", "polkadot", "rust", "appchains", "interoperability"]
                },

                # ── 5. Mobile App Development (10 courses) ──────────────────────────────
                {
                    "title": "React Native & Expo: iOS & Android Mobile Apps",
                    "description": "Build cross-platform mobile apps for iOS and Android using React Native and Expo. Master navigation, native device features, and app store deployment.",
                    "category": "Mobile Dev",
                    "price": 59.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 35.0,
                    "tags": ["react-native", "expo", "ios", "android", "mobile", "javascript"]
                },
                {
                    "title": "Flutter & Dart Masterclass: Build Production Apps",
                    "description": "Learn Flutter 3 and Dart. Build beautiful, fast native mobile applications with state management (Bloc, Provider), animation, and Firebase backend.",
                    "category": "Mobile Dev",
                    "price": 64.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 40.0,
                    "tags": ["flutter", "dart", "mobile", "bloc", "firebase", "cross-platform"]
                },
                {
                    "title": "iOS App Development with Swift & SwiftUI",
                    "description": "Master modern iOS development with Swift 5 and SwiftUI. Build elegant iPhone/iPad applications with CoreData, Combine, and Async/Await.",
                    "category": "Mobile Dev",
                    "price": 69.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 32.0,
                    "tags": ["ios", "swift", "swiftui", "apple", "xcode", "mobile"]
                },
                {
                    "title": "Android App Development with Kotlin & Jetpack Compose",
                    "description": "Build modern Android apps using Kotlin, Jetpack Compose declarative UI, Coroutines, Flow, Room Database, and MVVM clean architecture.",
                    "category": "Mobile Dev",
                    "price": 64.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 36.0,
                    "tags": ["android", "kotlin", "jetpack-compose", "mvvm", "coroutines", "mobile"]
                },
                {
                    "title": "Mobile App Security & Penetration Testing",
                    "description": "Identify and exploit security flaws in iOS and Android apps. Reverse engineer APKs/IPAs, bypass SSL pinning, analyze binary protections with Frida.",
                    "category": "Mobile Dev",
                    "price": 84.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 26.0,
                    "tags": ["mobile-security", "frida", "objection", "apk-decompilation", "ssl-pinning"]
                },
                {
                    "title": "Progressive Web Apps (PWA) with React & Service Workers",
                    "description": "Transform web apps into installable offline-capable Progressive Web Apps with push notifications, background sync, and App Shell architecture.",
                    "category": "Mobile Dev",
                    "price": 44.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 16.0,
                    "tags": ["pwa", "service-workers", "offline-first", "push-notifications", "web-app"]
                },
                {
                    "title": "KMP (Kotlin Multiplatform) Mobile Architecture",
                    "description": "Share business logic across iOS and Android using Kotlin Multiplatform (KMP), Ktor networking, SQLDelight database, and native UI layers.",
                    "category": "Mobile Dev",
                    "price": 79.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 28.0,
                    "tags": ["kmp", "kotlin-multiplatform", "mobile-architecture", "ios", "android"]
                },
                {
                    "title": "Firebase for Mobile Developers: Auth, Analytics & Firestore",
                    "description": "Add backend capabilities to mobile apps: Firebase Authentication, Cloud Firestore real-time DB, Cloud Functions, Push Notifications, and Crashlytics.",
                    "category": "Mobile Dev",
                    "price": 39.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 18.0,
                    "tags": ["firebase", "firestore", "mobile-backend", "push-notifications", "auth"]
                },
                {
                    "title": "Mobile Game Development with Unity & C#",
                    "description": "Create 2D and 3D games for mobile devices using Unity game engine and C#. Implement touch controls, physics, monetization, and performance tuning.",
                    "category": "Mobile Dev",
                    "price": 74.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 44.0,
                    "tags": ["unity", "csharp", "game-development", "mobile-games", "3d-graphics"]
                },
                {
                    "title": "App Store Optimization (ASO) & Mobile Growth Marketing",
                    "description": "Maximize mobile app downloads and revenue. Master ASO keyword research, screenshot conversion optimization, localized store listings, and user retention.",
                    "category": "Mobile Dev",
                    "price": 34.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 12.0,
                    "tags": ["aso", "mobile-marketing", "app-store", "play-store", "growth", "monetization"]
                },

                # ── 6. System Design & Architecture (10 courses) ────────────────────────
                {
                    "title": "System Design Interview Prep: High-Scale Systems",
                    "description": "Master system design for tech interviews and real-world architectures. Cover load balancing, caching, database sharding, rate limiting, and CAP theorem.",
                    "category": "System Design",
                    "price": 79.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 30.0,
                    "tags": ["system-design", "architecture", "scalability", "interviews", "distributed-systems"]
                },
                {
                    "title": "Distributed Systems Engineering with Go",
                    "description": "Build fault-tolerant distributed systems in Go. Implement Raft consensus, distributed key-value stores, RPC services, gRPC, and gossip protocols.",
                    "category": "System Design",
                    "price": 89.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 38.0,
                    "tags": ["golang", "distributed-systems", "raft", "grpc", "concurrency", "backend"]
                },
                {
                    "title": "Domain-Driven Design (DDD) & Clean Architecture",
                    "description": "Design complex enterprise software using Domain-Driven Design principles, Bounded Contexts, Event Storming, and Clean/Hexagonal Architecture.",
                    "category": "System Design",
                    "price": 69.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 24.0,
                    "tags": ["ddd", "clean-architecture", "hexagonal-architecture", "software-design", "patterns"]
                },
                {
                    "title": "Microservices Design Patterns & Event Sourcing",
                    "description": "Master microservices patterns: CQRS, Event Sourcing, Saga Pattern, Outbox Pattern, API Gateway, and Circuit Breakers with Kafka.",
                    "category": "System Design",
                    "price": 94.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 36.0,
                    "tags": ["microservices", "cqrs", "event-sourcing", "saga-pattern", "kafka", "patterns"]
                },
                {
                    "title": "Database Systems Internals: Indexing, Storage & Transactions",
                    "description": "Learn how database engines work under the hood: B+ Trees, LSM Trees, WAL logging, ACID concurrency control, MVCC, and query optimization.",
                    "category": "System Design",
                    "price": 84.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 32.0,
                    "tags": ["database-internals", "b-tree", "lsm-tree", "acid", "mvcc", "query-optimizer"]
                },
                {
                    "title": "High-Performance Caching Strategies with Redis & Memcached",
                    "description": "Design caching layers for low-latency web applications: cache-aside, write-through, cache eviction policies, Redis Sentinel, and Redis Cluster.",
                    "category": "System Design",
                    "price": 49.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 15.0,
                    "tags": ["redis", "memcached", "caching", "performance", "low-latency"]
                },
                {
                    "title": "API Design Masterclass: REST, gRPC & OpenAPI Specifications",
                    "description": "Design robust enterprise APIs. Master RESTful conventions, gRPC protocol buffers, OpenAPI 3.0 specs, rate limiting, versioning, and HATEOAS.",
                    "category": "System Design",
                    "price": 44.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 18.0,
                    "tags": ["api-design", "rest", "grpc", "openapi", "protobuf", "software-architecture"]
                },
                {
                    "title": "Fault Tolerance, Resilience & Chaos Engineering",
                    "description": "Build resilient software that survives outages. Master Chaos Mesh, Gremlin, rate limiters, bulkhead pattern, and graceful degradation techniques.",
                    "category": "System Design",
                    "price": 74.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 22.0,
                    "tags": ["resilience", "chaos-engineering", "fault-tolerance", "sre", "reliability"]
                },
                {
                    "title": "Cloud-Native Enterprise Integration Patterns with Apache Camel",
                    "description": "Solve enterprise application integration challenges using EIP standards, message routing, transformation, and event-driven messaging.",
                    "category": "System Design",
                    "price": 64.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 26.0,
                    "tags": ["enterprise-integration", "apache-camel", "messaging", "integration-patterns"]
                },
                {
                    "title": "Software Architecture Patterns & Refactoring Legacy Code",
                    "description": "Identify architectural technical debt, apply SOLID principles, refactor monolithic codebases safely into modern modular architecture.",
                    "category": "System Design",
                    "price": 54.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 20.0,
                    "tags": ["software-architecture", "solid-principles", "refactoring", "clean-code"]
                },

                # ── 7. Data Science & Big Data (10 courses) ────────────────────────────
                {
                    "title": "Data Science with Python: Complete Bootcamp",
                    "description": "Master data analysis, visualization, and statistical modeling with Python, Pandas, NumPy, Matplotlib, and Seaborn. Work with real datasets.",
                    "category": "Data Science",
                    "price": 54.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 32.0,
                    "tags": ["python", "pandas", "numpy", "matplotlib", "data-analysis", "statistics"]
                },
                {
                    "title": "Advanced Data Engineering with Apache Spark",
                    "description": "Build large-scale data pipelines using Apache Spark, PySpark, and Delta Lake. Learn streaming, batch processing, and data lake architecture.",
                    "category": "Data Science",
                    "price": 89.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 36.0,
                    "tags": ["spark", "pyspark", "data-engineering", "etl", "big-data", "delta-lake"]
                },
                {
                    "title": "SQL for Data Analysis: From Basics to Advanced",
                    "description": "Master SQL for data analysis including complex joins, window functions, CTEs, and query optimization. Work with PostgreSQL and real business scenarios.",
                    "category": "Data Science",
                    "price": 39.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 18.0,
                    "tags": ["sql", "postgresql", "data-analysis", "database", "queries"]
                },
                {
                    "title": "Data Visualization Mastery with Tableau & Power BI",
                    "description": "Create stunning dashboards and reports with Tableau and Power BI. Learn storytelling with data, DAX formulas, and interactive visualizations.",
                    "category": "Data Science",
                    "price": 44.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 20.0,
                    "tags": ["tableau", "powerbi", "visualization", "dashboard", "business-intelligence"]
                },
                {
                    "title": "Time Series Analysis and Forecasting",
                    "description": "Learn time series analysis, ARIMA, SARIMA, Prophet, and LSTM models for forecasting. Apply to stock prices, sales data, and more.",
                    "category": "Data Science",
                    "price": 69.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 26.0,
                    "tags": ["time-series", "forecasting", "arima", "prophet", "lstm", "statistics"]
                },
                {
                    "title": "Snowflake Data Warehousing Masterclass",
                    "description": "Architect modern cloud data warehouses with Snowflake. Cover virtual warehouses, snowpipe ingestion, zero-copy cloning, and security governance.",
                    "category": "Data Science",
                    "price": 74.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 24.0,
                    "tags": ["snowflake", "data-warehouse", "cloud-data", "sql", "data-engineering"]
                },
                {
                    "title": "Data Pipeline Orchestration with Apache Airflow & dbt",
                    "description": "Build robust data pipelines with Apache Airflow DAGs and dbt (data build tool) for data transformation, testing, and documentation.",
                    "category": "Data Science",
                    "price": 79.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 28.0,
                    "tags": ["airflow", "dbt", "data-pipeline", "orchestration", "etl", "dataops"]
                },
                {
                    "title": "Statistical Inference & Hypothesis Testing for Data Analysts",
                    "description": "Master probability, A/B testing methodology, p-values, confidence intervals, ANOVA, and regression analysis for data-driven decisions.",
                    "category": "Data Science",
                    "price": 34.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 14.0,
                    "tags": ["statistics", "hypothesis-testing", "ab-testing", "probability", "data-analysis"]
                },
                {
                    "title": "Real-Time Streaming Data Pipelines with Apache Kafka",
                    "description": "Build event-driven data streaming pipelines with Apache Kafka, Kafka Connect, KSQLDB, and Schema Registry in production.",
                    "category": "Data Science",
                    "price": 84.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 32.0,
                    "tags": ["kafka", "streaming", "event-driven", "ksqldb", "big-data"]
                },
                {
                    "title": "Vector Databases for AI: ChromaDB, Pinecone & Qdrant",
                    "description": "Store and index high-dimensional embeddings for AI applications. Master vector search algorithms (HNSW, IVFFlat), hybrid search, and RAG optimization.",
                    "category": "Data Science",
                    "price": 69.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 22.0,
                    "tags": ["vector-database", "chromadb", "pinecone", "qdrant", "embeddings", "rag"]
                },

                # ── 8. Cloud Computing (10 courses) ────────────────────────────────────
                {
                    "title": "AWS Cloud Practitioner: Complete Course",
                    "description": "Learn AWS fundamentals covering EC2, S3, RDS, Lambda, and CloudFormation. Prepare for the AWS Cloud Practitioner certification exam.",
                    "category": "Cloud",
                    "price": 49.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 16.0,
                    "tags": ["aws", "cloud", "ec2", "s3", "lambda", "certification"]
                },
                {
                    "title": "Kubernetes: From Zero to Production",
                    "description": "Master Kubernetes orchestration, deployments, services, ingress, and monitoring. Deploy microservices to production with Helm and GitOps.",
                    "category": "Cloud",
                    "price": 79.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 34.0,
                    "tags": ["kubernetes", "k8s", "docker", "helm", "devops", "orchestration"]
                },
                {
                    "title": "Azure DevOps and Cloud Architecture",
                    "description": "Build cloud-native applications on Azure. Learn Azure DevOps, ARM templates, Azure Functions, and microservices architecture.",
                    "category": "Cloud",
                    "price": 74.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 28.0,
                    "tags": ["azure", "devops", "cloud", "arm-templates", "azure-functions"]
                },
                {
                    "title": "Google Cloud Platform: Complete Developer Course",
                    "description": "Master GCP services including Compute Engine, Cloud Functions, BigQuery, and Cloud Run. Build scalable applications on Google Cloud.",
                    "category": "Cloud",
                    "price": 69.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 30.0,
                    "tags": ["gcp", "google-cloud", "bigquery", "cloud-run", "compute-engine"]
                },
                {
                    "title": "Terraform Infrastructure as Code Masterclass",
                    "description": "Learn infrastructure as code with Terraform. Manage AWS, Azure, and GCP resources. Cover modules, state management, and CI/CD integration.",
                    "category": "Cloud",
                    "price": 64.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 24.0,
                    "tags": ["terraform", "iac", "infrastructure", "devops", "aws", "azure"]
                },
                {
                    "title": "AWS Certified Solutions Architect Associate (SAA-C03)",
                    "description": "Deep dive into AWS cloud architecture: VPC design, Auto Scaling, Route 53, DynamoDB, SQS/SNS, and high-availability multi-region systems.",
                    "category": "Cloud",
                    "price": 84.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 45.0,
                    "tags": ["aws-solutions-architect", "aws", "vpc", "dynamodb", "cloud-architecture"]
                },
                {
                    "title": "Serverless Applications on AWS with Lambda & API Gateway",
                    "description": "Build zero-server applications using AWS Lambda, API Gateway, DynamoDB, EventBridge, and AWS SAM framework.",
                    "category": "Cloud",
                    "price": 59.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 20.0,
                    "tags": ["serverless", "aws-lambda", "api-gateway", "dynamodb", "sam"]
                },
                {
                    "title": "Cloud FinOps & Cost Optimization Masterclass",
                    "description": "Reduce cloud bills across AWS, Azure, and GCP. Master Reserved Instances, Savings Plans, spot instances, rightsizing, and cost allocation tags.",
                    "category": "Cloud",
                    "price": 39.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 12.0,
                    "tags": ["finops", "cloud-cost", "cost-optimization", "aws-cost", "azure-cost"]
                },
                {
                    "title": "Multi-Cloud Strategy & Hybrid Infrastructure Management",
                    "description": "Design resilient multi-cloud architectures. Connect hybrid on-premise and multi-cloud environments using HashiCorp Nomad, Consul, and Vault.",
                    "category": "Cloud",
                    "price": 89.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 32.0,
                    "tags": ["multi-cloud", "hybrid-cloud", "consul", "vault", "nomad"]
                },
                {
                    "title": "OpenStack Private Cloud Infrastructure Administration",
                    "description": "Deploy and manage private cloud infrastructure using OpenStack: Nova compute, Neutron networking, Cinder storage, and Keystone identity.",
                    "category": "Cloud",
                    "price": 79.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 36.0,
                    "tags": ["openstack", "private-cloud", "virtualization", "sysadmin", "infrastructure"]
                },

                # ── 9. DevOps & SRE (10 courses) ───────────────────────────────────────
                {
                    "title": "DevOps Fundamentals: CI/CD Pipeline Mastery",
                    "description": "Learn DevOps practices including Git, Jenkins, GitLab CI, Docker, and automated testing. Build complete CI/CD pipelines from scratch.",
                    "category": "DevOps",
                    "price": 59.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 26.0,
                    "tags": ["devops", "cicd", "jenkins", "gitlab", "docker", "git"]
                },
                {
                    "title": "Docker and Container Orchestration Complete Guide",
                    "description": "Master Docker, Docker Compose, and container best practices. Learn multi-stage builds, security, and optimization techniques.",
                    "category": "DevOps",
                    "price": 54.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 22.0,
                    "tags": ["docker", "containers", "docker-compose", "containerization", "devops"]
                },
                {
                    "title": "Monitoring and Logging: Prometheus, Grafana & ELK Stack",
                    "description": "Implement comprehensive monitoring solutions with Prometheus, Grafana, Elasticsearch, Logstash, and Kibana. Set up alerts and dashboards.",
                    "category": "DevOps",
                    "price": 69.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 28.0,
                    "tags": ["prometheus", "grafana", "elk", "monitoring", "logging", "observability"]
                },
                {
                    "title": "Ansible Automation: Configuration Management",
                    "description": "Automate infrastructure with Ansible. Learn playbooks, roles, variables, and best practices for managing server configurations at scale.",
                    "category": "DevOps",
                    "price": 49.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 20.0,
                    "tags": ["ansible", "automation", "configuration-management", "devops", "iac"]
                },
                {
                    "title": "Site Reliability Engineering (SRE) Practices",
                    "description": "Learn SRE principles including SLIs, SLOs, error budgets, incident management, and chaos engineering. Build reliable distributed systems.",
                    "category": "DevOps",
                    "price": 79.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 32.0,
                    "tags": ["sre", "reliability", "monitoring", "incident-management", "chaos-engineering"]
                },
                {
                    "title": "GitOps with ArgoCD & Flux for Kubernetes",
                    "description": "Implement GitOps deployment workflows for Kubernetes clusters using ArgoCD, Flux CD, Kustomize, and GitHub Actions.",
                    "category": "DevOps",
                    "price": 74.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 24.0,
                    "tags": ["gitops", "argocd", "flux", "kubernetes", "declarative-deployment"]
                },
                {
                    "title": "Linux System Administration & Shell Scripting Mastery",
                    "description": "Master Linux CLI, Bash shell scripting, systemd services, user management, disk partitioning, and cron job automation.",
                    "category": "DevOps",
                    "price": 39.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 25.0,
                    "tags": ["linux", "bash", "shell-scripting", "sysadmin", "automation"]
                },
                {
                    "title": "GitHub Actions Complete CI/CD & Automation Workflow",
                    "description": "Automate software workflows with GitHub Actions: build matrixes, custom action creation, secrets management, and automated release deployment.",
                    "category": "DevOps",
                    "price": 44.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 16.0,
                    "tags": ["github-actions", "cicd", "automation", "github", "devops"]
                },
                {
                    "title": "OpenTelemetry & Distributed Tracing Masterclass",
                    "description": "Instrument microservices with OpenTelemetry API/SDK, Jaeger, Zipkin, and Datadog for end-to-end request tracing.",
                    "category": "DevOps",
                    "price": 84.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 26.0,
                    "tags": ["opentelemetry", "tracing", "jaeger", "observability", "microservices"]
                },
                {
                    "title": "Service Mesh Engineering with Istio & Linkerd",
                    "description": "Manage microservice traffic, mutual TLS (mTLS) encryption, traffic splitting, canary deployments, and circuit breaking with Istio.",
                    "category": "DevOps",
                    "price": 89.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 30.0,
                    "tags": ["service-mesh", "istio", "linkerd", "mtls", "canary-deployment"]
                },

                # ── 10. UI/UX & Product Design (5 courses) ──────────────────────────────
                {
                    "title": "UI/UX Design Fundamentals with Figma",
                    "description": "Learn user interface and experience design principles. Master Figma for wireframing, prototyping, and creating design systems.",
                    "category": "Design",
                    "price": 44.99,
                    "difficulty_level": DifficultyLevel.BEGINNER,
                    "duration_hours": 18.0,
                    "tags": ["ui", "ux", "figma", "design", "prototyping", "wireframing"]
                },
                {
                    "title": "Advanced Product Design and Design Thinking",
                    "description": "Master product design methodology, user research, persona creation, and design thinking frameworks. Build user-centered products.",
                    "category": "Design",
                    "price": 59.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 24.0,
                    "tags": ["product-design", "design-thinking", "user-research", "ux", "persona"]
                },
                {
                    "title": "Motion Design and Animation with After Effects",
                    "description": "Create stunning animations and motion graphics with Adobe After Effects. Learn keyframing, expressions, and visual effects for web and video.",
                    "category": "Design",
                    "price": 64.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 26.0,
                    "tags": ["motion-design", "animation", "after-effects", "visual-effects", "graphics"]
                },
                {
                    "title": "Design Systems: Building Scalable UI Components",
                    "description": "Learn to create and maintain design systems. Cover component libraries, design tokens, documentation, and cross-platform consistency.",
                    "category": "Design",
                    "price": 54.99,
                    "difficulty_level": DifficultyLevel.ADVANCED,
                    "duration_hours": 22.0,
                    "tags": ["design-systems", "ui-components", "design-tokens", "figma", "storybook"]
                },
                {
                    "title": "Accessibility in Design: WCAG 2.1 Compliance",
                    "description": "Design accessible products following WCAG 2.1 guidelines. Learn inclusive design principles, screen reader optimization, and testing tools.",
                    "category": "Design",
                    "price": 39.99,
                    "difficulty_level": DifficultyLevel.INTERMEDIATE,
                    "duration_hours": 16.0,
                    "tags": ["accessibility", "wcag", "inclusive-design", "a11y", "usability"]
                },
            ]
            
            # Create product records
            for course_data in courses:
                product = Product(
                    title=course_data["title"],
                    description=course_data["description"],
                    category=course_data["category"],
                    price=course_data["price"],
                    difficulty_level=course_data["difficulty_level"],
                    duration_hours=course_data["duration_hours"],
                    tags=course_data["tags"],
                    embedding_status=EmbeddingStatus.PENDING,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(product)
            
            await session.commit()
            print("[SUCCESS] Database seeded successfully!")
            print("   - Created 1 admin user (admin@smartreco.com)")
            print(f"   - Created {len(courses)} courses across 10 domains:")
            print("     - AI/ML: 10 courses")
            print("     - Web Dev: 10 courses")
            print("     - Cyber Security: 10 courses")
            print("     - Blockchain: 10 courses")
            print("     - Mobile Dev: 10 courses")
            print("     - System Design: 10 courses")
            print("     - Data Science: 10 courses")
            print("     - Cloud: 10 courses")
            print("     - DevOps: 10 courses")
            print("     - Design: 5 courses")
            
        except Exception as e:
            await session.rollback()
            print(f"[ERROR] Error seeding database: {e}")
            raise


async def clear_database():
    """Clear all data from the database (use with caution!)"""
    from app.models import Event, Recommendation, RecommendationCache
    from sqlalchemy import delete
    
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(delete(RecommendationCache))
            await session.execute(delete(Recommendation))
            await session.execute(delete(Event))
            await session.execute(delete(Product))
            await session.execute(delete(User))
            await session.commit()
            print("[SUCCESS] Database cleared successfully!")
        except Exception as e:
            await session.rollback()
            print(f"[ERROR] Error clearing database: {e}")
            raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        print("[CLEAR] Clearing database...")
        asyncio.run(clear_database())
        sys.exit(0)
    else:
        print("[SEED] Seeding database with 105+ courses...")
        asyncio.run(seed_database())
        sys.exit(0)
