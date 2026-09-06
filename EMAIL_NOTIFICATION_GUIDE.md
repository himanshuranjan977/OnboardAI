# OnboardAI Email Notifications

## What is implemented

1. **Registration success email**: after `POST /api/customers` successfully creates a customer, a welcome email is sent with a stable display Customer ID such as `CUST-000123`.
2. **KYC completion email**: when the existing workflow reaches `APPROVED`, the customer receives a KYC completion email containing the customer ID and KYC case number.

The existing KYC workflow is unchanged. Email is a best-effort side effect: SMTP errors are logged and do not fail registration or KYC approval.

## Configure SMTP

Copy the email variables from `.env.example` into `.env` and set:

- `EMAIL_ENABLED=true`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD` (use an app password/provider credential, not a normal password)
- `SMTP_FROM_EMAIL`
- `SMTP_USE_TLS=true`

The service uses Python's standard `smtplib`, so no additional email package is required.

## Flow

Registration → customer stored → registration email

Existing KYC agents → Decision Agent → APPROVED → case status updated → KYC completion email
