# Database migrations

The MVP ensures tables via `Base.metadata.create_all()` on startup and through
`backend/app/seed.py`. For production change management, initialise Alembic
against the SQLAlchemy models in `backend/app/models`:

```bash
pip install alembic
alembic init backend/migrations
# set sqlalchemy.url from DATABASE_URL and target_metadata = Base.metadata
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

Apply migrations in your release pipeline instead of `create_all` for
controlled schema evolution.
