# SelfHost Media Orchestrator – Documentation Handbook

Welcome to the central documentation hub for the SelfHost Media Orchestrator. This registry contains all technical design specs, product definitions, and post-mortem bug analysis to assist developers and maintainers in understanding the system logic.

---

## 🏛️ Architecture & Concept logic
Documents explaining how the different pieces of the framework piece together under the hood.

- [**System Design**](ARCHITECTURE/system_design.md): The high-level relationships between the React frontend, FastAPI backend, SQLite, and Docker containerization.
- [**Application Architecture**](ARCHITECTURE/application_architecture.md): The deep-dive into internal coding logic. Includes the multi-threaded scanner workflow, scraper fallback mechanism, and real-time SSE state manager.

---

## 📦 Product & Scope
Documents outlining what the application aims to perform, and what it explicitly avoids.

- [**MVP Definition**](PRODUCT/mvp.md): The rigid scope and defined boundaries of the Minimum Viable Product (version 1.0).
- [**Development Roadmap**](PRODUCT/roadmap.md): The upcoming feature tracks, specifically concerning hybrid streaming playback and standalone desktop packaging.

---

## 🛠️ Troubleshooting & History
Knowledge base of complex errors we've historically navigated.

- [**Bug Reports & Root Cause Analysis (RSA)**](TROUBLESHOOTING/bug_reports_and_rsa.md): A detailed log breaking down major roadblocks (like Frontend missing files via pagination limits or sequential I/O Wait bottlenecks) and their integrated solutions. 

---

> [!NOTE]
> *Legacy planning documents and raw session outputs (like old task loops) are archived within the `/PLAN` sub-directory for reference, but are distinct from this formal documentation handbook.*
