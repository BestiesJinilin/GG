from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import datetime

from .models import ClientPersonalInfo, ClientStatus, Beneficiary, UserLog, Payment
from .forms import ClientForm, BeneficiaryFormSet


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect("homepage")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")
    return render(request, "app/login.html")


@login_required(login_url="login")
@require_POST
def logout(request):
    auth.logout(request)
    return redirect("login")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def homepage_view(request):
    clients          = ClientPersonalInfo.objects.all()
    active_status    = ClientStatus.objects.filter(status=True).count()
    total_clients    = clients.count()
    collected        = sum(ClientStatus.objects.values_list("paid_balance", flat=True))
    pending_payments = sum(ClientStatus.objects.values_list("months_remaining", flat=True))

    return render(request, "app/homepage.html", {
        "client":           clients,
        "total_clients":    total_clients,
        "collected":        collected,
        "active_status":    active_status,
        "pending_payments": pending_payments,
    })


# ---------------------------------------------------------------------------
# Clients — CREATE
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def add_client_view(request):
    if request.method == "POST":
        form                = ClientForm(request.POST)
        beneficiary_formset = BeneficiaryFormSet(request.POST, prefix="beneficiaries")

        form_valid    = form.is_valid()
        formset_valid = beneficiary_formset.is_valid()

        if form_valid and formset_valid:
            client = form.save(commit=False)

            # Duplicate check
            if ClientPersonalInfo.objects.filter(
                client_first_name__iexact=client.client_first_name,
                client_last_name__iexact=client.client_last_name,
                client_date_birth=client.client_date_birth,
            ).exists():
                form.add_error(None, "A client with this name and date of birth already exists.")
                return render(request, "app/addclient.html", {
                    "form": form,
                    "beneficiary_formset": beneficiary_formset,
                })

            with transaction.atomic():
                client.save()
                beneficiary_formset.instance = client
                beneficiary_formset.save()

                today    = datetime.date.today()

                client_status = ClientStatus.objects.create(
                    client=client,
                    plan= "No Plan",
                    monthly_payment=0,
                    duration=0,
                    months_remaining=0,
                    start_date= today,
                    balance=0,
                    paid_balance=0.00,
                    status=False,
                )
                _generate_payment_rows(client_status)

            messages.success(request, f"Client '{client.full_name()}' added successfully.")
            return redirect("records")

    else:
        form                = ClientForm()
        beneficiary_formset = BeneficiaryFormSet(prefix="beneficiaries")

    return render(request, "app/addclient.html", {
        "form": form,
        "beneficiary_formset": beneficiary_formset,
    })


# ---------------------------------------------------------------------------
# Clients — READ list
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def records_view(request):
    query   = request.GET.get("q", "").strip()
    clients = ClientPersonalInfo.objects.all().order_by(
        "client_last_name", "client_first_name"
    )

    if query:
        clients = clients.filter(
            Q(client_first_name__icontains=query)     |
            Q(client_middle_name__icontains=query)    |
            Q(client_last_name__icontains=query)      |
            Q(client_contact_number__icontains=query) |
            Q(client_civil_status__icontains=query)   |
            Q(clientstatus__plan__icontains=query)
        ).distinct()

    return render(request, "app/records.html", {"client": clients, "query": query})


# ---------------------------------------------------------------------------
# Clients — READ detail
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def client_details_view(request, pk):
    client        = get_object_or_404(ClientPersonalInfo, pk=pk)
    client_status = ClientStatus.objects.filter(client=client).first()
    return render(request, "app/client-details.html", {
        "client":        client,
        "client_status": client_status,
    })


# ---------------------------------------------------------------------------
# Clients — UPDATE
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def edit_details_view(request, pk):
    client = get_object_or_404(ClientPersonalInfo, pk=pk)

    if request.method == "POST":
        form                = ClientForm(request.POST, instance=client)
        beneficiary_formset = BeneficiaryFormSet(
            request.POST, instance=client, prefix="beneficiaries"
        )

        # BUG FIX: evaluate both so both sets of errors are collected
        form_valid    = form.is_valid()
        formset_valid = beneficiary_formset.is_valid()

        if form_valid and formset_valid:
            with transaction.atomic():
                form.save()
                beneficiary_formset.save()
            messages.success(request, "Client updated successfully.")
            return redirect("records")

    else:
        form                = ClientForm(instance=client)
        beneficiary_formset = BeneficiaryFormSet(instance=client, prefix="beneficiaries")

    return render(request, "app/edit_details.html", {
        "form":                form,
        "beneficiary_formset": beneficiary_formset,
        "client":              client,
    })


