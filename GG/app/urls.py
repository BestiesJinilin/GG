from django.urls import path
from . import views

urlpatterns = [
    # ── auth ──────────────────────────────────────────────────────────────
    path("",                          views.login_view,              name="login"),
    path("login/",                    views.login_view,              name="login"),
    path("logout/",                   views.logout,                  name="logout"),

    # ── dashboard ─────────────────────────────────────────────────────────
    path("homepage/",                 views.homepage_view,           name="homepage"),

    # ── clients ───────────────────────────────────────────────────────────
    path("add-client/",               views.add_client_view,         name="add-client"),
    path("records/",                  views.records_view,            name="records"),
    path("client-details/<int:pk>/",  views.client_details_view,     name="client-details"),
    path("edit-details/<int:pk>/",    views.edit_details_view,       name="edit-details"),
    path("delete-client/<int:pk>/",   views.delete_client_view,      name="delete-client"),

    # ── payments ──────────────────────────────────────────────────────────
    path("add-payment/<int:pk>/",     views.add_payment_view,        name="add-payment"),
    path("payment-history/<int:pk>/", views.payment_history_view,    name="payment-history"),

    # ── plan / lots ───────────────────────────────────────────────────────
    path("plan/<int:pk>/",            views.plan,                    name="plan"),
    path("cancel-plan/<int:pk>/",     views.cancel_plan_view,        name="cancel-plan"),   # NEW
    path("lots/",                     views.lots_view,               name="lots"),

    # ── bookings / calendar ───────────────────────────────────────────────
    path("bookings/",                 views.bookings_view,           name="bookings"),
    path("cancel-booking/<int:pk>/",  views.cancel_booking_view,     name="cancel-booking"), # NEW
    path("calendar/",                 views.calendar_view,           name="calendar"),

    # ── employees ─────────────────────────────────────────────────────────
    path("employee/",                       views.employee_view,           name="employee"),
    path("add-employee/",                   views.add_employee_view,       name="add-employee"),
    path("details-employee/<int:pk>/",      views.details_employee_view,   name="details-employee"),
    path("edit-employee/<int:pk>/",         views.edit_employee_view,      name="edit-employee"),
    path("delete-employee/<int:pk>/",       views.delete_employee_view,    name="delete-employee"),

    # ── monitor ───────────────────────────────────────────────────────────
    path("monitor/",                  views.monitor_view,            name="monitor"),

    # ── system / backup (admin only) ──────────────────────────────────────────
    path("system/backup/",        views.backup_now_view,    name="backup-now"),
    path("system/backup/status/", views.backup_status_view, name="backup-status"),

     # ── exports ───────────────────────────────────────────────────────────────
    path("export/bookings/",               views.export_bookings_excel,        name="export-bookings"),
    path("export/payment-history/<int:pk>/", views.export_payment_history_excel, name="export-payment-history"),
    path("export/lots/",                   views.export_lots_excel,             name="export-lots"),
    path("export/records/",                views.export_records_excel,          name="export-records"),

    # ── system/settings ──────────────────────────────────────────
    path("system/settings/", views.system_settings_view, name="system-settings"),
]
