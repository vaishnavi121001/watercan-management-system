from datetime import timezone, timedelta

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from owner.models import Bill, OwnerProfile
from Delivery.models import DeliveryProof
from .form import CustomerLoginForm, DailyScheduleForm, BulkOrderForm
from .models import DailySchedule, BulkOrder, HelpChatLog
from django.utils import timezone
from datetime import datetime
from calendar import monthrange
from django.db import models
from django.db.models import Sum, Q
from owner.models import DailyDeliveryLog, MonthlyBill, WaterCan, Bill


def customer_login_view(request):
    if request.method == 'POST':
        form = CustomerLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('customer_dashboard')  # your dashboard URL name
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = CustomerLoginForm()
    return render(request, 'login.html', {'form': form})



@login_required
def customer_dashboard_view(request):
    customer = request.user.customerprofile

    try:
        daily_schedule = DailySchedule.objects.get(customer=customer)
    except DailySchedule.DoesNotExist:
        daily_schedule = None

    daily_logs = DailyDeliveryLog.objects.filter(
        schedule__customer=customer
    ).order_by('-delivery_date')[:5]

    latest_bill = MonthlyBill.objects.filter(customer=customer).order_by('-month').first()

    bulk_orders = BulkOrder.objects.filter(customer=customer).order_by('-delivery_date')[:3]

    bills = MonthlyBill.objects.filter(customer=customer).order_by('-month')
    # === Calculate cans with customer using DeliveryProof ===

    delivered_total = DeliveryProof.objects.filter(
        Q(daily_delivery__schedule__customer=customer) |
        Q(bulk_order__customer=customer)
    ).aggregate(total_delivered=Sum('cans_delivered'))['total_delivered'] or 0

    received_empty_total = DeliveryProof.objects.filter(
        Q(daily_delivery__schedule__customer=customer) |
        Q(bulk_order__customer=customer)
    ).aggregate(total_received=Sum('cans_received_empty'))['total_received'] or 0

    cans_at_customer = delivered_total - received_empty_total

    context = {
        'customer': customer,
        'daily_schedule': daily_schedule,
        'daily_logs': daily_logs,
        'latest_bill': latest_bill,
        'bulk_orders': bulk_orders,
        'cans_at_customer': cans_at_customer,
        'bills':bills,
    }

    return render(request, 'dashboard.html', context)


def customer_logout_view(request):
    logout(request)
    return redirect('customer_login')


@login_required
def manage_daily_schedule(request):
    customer = request.user.customerprofile

    try:
        schedule = DailySchedule.objects.get(customer=customer)
        is_edit = True
    except DailySchedule.DoesNotExist:
        schedule = None
        is_edit = False

    if request.method == 'POST':
        form = DailyScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            daily_schedule = form.save(commit=False)
            daily_schedule.customer = customer
            daily_schedule.is_active = True
            daily_schedule.save()
            return redirect('customer_dashboard')
    else:
        form = DailyScheduleForm(instance=schedule)

    return render(request, 'manage_schedule.html', {
        'form': form,
        'is_edit': is_edit,
    })




@login_required
def cancel_delivery(request, log_id):
    log = get_object_or_404(DailyDeliveryLog, id=log_id, schedule__customer=request.user.customerprofile)

    if log.status == 'Scheduled':
        log.status = 'Cancelled'
        log.save()

    return redirect('customer_dashboard')


@login_required
def confirm_delivery(request, log_id):
    log = get_object_or_404(DailyDeliveryLog, id=log_id, schedule__customer=request.user.customerprofile)

    if log.status == 'Delivered':
        time_since_created = timezone.now() - log.created_at

        if time_since_created > timedelta(hours=12):
            # Auto-confirm if not confirmed within 12 hours
            log.status = 'Auto-Confirmed'
            log.confirmed_by_system = True
        else:
            # Manual confirmation by customer
            log.status = 'Confirmed'
            log.confirmed_by_customer = True

        log.save()

    return redirect('customer_dashboard')


@login_required
def request_modification(request, log_id):
    log = get_object_or_404(DailyDeliveryLog, id=log_id)

    # Ensure the logged-in user owns the schedule tied to this log
    if log.schedule.customer != request.user.customerprofile:
        messages.error(request, 'You are not authorized to modify this entry.')
        return redirect('customer_dashboard')

    if request.method == 'POST':
        try:
            num_cans = int(request.POST.get('num_cans'))
            if num_cans < 0:
                messages.error(request, 'Quantity cannot be negative.')
                return redirect('customer_dashboard')

            log.modified_quantity = num_cans
            log.save()

            messages.success(request, f'Modification request submitted successfully for {log.delivery_date}.')
        except (TypeError, ValueError):
            messages.error(request, 'Invalid quantity provided.')

        return redirect('customer_dashboard')

    # Optional: Render a modification form if you want GET support
    return redirect('customer_dashboard')


