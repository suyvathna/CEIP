from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Database
    database_host: str
    database_port: int
    database_name: str
    database_user: str
    database_password: str

    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    minio_secure: bool = False

    # Security
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # --- Engine A scheduler -----------------------------------------
    # All defaulted, so an existing .env keeps working untouched.
    #
    # Set scheduler_enabled=false to drive the sweep from system cron, a
    # Kubernetes CronJob or a cloud scheduler hitting POST
    # /compliance/tick instead - that endpoint is idempotent and takes
    # the same advisory lock, so nothing else needs to change.
    scheduler_enabled: bool = True

    # 06:00 project-local: early enough that a PM sees the day's
    # deadlines before site work starts, late enough that overnight
    # database maintenance has finished.
    scheduler_hour: int = 6
    scheduler_minute: int = 0

    # Matches the timezone the deadline maths already anchors to (see
    # notice_deadline_service). A server running in UTC would otherwise
    # run the "daily" sweep at 1pm Cambodian time.
    scheduler_timezone: str = "Asia/Phnom_Penh"

    # Off by default: with rolling deploys this fires a sweep on every
    # restart, which is harmless but clutters the run ledger. Handy in
    # development, and after a long outage.
    scheduler_run_on_startup: bool = False

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        # Ignore unrelated variables in a shared .env rather than
        # refusing to boot over one.
        extra="ignore",
    )


settings = Settings()