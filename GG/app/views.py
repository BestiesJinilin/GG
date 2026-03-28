from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q

from .models import ClientPersonalInfo, ClientStatus, Beneficiary, UserLog
from .forms import ClientForm, BeneficiaryFormSet


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect("homepage")
        else:
            messages.info(request, "Invalid Credentials")
            return redirect("login")

    return render(request, "app/login.html")


@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    return redirect("login")


@login_required(login_url="login")
def homepage_view(request):
    client = ClientPersonalInfo.objects.all()
    client_paid = ClientStatus.objects.values_list("paid_balance", flat=True)
    client_remaining_months = ClientStatus.objects.values_list("months_remaining", flat=True)
    active_status = ClientStatus.objects.filter(status=True).count()
    total_clients = client.count()

    collected = 0
    pending_payments = 0

    for paid in client_paid:
        collected += paid

    for pending in client_remaining_months:
        pending_payments += pending

    return render(
        request,
        "app/homepage.html",
        {
            "client": client,
            "total_clients": total_clients,
            "collected": collected,
            "active_status": active_status,
            "pending_payments": pending_payments,
        },
    )


@login_required(login_url='login')
def add_client_view(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        beneficiary_formset = BeneficiaryFormSet(request.POST, prefix="beneficiaries")

        if form.is_valid() and beneficiary_formset.is_valid():
            client = form.save(commit=False)

            first = client.client_first_name
            last = client.client_last_name
            dob = client.client_date_birth

            if ClientPersonalInfo.objects.filter(
                client_first_name__iexact=first,
                client_last_name__iexact=last,
                client_date_birth=dob
            ).exists():
                form.add_error(None, "Client with this name and date of birth already exists.")
                return render(request, "app/addclient.html", {
                    "form": form,
                    "beneficiary_formset": beneficiary_formset
                })

            with transaction.atomic():
                client.save()

                beneficiary_formset.instance = client
                beneficiary_formset.save()

                ClientStatus.objects.create(
                    client=client,
                    plan="Memorial B",
                    monthly_payment=2000.00,
                    duration=24,
                    months_remaining=24,
                    start_date=client.client_date_birth,
                    balance=48000.00,
                    paid_balance=0.00,
                    status=True
                )

            messages.success(request, f"Client '{client.full_name()}' added successfully!")
            return redirect("records")

        else:
            pass

    else:
        form = ClientForm()
        beneficiary_formset = BeneficiaryFormSet(prefix="beneficiaries")

    return render(request, "app/addclient.html", {
        "form": form,
        "beneficiary_formset": beneficiary_formset
    })


@login_required(login_url="login")
def records_view(request):
    query = request.GET.get("q")
    client = ClientPersonalInfo.objects.all()

    if query:
        client = client.filter(
            Q(client_first_name__icontains=query) |
            Q(client_middle_name__icontains=query) |
            Q(client_last_name__icontains=query) |
            Q(client_contact_number__icontains=query) |
            Q(client_civil_status__icontains=query) |
            Q(clientstatus__plan__icontains=query)
        ).distinct()

    return render(request, "app/records.html", {"client": client})


@login_required(login_url="login")
def add_payment_view(request, pk):
    client = get_object_or_404(ClientPersonalInfo, pk=pk)
    client_status = ClientStatus.objects.filter(client=client).first()
    return render(request, "app/add_payment.html", {"client": client, "client_status": client_status})


@login_required(login_url="login")
def monitor_view(request):
    return render(request, "app/monitor.html")


@login_required(login_url="login")
def client_details_view(request, pk):
    client = get_object_or_404(ClientPersonalInfo, pk=pk)
    return render(request, "app/client-details.html", {"client": client})


@login_required(login_url="login")
def edit_details_view(request, pk):
    client = get_object_or_404(ClientPersonalInfo, pk=pk)
    
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        beneficiary_formset = BeneficiaryFormSet(
            request.POST,
            instance=client,
            prefix="beneficiaries"
        )

        if form.is_valid() and beneficiary_formset.is_valid():
            with transaction.atomic():
                form.save()
                beneficiary_formset.save()

            messages.success(request, "Client updated successfully!")
            return redirect("records")

    else:
        form = ClientForm(instance=client)
        beneficiary_formset = BeneficiaryFormSet(
            instance=client,
            prefix="beneficiaries"
        )

    return render(request, "app/edit_details.html", {
        "form": form,
        "beneficiary_formset": beneficiary_formset,
        "client": client
    })


@login_required(login_url="login")
def payment_history_view(request):
    return render(request, "app/payment_history.html")