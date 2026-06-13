"""
app/signals.py

Django signals that fire a background backup whenever a significant
model change occurs in Green Garden.

Covered events:
  ClientPersonalInfo  — created / updated / deleted
  ClientStatus        — plan assigned or updated
  Payment             — payment marked as paid
  Booking             — booking created or cancelled
  UserLog             — employee created / updated

The backup itself runs in a background thread (see backup.py) and
respects a cooldown, so many rapid saves only produce one backup.
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .backup import trigger_backup
from .models import Booking, ClientPersonalInfo, ClientStatus, Payment, UserLog


# ── ClientPersonalInfo ────────────────────────────────────────────────────────

@receiver(post_save, sender=ClientPersonalInfo)
def backup_on_client_save(sender, instance, created, **kwargs):
    trigger_backup("add_client" if created else "edit_client")


@receiver(post_delete, sender=ClientPersonalInfo)
def backup_on_client_delete(sender, instance, **kwargs):
    trigger_backup("delete_client")


# ── ClientStatus (plan assignment / cancellation) ─────────────────────────────

@receiver(post_save, sender=ClientStatus)
def backup_on_plan_save(sender, instance, created, **kwargs):
    trigger_backup("add_plan" if created else "update_plan")


# ── Payment ───────────────────────────────────────────────────────────────────

@receiver(post_save, sender=Payment)
def backup_on_payment_save(sender, instance, created, **kwargs):
    if instance.is_paid:
        trigger_backup("payment_paid")


# ── Booking ───────────────────────────────────────────────────────────────────

@receiver(post_save, sender=Booking)
def backup_on_booking_save(sender, instance, created, **kwargs):
    if created:
        trigger_backup("add_booking")
    elif instance.status == "Cancelled":
        trigger_backup("cancel_booking")


# ── UserLog (employee management) ─────────────────────────────────────────────

@receiver(post_save, sender=UserLog)
def backup_on_employee_save(sender, instance, created, **kwargs):
    trigger_backup("add_employee" if created else "edit_employee")


@receiver(post_delete, sender=UserLog)
def backup_on_employee_delete(sender, instance, **kwargs):
    trigger_backup("delete_employee")
