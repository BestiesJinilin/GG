
# ─── paste this ENTIRE function into views.py, replacing the existing plan() ───

@login_required(login_url="login")
def plan(request, pk):
    client = get_object_or_404(ClientPersonalInfo, pk=pk)
    plans  = ClientStatus.objects.filter(client=client)
    form   = PlanForm()

    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            d         = form.cleaned_data
            plan_name = d["plan"]
            monthly   = d["monthly_payment"]
            duration  = d["duration"]
            total     = monthly * duration
            today     = datetime.date.today()

            # FIX: read the new lot-detail fields (all optional)
            down_payment = d.get("down_payment")  # may be None
            phase        = d.get("phase", "").strip()
            section      = d.get("section", "").strip()
            lot_number   = d.get("lot_number", "").strip()
            pa_number    = d.get("pa_number", "").strip()

            # Block if client already has a real active/completed plan
            blocking = plans.exclude(plan="No Plan").filter(status__in=[True, False])
            if blocking.exists():
                messages.error(
                    request,
                    "This client already has an active or completed plan. "
                    "You cannot add another plan while one is ongoing or finished."
                )
                return render(request, "app/plan.html", {
                    "client": client,
                    "plans":  plans,
                    "form":   form,
                })

            # Replace the "No Plan" placeholder row
            no_plan = plans.filter(plan="No Plan").first()

            if no_plan:
                no_plan.payments.all().delete()
                no_plan.plan             = plan_name
                no_plan.monthly_payment  = monthly
                no_plan.duration         = duration
                no_plan.months_remaining = duration
                no_plan.start_date       = today
                no_plan.balance          = total
                no_plan.paid_balance     = 0
                no_plan.status           = True
                no_plan.date_paid        = None
                # FIX: save lot-detail fields
                no_plan.down_payment     = down_payment
                no_plan.phase            = phase or None
                no_plan.section          = section or None
                no_plan.lot_number       = lot_number or None
                no_plan.pa_number        = pa_number or None
                no_plan.save()
                _generate_payment_rows(no_plan)
            else:
                # Edge case: no placeholder row exists at all
                new_status = ClientStatus.objects.create(
                    client           = client,
                    plan             = plan_name,
                    monthly_payment  = monthly,
                    duration         = duration,
                    months_remaining = duration,
                    start_date       = today,
                    balance          = total,
                    paid_balance     = 0,
                    status           = True,
                    down_payment     = down_payment,
                    phase            = phase or None,
                    section          = section or None,
                    lot_number       = lot_number or None,
                    pa_number        = pa_number or None,
                )
                _generate_payment_rows(new_status)

            messages.success(request, f"Plan '{plan_name}' has been assigned successfully.")
            return redirect("plan", pk=pk)

    return render(request, "app/plan.html", {
        "client": client,
        "plans":  plans,
        "form":   form,
    })
