# OnboardAI Email + Camera/OCR Setup

## Email

The application now:
- loads `.env` from the project directory even when Uvicorn is started from another directory;
- trims copied quotes/whitespace from SMTP settings;
- removes spaces from Gmail App Passwords copied in grouped form;
- supports Gmail STARTTLS on port 587 and SSL on port 465;
- sends the document-received email immediately after the original upload is stored;
- keeps delivery failures in the Email Notifications audit page;
- provides an ADMIN-only **Send test email** button.

### Gmail settings

Use a Google **App Password**, not the normal Gmail account password:

```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_16_character_google_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

If using Gmail port 465 instead:

```env
SMTP_PORT=465
SMTP_USE_TLS=false
SMTP_USE_SSL=true
```

A persistent `535` from Gmail still means Gmail rejected the credentials. Create a new App Password for the exact `SMTP_USERNAME` account and use that value in `.env`.

## Camera document capture

Customers now have two options:
1. **Choose a document** — file picker with camera capture support on supported mobile browsers.
2. **Use camera** — opens the browser camera, prefers the rear/environment camera, shows a document frame, captures a JPEG, and sends it through the same upload/OCR pipeline.

Camera access requires browser permission and normally works on `localhost`/`127.0.0.1` during development or over HTTPS in production.

Accepted formats: PDF, PNG, JPG/JPEG, WEBP and TIFF. Maximum upload size: 15 MB.

The original image/file remains stored. OCR text is stored separately in the document record.

## Run

Backend:

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Copy `.env.example` to `.env` and fill in your own values. Do not commit `.env`.