# ---------------------------------------------------------------------------
# Clients — DELETE
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def delete_client_view(request, pk):
    """
    POST-only, PIN-protected.
    Cascades automatically to ClientStatus → Payment, and Beneficiary.
    Returns JSON so the records table row can be removed without a full reload.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed."}, status=405)

    pin         = request.POST.get("pin", "")
    user_log    = UserLog.objects.filter(username=request.user.username).first()
    correct_pin = str(user_log.pin) if user_log else "1234"

    if pin != correct_pin:
        return JsonResponse({"success": False, "error": "Invalid PIN."})

    client = get_object_or_404(ClientPersonalInfo, pk=pk)
    name   = client.full_name()
    client.delete()

    return JsonResponse({"success": True, "name": name})


# ---------------------------------------------------------------------------
# Payments — internal helper
# ---------------------------------------------------------------------------

def _generate_payment_rows(client_status):
    """
    Idempotent. Generates one Payment row per month of the plan duration.
    First month = same calendar month as start_date (day normalised to 1).
    """
    if client_status.payments.exists():
        return

    first_month = client_status.start_date.replace(day=1)
    Payment.objects.bulk_create([
        Payment(
            client_status=client_status,
            month=first_month + relativedelta(months=i),
            amount=client_status.monthly_payment,
            is_paid=False,
        )
        for i in range(client_status.duration)
    ])


# ---------------------------------------------------------------------------
# Payments — summary (Records → Update Payment)
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def add_payment_view(request, pk):
    client        = get_object_or_404(ClientPersonalInfo, pk=pk)
    client_status = ClientStatus.objects.filter(client=client).first()

    if client_status:
        _generate_payment_rows(client_status)

    return render(request, "app/add_payment.html", {
        "client":        client,
        "client_status": client_status,
    })


# ---------------------------------------------------------------------------
# Payments — full monthly table + pay action
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def payment_history_view(request, pk):
    client        = get_object_or_404(ClientPersonalInfo, pk=pk)
    client_status = ClientStatus.objects.filter(client=client).first()

    if not client_status:
        messages.error(request, "No plan found for this client.")
        return redirect("records")

    _generate_payment_rows(client_status)

    # AJAX POST — mark a single month paid
    if request.method == "POST":
        payment_id  = request.POST.get("payment_id", "")
        pin         = request.POST.get("pin", "")
        user_log    = UserLog.objects.filter(username=request.user.username).first()
        correct_pin = str(user_log.pin) if user_log else "1234"

        if pin != correct_pin:
            return JsonResponse({"success": False, "error": "Invalid PIN."})

        payment = get_object_or_404(Payment, pk=payment_id, client_status=client_status)

        if payment.is_paid:
            return JsonResponse({"success": False, "error": "This month is already paid."})

        with transaction.atomic():
            payment.is_paid   = True
            payment.date_paid = timezone.now()
            payment.save()

            client_status.paid_balance     += payment.amount
            client_status.balance          -= payment.amount
            client_status.months_remaining  = client_status.payments.filter(is_paid=False).count()
            client_status.date_paid         = payment.date_paid
            if client_status.months_remaining == 0:
                client_status.status = False
            client_status.save()

        return JsonResponse({
            "success":          True,
            "date_paid":        payment.date_paid.strftime("%b %d, %Y %I:%M %p"),
            "paid_balance":     str(client_status.paid_balance),
            "balance":          str(client_status.balance),
            "months_remaining": client_status.months_remaining,
        })

    payments = client_status.payments.all()

    return render(request, "app/payment_history.html", {
        "client":        client,
        "client_status": client_status,
        "payments":      payments,
    })


# ---------------------------------------------------------------------------
# Monitor
# ---------------------------------------------------------------------------

@login_required(login_url="login")
def monitor_view(request):
    return render(request, "app/monitor.html")


@login_required(login_url="login")
def plan_get(request, pk):
    client = get_object_or_404(ClientPersonalInfo, pk=pk)
    return render(request, "app/plan.html", {"client": client})

@login_required(login_url="login")
def plan_view(request):
    return render(request, "app/plan.html")

@login_required(login_url="login")
def employee_view(request):
    return render(request, "app/viewemployee.html")

@login_required(login_url="login")
def add_employee_view(request):
    return render(request, "app/add-employee.html")

@login_required(login_url="login")
def details_employee_view(request):
    return render(request, "app/details-employee.html")

