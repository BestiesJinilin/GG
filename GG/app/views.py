from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import auth, User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import localtime
from dateutil.relativedelta import relativedelta
from .models import ClientPersonalInfo, ClientStatus, Beneficiary, UserLog, Payment
from .forms import ClientForm, BeneficiaryFormSet, EmployeeCreateForm
# from .employee_forms import EmployeeCreateForm, EmployeeUpdateForm
import datetime


#Login
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)

            #Time in
            log = UserLog.objects.filter(user=user).first()
            if log:
                log.time_in    = timezone.now()
                log.time_out   = None        
                log.activities = "Login"
                log.save()

            return redirect("homepage")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "app/login.html")

#Log out
@login_required(login_url="login")
@require_POST
def logout(request):
    #Time out
    if request.user.username != "admin":
        log = UserLog.objects.filter(user=request.user).first()
        if log:
            log.time_out   = timezone.now()
            log.activities = "Logout"
            log.save()

    auth.logout(request)
    return redirect("login")


# Dashboard
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



# Clients — CREATE
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

                today = datetime.date.today()
                client_status = ClientStatus.objects.create(
                    client=client,
                    plan="No Plan",
                    monthly_payment=0,
                    duration=0,
                    months_remaining=0,
                    start_date=today,
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



# Clients — Records
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



# Clients — Details
@login_required(login_url="login")
def client_details_view(request, pk):
    client        = get_object_or_404(ClientPersonalInfo, pk=pk)
    client_status = ClientStatus.objects.filter(client=client).first()
    return render(request, "app/client-details.html", {
        "client":        client,
        "client_status": client_status,
    })



# Clients — UPDATE
@login_required(login_url="login")
def edit_details_view(request, pk):
    client = get_object_or_404(ClientPersonalInfo, pk=pk)

    if request.method == "POST":
        form                = ClientForm(request.POST, instance=client)
        beneficiary_formset = BeneficiaryFormSet(
            request.POST, instance=client, prefix="beneficiaries"
        )

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



# Clients — DELETE
@login_required(login_url="login")
def delete_client_view(request, pk):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed."}, status=405)

    pin         = request.POST.get("pin", "")
    user_log    = UserLog.objects.filter(user=request.user).first()
    correct_pin = str(user_log.pin) if user_log else "1234"

    if pin != correct_pin:
        return JsonResponse({"success": False, "error": "Invalid PIN."})

    client = get_object_or_404(ClientPersonalInfo, pk=pk)
    name   = client.full_name()
    client.delete()

    return JsonResponse({"success": True, "name": name})



# Payments - HELPER
def _generate_payment_rows(client_status):
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



# Payments - SUMMARY
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


# Payments — Table
@login_required(login_url="login")
def payment_history_view(request, pk):
    client        = get_object_or_404(ClientPersonalInfo, pk=pk)
    client_status = ClientStatus.objects.filter(client=client).first()

    if not client_status:
        messages.error(request, "No plan found for this client.")
        return redirect("records")

    _generate_payment_rows(client_status)

    if request.method == "POST":
        payment_id  = request.POST.get("payment_id", "")
        pin         = request.POST.get("pin", "")
        user_log    = UserLog.objects.filter(user=request.user).first()
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
            "date_paid":        localtime(payment.date_paid).strftime("%b %d, %Y %I:%M %p"),
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


# Monitor
@login_required(login_url="login")
def monitor_view(request):
    return render(request, "app/monitor.html")


# Plan
@login_required(login_url="login")
def plan(request, pk):
    client = get_object_or_404(ClientPersonalInfo, pk=pk)
    status = ClientStatus.objects.filter(client=client)
    return render(request, "app/plan.html", {"client": client, "status": status})



# Employee — LIST
@login_required(login_url="login")
def employee_view(request):
    query     = request.GET.get("q", "").strip()
    employees = UserLog.objects.select_related("user").all().order_by("last_name", "first_name")

    if query:
        employees = employees.filter(
            Q(first_name__icontains=query)  |
            Q(last_name__icontains=query)   |
            Q(middle_name__icontains=query) |
            Q(role__icontains=query)        |
            Q(employee_id__icontains=query) |
            Q(phone_number__icontains=query)
        ).distinct()


    for emp in employees:
        emp.full_name = emp.full_name()

    return render(request, "app/viewemployee.html", {
        "employees": employees,
        "query":     query,
    })


# Employee - CREATE
@login_required(login_url="login")
def add_employee_view(request):
    if request.method == "POST":
        form = EmployeeCreateForm(request.POST)

        if form.is_valid():
            d = form.cleaned_data

            if User.objects.filter(username=d["username"]).exists():
                form.add_error("username", "Username already exists.")
                return render(request, "app/add-employee.html", {"form": form})

            with transaction.atomic():
                user = User.objects.create_user(
                    username=d["username"],
                    password=d["password"],
                    email=d.get("email", ""),
                    first_name=d["first_name"],
                    last_name=d["last_name"],
                )

                UserLog.objects.create(
                    user=user,
                    role=d["role"],
                    first_name=d["first_name"],
                    middle_name=d.get("middle_name", "") or "",
                    last_name=d["last_name"],
                    date_of_birth=d["date_of_birth"],
                    government_id=d.get("government_id", ""),
                    phone_number=d.get("phone_number", ""),
                    email=d.get("email", ""),
                    address=d["address"],
                    emergency_contact_name=d["emergency_contact_name"],
                    emergency_contact_number=d["emergency_contact_number"],
                    activities="Account created",
                    pin=d["pin"],
                )

            messages.success(
                request,
                f"Employee '{d['first_name']} {d['last_name']}' created successfully."
            )
            return redirect("employee")
        else:
            # Form invalid, render with errors
            return render(request, "app/add-employee.html", {"form": form})

    else:
        form = EmployeeCreateForm()

    return render(request, "app/add-employee.html", {"form": form})


# Employee — DETAILS
@login_required(login_url="login")
def details_employee_view(request, pk):
    employee = get_object_or_404(UserLog, pk=pk)

    # Annotate duration for display (simple minutes calculation)
    logs = UserLog.objects.filter(pk=pk)  # single-row history for this employee
    # For a real audit trail you'd have a separate AuditLog model;
    # here we show the current UserLog record's session info.
    # We build a synthetic list so the template loop works cleanly.
    session = []
    if employee.time_in:
        duration_str = "—"
        if employee.time_out:
            delta   = employee.time_out - employee.time_in
            minutes = int(delta.total_seconds() // 60)
            hours   = minutes // 60
            mins    = minutes % 60
            duration_str = f"{hours}h {mins}m"
        employee.duration = duration_str
        session.append(employee)

    return render(request, "app/employee-details.html", {
        "employee": employee,
        "logs":     session,
    })



# Employee — UPDATE
@login_required(login_url="login")
def edit_employee_view(request, pk):
    employee = get_object_or_404(UserLog, pk=pk)

    if request.method == "POST":
        form = EmployeeUpdateForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            with transaction.atomic():
               
                employee.first_name               = d["first_name"]
                employee.middle_name              = d.get("middle_name", "") or ""
                employee.last_name                = d["last_name"]
                employee.date_of_birth            = d["date_of_birth"]
                employee.address                  = d["address"]
                employee.email                    = d["email"]
                employee.phone_number             = d["phone_number"]
                employee.emergency_contact_name   = d["emergency_contact_name"]
                employee.emergency_contact_number = d["emergency_contact_number"]
                employee.role                     = d["role"]
                employee.employee_id              = d["employee_id"]
                employee.government_id            = d["government_id"]
                employee.pin                      = d["pin"]
                employee.save()

        
                if employee.user:
                    employee.user.first_name = d["first_name"]
                    employee.user.last_name  = d["last_name"]
                    employee.user.email      = d["email"]
                    if d.get("new_password"):
                        employee.user.set_password(d["new_password"])
                    employee.user.save()

            messages.success(request, "Employee updated successfully.")
            return redirect("details-employee", pk=pk)
    else:
        form = EmployeeUpdateForm(initial={
            "first_name":               employee.first_name,
            "middle_name":              employee.middle_name,
            "last_name":                employee.last_name,
            "date_of_birth":            employee.date_of_birth,
            "address":                  employee.address,
            "email":                    employee.email,
            "phone_number":             employee.phone_number,
            "emergency_contact_name":   employee.emergency_contact_name,
            "emergency_contact_number": employee.emergency_contact_number,
            "role":                     employee.role,
            "employee_id":              employee.employee_id,
            "government_id":            employee.government_id,
            "pin":                      employee.pin,
        })

    return render(request, "app/employee-edit.html", {
        "form":     form,
        "employee": employee,
    })



# Employee — DELETE 
@login_required(login_url="login")
def delete_employee_view(request, pk):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed."}, status=405)

    pin         = request.POST.get("pin", "")
    user_log    = UserLog.objects.filter(user=request.user).first()
    correct_pin = str(user_log.pin) if user_log else "1234"

    if pin != correct_pin:
        return JsonResponse({"success": False, "error": "Invalid PIN."})

    # Prevent self-deletion
    employee = get_object_or_404(UserLog, pk=pk)
    if employee.user == request.user:
        return JsonResponse({"success": False, "error": "You cannot delete your own account."})

    name = employee.full_name()
    with transaction.atomic():
        if employee.user:
            employee.user.delete() 
        else:
            employee.delete()

    return JsonResponse({"success": True, "name": name})
