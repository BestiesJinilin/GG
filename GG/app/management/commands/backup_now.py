"""
app/management/commands/backup_now.py

Usage:
  python manage.py backup_now

Triggers a full organized backup immediately, bypassing the cooldown.
Prints the result to the console including file path.
"""

from django.core.management.base import BaseCommand

from app.backup import trigger_manual_backup


class Command(BaseCommand):
    help = "Trigger a full manual backup immediately (bypasses cooldown)"

    def handle(self, *args, **options):
        self.stdout.write("Starting manual backup...")

        result = trigger_manual_backup()

        if result.get("success"):
            self.stdout.write(self.style.SUCCESS(
                f"\n✓  Backup complete: {result['filename']}"
                f"\n   Local  : {'✓ saved' if result.get('offline') else '✗ failed'}"
                f"\n   Cloud  : {'✓ uploaded' if result.get('cloud') else '✗ skipped/failed'}"
                f"\n   Path   : {result.get('path', '—')}"
            ))
        else:
            reason = result.get("reason", "unknown")
            self.stdout.write(self.style.ERROR(
                f"\n✗  Backup failed — reason: {reason}"
            ))