@login_required
def place_bulk_order(request):
    if request.method == 'POST':
        form = BulkOrderForm(request.POST)
        if form.is_valid():
            bulk_order = form.save(commit=False)
            bulk_order.customer = request.user.customerprofile
            bulk_order.status = 'Pending'

            water_can = bulk_order.water_can
            if water_can.current_stock >= bulk_order.quantity:


                bulk_order.save()
                return redirect('customer_dashboard')
            else:
                messages.error(request, 'Not enough stock available for this order.')
    else:
        form = BulkOrderForm()

    return render(request, 'bulk_order.html', {'form': form})

@login_required
def generate_monthly_bill(request):
    customer = request.user.customerprofile
    now = timezone.now()

    # Set start and end of current month with timezone awareness
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.get_current_timezone())
    last_day = monthrange(now.year, now.month)[1]
    month_end = datetime(now.year, now.month, last_day, 23, 59, 59, tzinfo=timezone.get_current_timezone())

    # Fetch logs for the current month
    logs = DailyDeliveryLog.objects.filter(
        schedule__customer=customer,
        delivery_date__range=(month_start, month_end),
        status__in=['Delivered', 'Confirmed', 'Auto-Confirmed']
    )

    total_cans = 0
    price = 0

    for log in logs:
        schedule = log.schedule
        day_quantity = log.modified_quantity if log.modified_quantity is not None else schedule.quantity_per_day
        total_cans += day_quantity

        if schedule.water_can:
            price = schedule.water_can.price  # Use last found can price

    amount_due = total_cans * price

    bill, created = MonthlyBill.objects.get_or_create(
        customer=customer,
        month=month_start,
        defaults={
            'total_cans': total_cans,
            'amount_due': amount_due,
            'payment_status': 'Pending',
        }
    )

    if not created:
        bill.total_cans = total_cans
        bill.amount_due = amount_due
        if bill.payment_status != 'Paid':
            bill.payment_status = 'Pending'
        bill.save()

    return redirect('view_bills')


@login_required
def view_all_bills(request):
    customer = request.user.customerprofile
    bills = MonthlyBill.objects.filter(customer=customer).order_by('-month')

    bulk_orders = BulkOrder.objects.filter(
        customer=customer,
        delivery_date__month=timezone.now().month,
        delivery_date__year=timezone.now().year,
        status__in=['Pending', 'Delivered']
    )

    # Calculate total price for bulk orders dynamically
    for order in bulk_orders:
        if order.water_can and order.water_can.price:
            order.total_price = order.quantity * order.water_can.price
        else:
            order.total_price = 0

    return render(request, 'all_bills.html', {'bills': bills, 'bulk_orders': bulk_orders})


@login_required
def pay_bill(request, bill_id):
    bill = get_object_or_404(MonthlyBill, id=bill_id, customer=request.user.customerprofile)

    if bill.payment_status == 'Paid':
        messages.info(request, "This bill is already paid.")
        return redirect('view_bills')

    if request.method == 'POST':
        # TODO: Integrate payment gateway here
        bill.payment_status = 'Paid'
        bill.save()
        messages.success(request, "Payment successful! Thank you.")
        return redirect('view_bills')

    return render(request, 'pay_bill.html', {'bill': bill})


@login_required
def confirm_payment(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)

    # Check if the logged-in user has permission to confirm this bill payment
    if bill.customer.user != request.user:
        return HttpResponseForbidden("You are not allowed to confirm this payment.")

    if request.method == "POST":
        # Update the bill status as paid
        bill.status = 'paid'  # or however you represent paid bills
        bill.save()
        # Redirect to some confirmation page or bills page
        return redirect('view_all_bills')

    # If GET request, show a confirmation page
    return render(request, 'confirm_payment.html', {'bill': bill})


def view_bill_detail(request, bill_id):
    bill = MonthlyBill.objects.select_related('customer').get(id=bill_id)
    owner = OwnerProfile.objects.first()  # Assuming only one owner

    return render(request, 'view_bill.html', {
        'bill': bill,
        'owner': owner,
    })


from openai import OpenAI
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.clickjacking import xframe_options_exempt


