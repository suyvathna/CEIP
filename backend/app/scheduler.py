"""
The clock that drives Engine A (and, through it, Engine B's daily sweep).

An in-process APScheduler job rather than Celery or a separate worker
container, because the platform's whole infrastructure today is one
FastAPI process, one Postgres and one MinIO, and adding a broker plus a
worker to run one job a day would be a poor trade. The pieces that make
that choice safe live in compliance_service, not here:

  * A Postgres advisory lock, so N uvicorn workers all firing at 06:00
    produce one sweep rather than N.
  * Idempotent writes - obligations keyed on (project, rule, period),
    alerts on a dedupe key - so even if the lock were bypassed entirely,
    a duplicated run would change nothing.
  * A run ledger (compliance_runs), so a failed sweep leaves evidence
    instead of silence.

If a deployment later wants the sweep driven from system cron, a
Kubernetes CronJob or a cloud scheduler instead, set
CEIP_SCHEDULER_ENABLED=false and hit POST /compliance/tick on whatever
cadence suits. Nothing else changes.
"""

import logging

from app.core.config import settings
from app.db.database import SessionLocal
from app.services.compliance_service import run_daily_tick

logger = logging.getLogger(__name__)

_scheduler = None


def run_tick_job(trigger_source: str = "scheduled") -> None:
    """
    Job body. Owns its own database session - APScheduler runs this on a
    worker thread with no request context, so it cannot borrow the
    request-scoped session from get_db.
    """
    db = SessionLocal()
    try:
        run = run_daily_tick(db, trigger_source=trigger_source)

        if run is None:
            logger.info("Compliance sweep skipped - another worker holds the lock.")
        else:
            logger.info(
                "Compliance sweep %s: %s projects, %s obligations created, "
                "%s updated, %s alerts raised.",
                run.status,
                run.projects_processed,
                run.obligations_created,
                run.obligations_updated,
                run.notifications_created,
            )
    except Exception:  # noqa: BLE001 - a scheduler thread must not die
        logger.exception("Compliance sweep raised outside the tick's own handling")
    finally:
        db.close()


def start_scheduler() -> None:
    """
    Wire the daily job up. Called from the FastAPI lifespan hook.

    Deliberately forgiving: if APScheduler isn't installed, or the
    scheduler fails to start, the application still serves requests. The
    engines remain fully usable through POST /compliance/tick, and an API
    that refuses to boot because a background job couldn't be scheduled
    would be a much worse failure than a sweep that has to be triggered
    by hand.
    """
    global _scheduler

    if not getattr(settings, "scheduler_enabled", True):
        logger.info("Compliance scheduler disabled by configuration.")
        return

    if _scheduler is not None:
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning(
            "APScheduler is not installed - the compliance sweep will not run "
            "automatically. Install apscheduler, or drive POST /compliance/tick "
            "from an external scheduler."
        )
        return

    try:
        scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)

        scheduler.add_job(
            run_tick_job,
            trigger=CronTrigger(
                hour=settings.scheduler_hour,
                minute=settings.scheduler_minute,
                timezone=settings.scheduler_timezone,
            ),
            id="ceip_compliance_daily_tick",
            name="CEIP daily FIDIC compliance sweep",
            # A worker that was down at 06:00 still runs the sweep when it
            # comes back, as long as it's within the grace window - a
            # deployment during the morning window shouldn't cost a day's
            # alerting. coalesce collapses several missed firings into one.
            misfire_grace_time=60 * 60 * 6,
            coalesce=True,
            max_instances=1,
            replace_existing=True,
        )

        scheduler.start()
        _scheduler = scheduler

        logger.info(
            "Compliance scheduler started - daily at %02d:%02d %s.",
            settings.scheduler_hour,
            settings.scheduler_minute,
            settings.scheduler_timezone,
        )

        if getattr(settings, "scheduler_run_on_startup", False):
            # Off by default. Useful in development and after a long
            # outage; in production it means every rolling deploy fires a
            # sweep, which is harmless but noisy in the run ledger.
            scheduler.add_job(
                run_tick_job,
                id="ceip_compliance_startup_tick",
                name="CEIP compliance sweep (startup)",
                kwargs={"trigger_source": "startup"},
                replace_existing=True,
            )

    except Exception:  # noqa: BLE001 - see docstring
        logger.exception("Could not start the compliance scheduler")


def shutdown_scheduler() -> None:
    global _scheduler

    if _scheduler is None:
        return

    try:
        _scheduler.shutdown(wait=False)
    except Exception:  # noqa: BLE001
        logger.exception("Error shutting down the compliance scheduler")
    finally:
        _scheduler = None
