# Database migrations

Schema initialization remains backward-compatible in `services/database.py` for the prototype. This directory is the migration boundary for production Alembic migrations.

Before production, generate an initial revision from the desired SQLAlchemy schema and run migrations in CI/CD rather than relying on `CREATE TABLE IF NOT EXISTS`.
