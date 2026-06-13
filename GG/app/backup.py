"""
app/backup.py  — Green Garden Backup System (Revised)

Each backup produces a timestamped ZIP archive containing:
  clients.csv        — ClientPersonalInfo
  beneficiaries.csv  — Beneficiary
  plans.csv          — ClientStatus
  payments.csv       — Payment
  bookings.csv       — Booking
  employees.csv      — UserLog
  activity_logs.csv  — ActivityLog
  db.sqlite3         — raw database copy (for full restore)

Local path : GG/backups/          (inside the project, easy access)
Cloud      : Dropbox via API      (token from environment variable)

Manual trigger:
  python manage.py backup_now
"""

import csv
import datetime
import io
import logging
import threading
import zipfile
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

_backup_lock: threading.Lock = threading.Lock()
_last_backup_time: datetime.datetime | None = None


# ─────────────────────────────── helpers ──────────────────────────────────────

def _is_on_cooldown() -> bool:
    global _last_backup_time
    cooldown = getattr(settings, "BACKUP_COOLDOWN_MINUTES", 15)
    if _last_backup_time is None:
        return False
    elapsed = (datetime.datetime.now() - _last_backup_time).total_seconds() / 60
    return elapsed < cooldown


def _v(value):
    """Safely stringify any value for CSV output."""
    if value is None:
        return ""
    return str(value)