@xframe_options_exempt
@login_required
def help_chat(request):
    user = request.user
    response = None

    # 🧊 Water Can Info
    can_info = "Available Water Cans and Prices (in ₹):\n"
    for can in WaterCan.objects.all():
        can_info += f"- {can.name}: ₹{can.price} per unit\n"

    # 🧠 Role-specific Data
    role_context = schedule_info = bill_info = bulk_info = ""

    if user.role == 'customer':
        profile = user.customerprofile

        # 📅 Daily Schedule
        try:
            schedule = DailySchedule.objects.get(customer=profile)
            schedule_info = (
                f"Daily Schedule:\n"
                f"- Can: {schedule.water_can.name}\n"
                f"- Quantity per day: {schedule.quantity_per_day}\n"
                f"- Delivery time: {schedule.delivery_time}\n"
                f"- Status: {'Active' if schedule.is_active else 'Inactive'}\n"
            )
        except DailySchedule.DoesNotExist:
            schedule_info = "You do not have a daily schedule.\n"

        # 💸 Latest Bill
        latest_bill = MonthlyBill.objects.filter(customer=profile).order_by('-month').first()
        if latest_bill:
            bill_info = (
                f"Latest Bill:\n"
                f"- Month: {latest_bill.month.strftime('%B %Y')}\n"
                f"- Total Cans: {latest_bill.total_cans}\n"
                f"- Amount Due: ₹{latest_bill.amount_due}\n"
                f"- Payment Status: {latest_bill.payment_status}\n"
            )
        else:
            bill_info = "No billing records found.\n"

        # 📦 Bulk Orders
        bulk_orders = BulkOrder.objects.filter(customer=profile).order_by('-delivery_date')[:3]
        if bulk_orders.exists():
            bulk_info = "Recent Bulk Orders:\n"
            for order in bulk_orders:
                bulk_info += (
                    f"- Event: {order.event_name or 'N/A'}, Qty: {order.quantity}, "
                    f"Date: {order.delivery_date}, Status: {order.status}\n"
                )
        else:
            bulk_info = "No recent bulk orders.\n"

        role_context = (
            f"User Role: Customer\n"
            f"Name: {profile.full_name}\n"
            f"Phone: {profile.phone_number}\n"
            f"Address: {profile.address}\n"
        )

    elif user.role == 'delivery_boy':
        profile = user.deliveryboyprofile
        deliveries = DailyDeliveryLog.objects.filter(delivery_boy=profile).order_by('-delivery_date')[:3]

        delivery_info = "Recent Deliveries:\n"
        if deliveries.exists():
            for d in deliveries:
                delivery_info += (
                    f"- Date: {d.delivery_date}, Customer: {d.schedule.customer.user.username}, "
                    f"Quantity: {d.modified_quantity or d.schedule.quantity_per_day}, "
                    f"Status: {d.status}\n"
                )
        else:
            delivery_info += "No delivery logs available.\n"

        role_context = (
            f"User Role: Delivery Boy\n"
            f"Name: {profile.full_name}\n"
            f"Phone: {profile.phone}\n"
            f"Address: {profile.address}\n"
            f"{delivery_info}"
        )

    elif user.role == 'admin':
        role_context = (
            "User Role: Admin\n"
            "You are the administrator of the Water Cans Delivery System.\n"
            "You can manage users, delivery boys, schedules, and bills.\n"
        )

    # 📜 System Prompt
    system_prompt = (
        "You are a helpful assistant for a Water Cans Delivery System in India.\n"
        "You must answer only in the context of the following user-specific data.\n"
        "Respond politely and clearly in simple language.\n\n"
        f"{role_context}\n"
        f"{can_info}\n"
        f"{schedule_info}\n"
        f"{bill_info}\n"
        f"{bulk_info}"
    )

    if request.method == 'POST':
        question = request.POST.get('question')

        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.GROQ_API_KEY,
        )

        try:
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ]
            )

            response = chat_completion.choices[0].message.content.strip()

            # ✅ Save chat with correct customer profile
            if user.role == 'customer':
                HelpChatLog.objects.create(
                    customer=profile,
                    question=question,
                    response=response,
                    timestamp=timezone.now()
                )

            return redirect('help_chat')

        except Exception as e:
            response = f"⚠️ Error: {str(e)}"

    # ⏪ Show chat history (only for customers)
    if user.role == 'customer':
        chat_logs = HelpChatLog.objects.filter(customer=user.customerprofile).order_by('timestamp')
    else:
        chat_logs = []

    return render(request, 'help_chat.html', {
        'response': response,
        'chat_logs': chat_logs,
    })


@login_required
def chat_history(request):
    history = HelpChatLog.objects.filter(customer=request.user.customerprofile).order_by('-timestamp')[:20]
    return render(request, 'chat_history.html', {'history': history})


