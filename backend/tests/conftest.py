"""
Test bootstrap.

app.core.config.Settings has no defaults for the database, MinIO and JWT
values, so importing anything that reaches app.db.database explodes on a
machine with no .env - which is every CI runner. The engine tests below
are pure date and rule logic and never open a connection, but Python's
import graph doesn't care about that, so placeholder values go into the
environment before any app module is imported.

Deliberately obvious junk values: if one of these ever ends up in a real
connection attempt, the failure should be loud and unmistakable rather
than quietly pointing at something real.
"""

import os

os.environ.setdefault("DATABASE_HOST", "test-host-not-used")
os.environ.setdefault("DATABASE_PORT", "5432")
os.environ.setdefault("DATABASE_NAME", "test-db-not-used")
os.environ.setdefault("DATABASE_USER", "test-user-not-used")
os.environ.setdefault("DATABASE_PASSWORD", "test-password-not-used")
os.environ.setdefault("MINIO_ENDPOINT", "test-minio-not-used:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "test-access-key-not-used")
os.environ.setdefault("MINIO_SECRET_KEY", "test-secret-key-not-used")
os.environ.setdefault("MINIO_BUCKET", "test-bucket-not-used")
os.environ.setdefault("MINIO_SECURE", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-used-in-any-real-signing")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("SCHEDULER_ENABLED", "false")
