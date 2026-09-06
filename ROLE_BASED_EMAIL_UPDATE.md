# OnboardAI Role-Based + Email Update

## What remains unchanged
The original App KYC backend, SQLite schema for customers/cases/documents/evidence/audit/human reviews, Groq client, existing agents, orchestration and React workflow remain the primary process.

## Added authentication
- Customer registration and login.
- Signed bearer access tokens.
- PBKDF2 password hashing using Python stdlib.
- Roles: CUSTOMER, ANALYST, QA, ADMIN.
- Customer data/case/document/evidence access is ownership-scoped.
- KYC execution, case status changes, document status changes and human review are staff-only.
- Admin-only user role and account activation management.

## Added email service
- Registration-success email includes the Customer ID.
- Successful KYC approval email includes Customer ID and KYC case number.
- Email delivery is best-effort and never breaks KYC processing.
- Every email attempt is recorded in `email_notifications` as SENT, FAILED or DISABLED.
- Staff can inspect `/api/notifications/emails`; Admin gets an Email Notifications page in the React UI.

## Environment
Copy `.env.example` to `.env` and set your Groq key, authentication secret and SMTP settings. For Gmail, use an App Password rather than your normal account password.

Optional first admin bootstrap:
`ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_FULL_NAME`.

## Frontend
The existing React dashboard and process are preserved. A login/register gate, role-aware navigation, customer profile, Admin User Management and Admin Email Notifications pages were added.