def _write_csv(zipf: zipfile.ZipFile, filename: str, headers: list, rows) -> None:
    """Write a list of rows as a CSV file into the zip archive."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_v(cell) for cell in row])
    zipf.writestr(filename, buf.getvalue())


# ─────────────────────────────── build zip ────────────────────────────────────

def _build_zip(db_path: Path) -> tuple[bytes, str]:
    """
    Build the organized ZIP backup.
    Returns (zip_bytes, timestamp_str).
    Lazy imports avoid circular import issues at startup.
    """
    from .models import (
        ActivityLog, Beneficiary, Booking,
        ClientPersonalInfo, ClientStatus, Payment, UserLog,
    )

    ts  = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        # ── 1. Clients ─────────────────────────────────────────────────────
        _write_csv(
            zf, "clients.csv",
            [
                "id", "first_name", "middle_name", "last_name",
                "address", "contact_number", "civil_status", "date_birth",
                "religion", "occupation", "employer_name", "employer_address",
                "spouse_name", "spouse_date_birth", "spouse_occupation", "spouse_employer",
                "id_type", "id_number", "date_issued", "place_issued",
            ],
            [
                (
                    c.pk, c.client_first_name, c.client_middle_name, c.client_last_name,
                    c.client_address, c.client_contact_number, c.client_civil_status,
                    c.client_date_birth, c.client_religion, c.client_occupation,
                    c.client_employer_name, c.client_employer_address,
                    c.client_spouse_name, c.client_spouse_date_birth,
                    c.client_spouse_occupation, c.client_spouse_employer,
                    c.client_id_type, c.client_id_number,
                    c.client_date_issued, c.client_place_issued,
                )
                for c in ClientPersonalInfo.objects.all().order_by("pk")
            ],
        )

        # ── 2. Beneficiaries ───────────────────────────────────────────────
        _write_csv(
            zf, "beneficiaries.csv",
            ["id", "client_id", "client_name", "beneficiary_name", "relationship"],
            [
                (b.pk, b.client_id, b.client.full_name, b.name, b.relationship)
                for b in Beneficiary.objects.select_related("client").order_by("client_id", "pk")
            ],
        )

        # ── 3. Plans (ClientStatus) ────────────────────────────────────────
        _write_csv(
            zf, "plans.csv",
            [
                "id", "client_id", "client_name", "plan",
                "monthly_payment", "duration", "months_remaining",
                "start_date", "balance", "paid_balance",
                "down_payment", "discount_percent",
                "phase", "block", "section", "lot_number", "pa_number",
                "contract_number", "interment_date", "pa_date", "date_fully_paid",
                "column_level", "columbarium_type", "columbarium_level", "tomb_number",
                "status", "is_cancelled", "cancellation_reason", "cancellation_date",
            ],
            [
                (
                    cs.pk, cs.client_id, cs.client.full_name, cs.plan,
                    cs.monthly_payment, cs.duration, cs.months_remaining,
                    cs.start_date, cs.balance, cs.paid_balance,
                    cs.down_payment, cs.discount_percent,
                    cs.phase, cs.block, cs.section, cs.lot_number, cs.pa_number,
                    cs.contract_number, cs.interment_date, cs.pa_date, cs.date_fully_paid,
                    cs.column_level, cs.columbarium_type, cs.columbarium_level, cs.tomb_number,
                    cs.status, cs.is_cancelled, cs.cancellation_reason, cs.cancellation_date,
                )
                for cs in ClientStatus.objects.select_related("client").order_by("pk")
            ],
        )

        # ── 4. Payments ────────────────────────────────────────────────────
        _write_csv(
            zf, "payments.csv",
            [
                "id", "client_status_id", "client_name", "plan",
                "month", "amount", "is_paid", "date_paid", "processed_by",
            ],
            [
                (
                    p.pk, p.client_status_id,
                    p.client_status.client.full_name,
                    p.client_status.plan,
                    p.month, p.amount, p.is_paid, p.date_paid,
                    (p.processed_by.username if p.processed_by else ""),
                )
                for p in Payment.objects
                    .select_related("client_status__client", "processed_by")
                    .order_by("client_status_id", "month")
            ],
        )

        # ── 5. Bookings ────────────────────────────────────────────────────
        _write_csv(
            zf, "bookings.csv",
            [
                "id", "client_name", "contact_number", "event_type",
                "booking_date", "booking_time", "notes",
                "status", "cancellation_reason", "cancelled_at", "created_at",
            ],
            [
                (
                    b.pk, b.client_name, b.contact_number, b.event_type,
                    b.booking_date, b.get_booking_time_display(), b.notes,
                    b.status, b.cancellation_reason, b.cancelled_at, b.created_at,
                )
                for b in Booking.objects.all().order_by("booking_date", "booking_time")
            ],
        )

        # ── 6. Employees ───────────────────────────────────────────────────
        _write_csv(
            zf, "employees.csv",
            [
                "id", "username", "role",
                "first_name", "middle_name", "last_name",
                "date_of_birth", "address", "phone_number", "email",
                "emergency_contact_name", "emergency_contact_number",
                "government_id", "time_in", "time_out", "last_activity",
            ],
            [
                (
                    e.pk,
                    (e.user.username if e.user else ""),
                    e.role, e.first_name, e.middle_name, e.last_name,
                    e.date_of_birth, e.address, e.phone_number, e.email,
                    e.emergency_contact_name, e.emergency_contact_number,
                    e.government_id, e.time_in, e.time_out, e.activities,
                )
                for e in UserLog.objects.select_related("user").order_by("pk")
            ],
        )

        # ── 7. Activity Logs ───────────────────────────────────────────────
        _write_csv(
            zf, "activity_logs.csv",
            ["id", "staff_name", "role", "action", "detail", "timestamp"],
            [
                (a.pk, a.staff_name, a.role, a.action, a.detail, a.timestamp)
                for a in ActivityLog.objects.all().order_by("timestamp")
            ],
        )

        # ── 8. Raw database (for full restore if needed) ───────────────────
        zf.write(str(db_path), arcname="db.sqlite3")

    return buf.getvalue(), ts


# ─────────────────────────────── offline (local) ──────────────────────────────

def _get_offline_dir() -> Path:
    """
    Default: GG/backups/ — inside the project folder for easy access.
    Override with BACKUP_OFFLINE_DIR in settings.
    """
    default = settings.BASE_DIR / "backups"
    return Path(getattr(settings, "BACKUP_OFFLINE_DIR", str(default)))


def _save_offline(zip_bytes: bytes, filename: str) -> bool:
    directory = _get_offline_dir()
    try:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / filename).write_bytes(zip_bytes)
        logger.info("[Backup] Local saved → %s", directory / filename)
        return True
    except Exception as exc:
        logger.error("[Backup] Local save failed: %s", exc)
        return False


def _cleanup_offline() -> None:
    retention = getattr(settings, "BACKUP_RETENTION_DAYS", 90)
    cutoff    = datetime.datetime.now() - datetime.timedelta(days=retention)
    directory = _get_offline_dir()
    if not directory.exists():
        return
    for f in directory.glob("backup_*.zip"):
        try:
            mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                f.unlink()
                logger.info("[Backup] Deleted old local backup: %s", f.name)
        except Exception as exc:
            logger.warning("[Backup] Could not delete %s: %s", f, exc)


# ─────────────────────────────── cloud (Dropbox) ──────────────────────────────

def _upload_to_dropbox(zip_bytes: bytes, filename: str) -> bool:
    token = getattr(settings, "DROPBOX_ACCESS_TOKEN", None)
    if not token:
        logger.warning("[Backup] DROPBOX_ACCESS_TOKEN not configured — cloud backup skipped.")
        return False
    try:
        import dropbox
        from dropbox.files import WriteMode

        folder      = getattr(settings, "DROPBOX_BACKUP_FOLDER", "/GreenGardenBackups")
        remote_path = f"{folder.rstrip('/')}/{filename}"

        with dropbox.Dropbox(token) as dbx:
            # Quick auth check before uploading
            dbx.users_get_current_account()
            dbx.files_upload(zip_bytes, remote_path, mode=WriteMode.overwrite)

        logger.info("[Backup] Dropbox uploaded → %s", remote_path)
        return True

    except ImportError:
        logger.error("[Backup] 'dropbox' package not installed. Run: pip install dropbox")
        return False
    except Exception as exc:
        logger.error("[Backup] Dropbox upload failed: %s", exc)
        return False


def _cleanup_dropbox() -> None:
    token = getattr(settings, "DROPBOX_ACCESS_TOKEN", None)
    if not token:
        return
    try:
        import dropbox
        from dropbox.files import FileMetadata

        retention = getattr(settings, "BACKUP_RETENTION_DAYS", 90)
        cutoff    = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=retention)
        folder    = getattr(settings, "DROPBOX_BACKUP_FOLDER", "/GreenGardenBackups")

        with dropbox.Dropbox(token) as dbx:
            try:
                result = dbx.files_list_folder(folder)
            except dropbox.exceptions.ApiError:
                return  # folder doesn't exist yet
            for entry in result.entries:
                if isinstance(entry, FileMetadata) and entry.client_modified < cutoff:
                    dbx.files_delete_v2(entry.path_lower)
                    logger.info("[Backup] Deleted old Dropbox backup: %s", entry.name)
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("[Backup] Dropbox cleanup failed: %s", exc)


# ─────────────────────────────── core ─────────────────────────────────────────

def _do_backup(trigger: str, force: bool = False) -> dict:
    """
    Build + save backup. Returns a status dict.
    force=True bypasses the cooldown (used for manual backups).
    """
    global _last_backup_time

    with _backup_lock:
        if not force and _is_on_cooldown():
            logger.debug("[Backup] Skipped — cooldown active.")
            return {"success": False, "reason": "cooldown"}

        db_path = Path(settings.DATABASES["default"]["NAME"])
        if not db_path.exists():
            logger.warning("[Backup] Database not found: %s", db_path)
            return {"success": False, "reason": "db_not_found"}

        try:
            zip_bytes, ts = _build_zip(db_path)
        except Exception as exc:
            logger.error("[Backup] Failed to build archive: %s", exc)
            return {"success": False, "reason": str(exc)}

        filename   = f"backup_{ts}_{trigger}.zip"
        offline_ok = _save_offline(zip_bytes, filename)
        cloud_ok   = _upload_to_dropbox(zip_bytes, filename)

        if not offline_ok and not cloud_ok:
            return {"success": False, "reason": "all_destinations_failed"}

        _last_backup_time = datetime.datetime.now()
        _cleanup_offline()
        _cleanup_dropbox()

        return {
            "success":  True,
            "filename": filename,
            "offline":  offline_ok,
            "cloud":    cloud_ok,
            "path":     str(_get_offline_dir() / filename),
        }


def trigger_backup(trigger: str = "activity") -> None:
    """Async trigger used by Django signals. Fire-and-forget."""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in trigger)[:30]
    threading.Thread(
        target=_do_backup,
        args=(safe,),
        kwargs={"force": False},
        daemon=True,
        name=f"gg-backup-{safe}",
    ).start()


def trigger_manual_backup() -> dict:
    """
    Synchronous manual backup — bypasses cooldown.
    Called by: python manage.py backup_now
    """
    return _do_backup("manual", force=True)