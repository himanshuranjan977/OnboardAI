# Production database adapter

The current app remains SQLite-compatible. `production_db` adds a SQLAlchemy boundary for a PostgreSQL migration without coupling agents to the database engine.

Example: `DATABASE_URL=postgresql+psycopg://user:password@host:5432/onboardai`

Use Alembic in the production environment for schema migrations.
