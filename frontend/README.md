# OnboardAI KYC Frontend

React + Vite frontend for the uploaded FastAPI Agentic KYC backend.

## Run

1. Keep the FastAPI backend running on `http://127.0.0.1:8000`.
2. In this folder:

```bash
npm install
npm run dev
```

3. Open the Vite URL, normally `http://localhost:5173`.

The backend already allows this origin through CORS.

## Included screens

- Operations overview dashboard
- KYC case list and search
- Case detail with:
  - customer profile
  - identity / risk / decision outputs
  - documents
  - document upload
  - evidence ledger
  - audit timeline
  - human review approval / rejection
- Customer directory
- Create customer + start a KYC case

## API

The frontend uses the existing endpoints under:

- `/api/customers`
- `/api/cases`
- `/api/documents`
- `/api/evidence`
- `/api/audit`
- `/api/reviews`
