import sqlite3
from pathlib import Path


DATABASE_PATH = Path("onboardai.db")


def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False,
        timeout=30,
    )

    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # ==========================================
    # CUSTOMERS
    # ==========================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            date_of_birth TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ==========================================
    # KYC CASES
    # ==========================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_number TEXT NOT NULL UNIQUE,

            customer_id INTEGER NOT NULL,

            status TEXT NOT NULL DEFAULT 'CREATED',

            risk_level TEXT,

            risk_score INTEGER,

            decision TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (customer_id)
                REFERENCES customers(id)
        )
        """
    )

    # ==========================================
    # DOCUMENTS
    # ==========================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id INTEGER NOT NULL,

            document_type TEXT NOT NULL,

            file_name TEXT NOT NULL,

            file_path TEXT NOT NULL,

            mime_type TEXT,

            status TEXT NOT NULL DEFAULT 'UPLOADED',

            extraction_status TEXT DEFAULT 'PENDING',

            confidence REAL,

            extracted_data TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (case_id)
                REFERENCES cases(id)
        )
        """
    )

    # ==========================================
    # EVIDENCE
    # ==========================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id INTEGER NOT NULL,

            document_id INTEGER,

            agent_name TEXT NOT NULL,

            evidence_type TEXT NOT NULL,

            field_name TEXT,

            source TEXT,

            customer_value TEXT,

            document_value TEXT,

            result TEXT,

            confidence REAL,

            explanation TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (case_id)
                REFERENCES cases(id),

            FOREIGN KEY (document_id)
                REFERENCES documents(id)
        )
        """
    ) 

    # ==========================================
    # AUDIT EVENTS
    # ==========================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id INTEGER NOT NULL,

            agent_name TEXT,

            event_type TEXT NOT NULL,

            event_message TEXT,

            event_data TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (case_id)
                REFERENCES cases(id)
        )
        """
    ) 

    # ==========================================
    # HUMAN REVIEWS
    # ==========================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS human_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id INTEGER NOT NULL,

            status TEXT NOT NULL,

            decision TEXT,

            reviewer_name TEXT,

            reviewer_comment TEXT,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (case_id)
                REFERENCES cases(id)
        )
        """
    )


    # ==========================================
    # USERS / AUTHENTICATION
    # ==========================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            phone TEXT,
            date_of_birth TEXT,
            address TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'CUSTOMER',
            active INTEGER NOT NULL DEFAULT 1,
            customer_id INTEGER UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
        """
    )

    # ==========================================
    # EMAIL NOTIFICATION AUDIT
    # ==========================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS email_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            case_id INTEGER,
            recipient_email TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            subject TEXT NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
        """
    )


    # ==========================================
    # TARGET ARCHITECTURE / DURABLE WORKFLOW
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_key TEXT NOT NULL UNIQUE,
            job_type TEXT NOT NULL,
            case_id INTEGER NOT NULL,
            document_id INTEGER,
            status TEXT NOT NULL DEFAULT 'QUEUED',
            attempts INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3,
            payload TEXT,
            result TEXT,
            error_message TEXT,
            locked_at TIMESTAMP,
            available_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases(id),
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_jobs_status ON workflow_jobs(status, available_at)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            job_id INTEGER,
            current_agent TEXT,
            workflow_status TEXT,
            state_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases(id),
            FOREIGN KEY (job_id) REFERENCES workflow_jobs(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_snapshots_case ON workflow_snapshots(case_id, id DESC)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            status TEXT NOT NULL,
            duration_ms REAL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_events_case ON agent_events(case_id, id)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_explanations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL UNIQUE,
            provider TEXT NOT NULL,
            explanation TEXT NOT NULL,
            model_version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            sanctions_result TEXT,
            pep_result TEXT,
            adverse_media_result TEXT,
            provider TEXT,
            manual_review_required INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            alerts TEXT,
            severity TEXT,
            manual_review_required INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policy_versions (
            version TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_key TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            content TEXT NOT NULL,
            version TEXT NOT NULL DEFAULT '1.0',
            approved INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO policy_versions(version, description, active)
        VALUES('2.0-TARGET', 'Deterministic KYC policy with screening, anomaly and human-review gates.', 1)
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO knowledge_documents(document_key,title,source,content,version,approved)
        VALUES(?,?,?,?,?,1)
    """, ('approved-policy-1','Approved KYC Review Policy','ONBOARDAI_POLICY',
           'Medium/high risk, unresolved identity, screening matches, document exceptions and anomaly alerts require human review. LLM output is assistive only and cannot override deterministic policy or human review.', '1.0'))


    connection.commit()

    connection.close()