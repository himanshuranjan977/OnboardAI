# Role-Based Security Integration

The existing App backend remains the source of truth for the KYC process. Authentication and authorization are additive.

## Roles
- CUSTOMER: only their own profile, cases, documents and evidence; can create their own case and upload documents.
- ANALYST: operational KYC access and workflow execution.
- QA: operational KYC access, workflow execution and human review.
- ADMIN: full access plus user management and email delivery audit.

## Authentication
- `POST /api/auth/register` creates a CUSTOMER user and linked customer record.
- `POST /api/auth/login` returns a signed bearer token.
- `GET /api/auth/me` returns the authenticated user.
- Tokens use HMAC-SHA256 and PBKDF2 password hashing implemented with the Python standard library.

## Email audit
Every registration and KYC-completion notification creates a row in `email_notifications` with SENT, FAILED or DISABLED status. Email errors are best-effort and never change a KYC decision.

## Bootstrap admin
Set `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` and optionally `ADMIN_FULL_NAME` in `.env`. On startup, an administrator is created if that username/email does not already exist.
