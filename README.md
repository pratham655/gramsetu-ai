# GramSetu AI (ग्रामीण सेतु)

> **AI-Powered Civic Intelligence Platform Bridging Citizens & Schemes**

---

## 1. Project Overview

**GramSetu AI** is an AI-powered civic assistance platform designed to help citizens discover government welfare schemes, understand eligibility criteria deterministically, verify policy details directly from official government gazettes, identify and audit required documentation, and receive actionable, structured application dossiers.

---

## 2. Core Architecture & Modules

```
┌─────────────────────────────────────────────────────────────┐
│                      Citizen Profile                        │
│          (Age, Income, State, Landholding, Category, BPL)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             1. YojanaMatch (Eligibility Engine)             │
│        - Deterministic rule-based filter against schemes     │
│        - Evaluates field operators (equals, in, gt, lte...)  │
│        - Surfaces ranked eligible programs & explanations    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             2. NitiRAG (Knowledge & Verification)           │
│        - Grounded retrieval over official gazettes & docs    │
│        - Live verification of quotas & deadlines             │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│            3. KagazCheck (Document Intelligence)            │
│        - Multimodal document checklist & gap validation      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             4. Parchaa (Actionable Application Plan)        │
│        - Printable single-page dossier with next steps       │
└──────────────────────────────┘
```

---

## 3. Technology Stack

- **Frontend**: React 19, Vite, TypeScript, Tailwind CSS, Axios, Lucide Icons.
- **Backend**: Python 3.13+, FastAPI, Pydantic v2, Pydantic Settings, SQLAlchemy 2.0, Uvicorn.
- **Database & Retrieval**: PostgreSQL with SQLAlchemy ORM (ready for `pgvector` extension in NitiRAG).
- **AI & Orchestration (Future Milestones)**: LangChain, LangGraph.

---

## 4. Repository Structure

```
gramsetu-ai/
├── .gitignore                    # Root gitignore protecting .env and virtual environments
├── frontend/                     # React + Vite + TypeScript web application
│   ├── src/
│   │   ├── services/
│   │   │   └── api.ts            # Axios API client & YojanaMatch endpoints
│   │   ├── App.tsx               # Interactive YojanaMatch testing interface
│   │   ├── main.tsx              # React DOM entrypoint
│   │   └── index.css             # Tailwind CSS design system styles
│   ├── .env.example              # Frontend environment template
│   ├── .env                      # Local frontend environment config
│   ├── package.json              # Frontend dependencies
│   └── vite.config.ts            # Vite & Tailwind configuration
├── backend/                      # FastAPI backend application
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── health.py     # GET /api/v1/health endpoint
│   │   │       ├── eligibility.py# POST /api/v1/eligibility/match endpoint
│   │   │       └── router.py     # Aggregated v1 API router
│   │   ├── core/
│   │   │       └── config.py     # Pydantic BaseSettings & CORS/Database config
│   │   ├── database/
│   │   │       ├── base.py       # SQLAlchemy Declarative Base
│   │   │       └── session.py    # PostgreSQL session & connection management
│   │   ├── models/
│   │   │       └── scheme.py     # Scheme and EligibilityRule relational models
│   │   ├── schemas/
│   │   │       ├── eligibility.py# CitizenProfile & Match response schemas
│   │   │       └── scheme.py     # Scheme & Rule Pydantic schemas
│   │   ├── services/
│   │   │       ├── yojanamatch.py# Deterministic rule evaluation engine
│   │   │       └── scheme_service.py # Scheme data repository & database loader
│   │   ├── data/
│   │   │       └── verified_schemes.py # Authoritative verified scheme seed data
│   │   └── main.py               # FastAPI application setup & Swagger docs
│   ├── tests/
│   │   └── test_eligibility.py   # Unit tests for YojanaMatch rule engine
│   ├── .env.example              # Backend environment template
│   ├── .env                      # Local backend environment config
│   └── requirements.txt          # Python backend dependencies
├── data/
│   ├── schemes/                  # Structured scheme datasets (.gitkeep)
│   └── documents/                # Government policy gazettes & circulars (.gitkeep)
└── README.md                     # Project documentation
```

---

## 5. API Endpoints

### 1. Health Check
`GET /api/v1/health`
```json
{
  "status": "ok",
  "service": "gramsetu-api"
}
```

### 2. Scheme Eligibility Matching (YojanaMatch)
`POST /api/v1/eligibility/match`

**Sample Request**:
```json
{
  "age": 42,
  "income": 180000,
  "state": "Karnataka",
  "district": "Tumakuru",
  "gender": "male",
  "occupation": "farmer",
  "landholding": 2.5,
  "category": "OBC",
  "bpl": true
}
```

**Sample Response**:
```json
{
  "citizen_profile": {
    "age": 42,
    "income": 180000.0,
    "state": "Karnataka",
    "district": "Tumakuru",
    "gender": "male",
    "occupation": "farmer",
    "landholding": 2.5,
    "category": "OBC",
    "bpl": true
  },
  "total_schemes_evaluated": 5,
  "eligible_schemes_count": 4,
  "results": [
    {
      "scheme_id": "pm-kisan-001",
      "scheme_name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
      "short_description": "Central income support initiative providing ₹6,000 per year to landholding farmer families.",
      "match_score": 100.0,
      "eligible_status": true,
      "matched_rules": [
        {
          "field": "occupation",
          "operator": "in",
          "expected_value": "farmer,agriculture,cultivator",
          "actual_value": "farmer",
          "passed": true,
          "description": "Applicant must be a farmer or engaged in agriculture."
        },
        {
          "field": "landholding",
          "operator": "greater_than",
          "expected_value": "0.0",
          "actual_value": 2.5,
          "passed": true,
          "description": "Applicant family must possess cultivable agricultural land."
        }
      ],
      "failed_rules": [],
      "benefits": [
        "Direct income support of ₹6,000 per year transferred in 3 equal installments of ₹2,000",
        "100% Direct Benefit Transfer (DBT) into Aadhaar-seeded bank accounts"
      ],
      "required_documents": [
        "Aadhaar Card",
        "Proof of Agricultural Land Ownership (ROR / Khasra / Khatauni)",
        "Aadhaar-seeded Bank Account Passbook",
        "Active Mobile Number linked with Aadhaar"
      ],
      "official_source_url": "https://pmkisan.gov.in",
      "application_url": "https://pmkisan.gov.in/RegistrationFormNew.aspx"
    }
  ]
}
```

---

## 6. How to Run Locally

### 1. Backend Setup & Run

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Run Unit Tests**: `python -m tests.test_eligibility`

### 2. Frontend Setup & Run

```bash
cd frontend
npm install
npm run dev
```

- **Frontend Application**: [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## 7. Milestones Overview

- ✅ **Milestone 1**: Foundation & Service Integration (FastAPI, React 19, Tailwind, Axios, CORS, Health check).
- ✅ **Milestone 2**: Data Foundation & Deterministic YojanaMatch Eligibility Engine (Relational SQLAlchemy models, Pydantic schemas, rule evaluation engine, POST `/api/v1/eligibility/match`, testing UI).
- 📋 **Milestone 3**: NitiRAG (Grounded policy retrieval with gazette vector search).
- 📋 **Milestone 4**: KagazCheck (Multimodal document auditor & gap analysis).
- 📋 **Milestone 5**: Parchaa (Actionable application dossier generator).
