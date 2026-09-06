# 🚀 OnboardAI — Agentic KYC Platform

OnboardAI is an **AI-powered KYC onboarding platform** that automates customer verification using a Supervisor/Worker agent architecture, with human review for cases requiring additional verification.

## 🌐 Live Demo

🔗 **[OnboardAI — Live on Render](https://onboardai-frontend-o4sz.onrender.com/)**

---

## ✨ Features

* 🔐 JWT Authentication & Role-Based Access
* 👤 Customer, Analyst, QA & Admin roles
* 🤖 Multi-agent KYC workflow using LangGraph
* 📄 Document upload & OCR verification
* 🪪 Identity verification
* 🔎 Sanctions & PEP screening
* ⚠️ Risk & anomaly detection
* 👨‍💼 Human review for flagged cases
* 📧 **LLM-powered professional email generation**
* 📊 KYC & agent monitoring dashboard
* 📝 Evidence, audit & workflow tracking
* 🔄 Durable job queue with retry & idempotency
* 🔌 MCP-based tool gateway
* 🧠 LlamaIndex/ChromaDB knowledge layer with local fallback

---

## 🏗️ Architecture

```text
React/Vite
    ↓
FastAPI
    ↓
LangGraph Supervisor
    ↓
Data Intake → Documents → Identity → Screening
    ↓
Risk → Anomaly Detection → Decision
    ↓
Approve / Human Review
    ↓
AI Explanation + Monitoring
```

---

## 📧 LLM Email Generation

The platform can generate personalized KYC emails using an LLM, including:

* KYC approval notifications
* Missing document requests
* Human review notifications
* Additional information requests
* KYC status updates

The **final KYC decision remains controlled by deterministic business rules**, while the LLM assists with communication and explanations.

---

## 🛠️ Tech Stack

| Component        | Technology           |
| ---------------- | -------------------- |
| Frontend         | React, Vite          |
| Backend          | FastAPI              |
| AI Orchestration | LangGraph            |
| LLM              | Groq / LLM Provider  |
| Database         | SQLite               |
| Knowledge Layer  | LlamaIndex, ChromaDB |
| OCR              | Tesseract            |
| Authentication   | JWT                  |
| Tool Gateway     | MCP                  |
| Monitoring       | OpenTelemetry        |
| API Testing      | Postman              |
| Deployment       | Render               |

---

## ⚙️ Run Locally

### Backend

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Create `.env` from `.env.example` and add your required API credentials.

---

## 🔌 Key APIs

```text
POST /api/auth/register
POST /api/auth/login
POST /api/kyc/process-upload
POST /api/documents/upload
POST /api/workflow/cases/{case_id}/run
GET  /api/cases/{case_id}/summary
GET  /api/reviews/pending
GET  /api/dashboard/stats
```

---

## 📌 Project Goal

OnboardAI demonstrates how **Agentic AI, LLMs, and workflow orchestration** can be combined to build an intelligent, secure, and extensible KYC onboarding platform.

> ⚠️ This is a demonstration project. Risk and decision rules are not intended as regulatory advice.

---

## 👨‍💻 Developer

**Himanshu Ranjan**

[GitHub](https://github.com/himanshuranjan977) • [LinkedIn](https://www.linkedin.com/in/himanshu-ranjan-6019a6215/)
