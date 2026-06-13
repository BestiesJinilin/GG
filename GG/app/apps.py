"""
app/apps.py

Starts two background systems when Django launches:
  1. Signal handlers  — auto-backup on every major data change
  2. Daily scheduler  — guaranteed backup once per day at 6:00 PM

No Task Scheduler, no cron, no extra packages needed.
Everything runs inside the Django process automatically.
"""

import datetime
import logging
import os
import sys
import threading
import time

from django.apps import AppConfig

logger = logging.getLogger(__name__)


# ─────────────────────────────── Daily Scheduler ──────────────────────────────

def _daily_backup_loop(hour: int = 18, minute: int = 0) -> None:
    """
    Daemon thread — sleeps until the target time, fires a backup, then repeats.
    Runs inside the Django process so no external scheduler is needed.
    """
    logger.info(
        "[Scheduler] Daily backup scheduler active — fires every day at %02d:%02d",
        hour, minute,
    )

    while True:
        now    = datetime.datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If today's target already passed, schedule for tomorrow
        if now >= target:
            target += datetime.timedelta(days=1)

        sleep_secs = (target - now).total_seconds()
        logger.info(
            "[Scheduler] Next daily backup in %.0f min — scheduled for %s",
            sleep_secs / 60,
            target.strftime("%b %d, %Y %I:%M %p"),
        )

        time.sleep(sleep_secs)

        # Fire the backup
        try:
            from .backup import trigger_manual_backup
            result = trigger_manual_backup()
            if result.get("success"):
                logger.info(
                    "[Scheduler] Daily backup complete ✓ — %s  (local=%s, cloud=%s)",
                    result.get("filename"),
                    result.get("offline"),
                    result.get("cloud"),
                )
            else:
                logger.warning(
                    "[Scheduler] Daily backup failed — reason: %s",
                    result.get("reason"),
                )
        except Exception as exc:
            logger.error("[Scheduler] Daily backup error: %s", exc)


def _start_daily_scheduler() -> None:
    """
    Spawn the scheduler thread.
    Reads BACKUP_DAILY_HOUR / BACKUP_DAILY_MINUTE from settings if set,
    otherwise defaults to 18:00 (6:00 PM).
    """
    try:
        from django.conf import settings
        hour   = getattr(settings, "BACKUP_DAILY_HOUR",   18)
        minute = getattr(settings, "BACKUP_DAILY_MINUTE",  0)
    except Exception:
        hour, minute = 18, 0

    t = threading.Thread(
        target=_daily_backup_loop,
        kwargs={"hour": hour, "minute": minute},
        daemon=True,         # dies automatically when the server stops
        name="gg-daily-backup-scheduler",
    )
    t.start()
    logger.info("[Scheduler] Background daily backup thread started.")


# ─────────────────────────────── App Config ───────────────────────────────────

class AppAppConfig(AppConfig):
    name = "app"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        # ── 1. Connect signal handlers (auto-backup on data changes) ──────────
        import app.signals  # noqa: F401

        # ── 2. Start the daily backup scheduler ───────────────────────────────
        #
        # Guard: Django's dev server runs ready() twice — once for the file
        # watcher (outer process) and once for the actual worker (inner process,
        # RUN_MAIN='true'). We only want ONE scheduler thread running.
        #
        # In production (--noreload / waitress / gunicorn) ready() runs once
        # and RUN_MAIN is not set, so we also start the scheduler there.
        #
        in_dev_worker   = os.environ.get("RUN_MAIN") == "true"
        in_dev_reloader = "runserver" in sys.argv and not in_dev_worker
        in_production   = "runserver" not in sys.argv   # waitress / gunicorn

        if in_dev_worker or in_production:
            _start_daily_scheduler()