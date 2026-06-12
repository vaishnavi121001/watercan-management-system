from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse

from Delivery.models import DeliveryProof
from customerlog.models import DailySchedule, BulkOrder

from owner.models import DeliveryBoyProfile, CustomerProfile, WaterCan, DailyDeliveryLog, OwnerProfile, Bill

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from owner.form import CustomerRegistrationForm, CustomerUpdateForm, DailyDeliveryLogForm, \
    WaterCanForm, AssignBulkOrderForm, OwnerProfileForm
from owner.form1 import DeliveryBoyUpdateForm, DeliveryBoyRegistrationForm

def home_page(request):
    """Render the home page"""
    return render(request, 'owner/home.html')
# Dashboard view


def owner_dashboard(request):
    # Now request.user is guaranteed to be an authenticated user
    profile = OwnerProfile.objects.last()
    total_customers = CustomerProfile.objects.count()
    total_delivery_boys = DeliveryBoyProfile.objects.count()
    inventory = WaterCan.objects.last()
    total_cans_added = inventory.total_cans_added if inventory else 0

    context = {
        'total_customers': total_customers,
        'total_delivery_boys': total_delivery_boys,
        'total_cans_added': total_cans_added,
        'profile': profile,
    }
    return render(request, 'owner/owner_dashboard.html', context)



def update_owner_profile(request):
    if request.method == 'POST':
        form = OwnerProfileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('owner:owner_dashboard')
    else:
        form = OwnerProfileForm()

    return render(request, 'owner/update_profile.html', {'form': form})


def add_customer(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('owner:owner_dashboard')
    else:
        form = CustomerRegistrationForm()
    return render(request, 'owner/add_customer.html', {'form': form})


def view_customers(request):
    customers = CustomerProfile.objects.all()
    return render(request, 'owner/view_customers.html', {'customers': customers})


def update_customer(request, pk):
    customer = get_object_or_404(CustomerProfile, pk=pk)
    if request.method == 'POST':
        form = CustomerUpdateForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer updated successfully.")
            return redirect('owner:view_customers')
    else:
        form = CustomerUpdateForm(instance=customer)
    return render(request, 'owner/update_customer.html', {'form': form})


def delete_customer(request, customer_id):
    customer = get_object_or_404(CustomerProfile, id=customer_id)
    user = customer.user  # store user before deleting customer profile
    customer.delete()
    user.delete()  # also delete the linked User
    messages.success(request, "Customer deleted successfully.")
    return redirect('owner:view_customers')


# Delivery boy management views
def view_delivery_boys(request):
    delivery_boys = DeliveryBoyProfile.objects.all()
    return render(request, 'owner/view_delivery_boys.html', {'delivery_boys': delivery_boys})


def add_delivery_boys(request):
    if request.method == 'POST':
        form = DeliveryBoyRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # This creates both the User and DeliveryBoyProfile
            messages.success(request, "Delivery boy registered successfully.")
            return redirect('owner:owner_dashboard')
    else:
        form = DeliveryBoyRegistrationForm()
    return render(request, 'owner/add_delivery_boy.html', {'form': form})


def update_delivery_boy(request, delivery_boy_id):
    delivery_boy = get_object_or_404(DeliveryBoyProfile, id=delivery_boy_id)
    if request.method == 'POST':
        form = DeliveryBoyUpdateForm(request.POST, request.FILES, instance=delivery_boy)
        if form.is_valid():
            form.save()
            messages.success(request, "Delivery boy updated successfully.")
            return redirect('owner:view_delivery_boys')
    else:
        form = DeliveryBoyUpdateForm(instance=delivery_boy)
    return render(request, 'owner/update_delivery_boy.html', {'form': form})


def delete_delivery_boy(request, delivery_boy_id):
    delivery_boy = get_object_or_404(DeliveryBoyProfile, id=delivery_boy_id)
    user = delivery_boy.user  # Get associated User object
    delivery_boy.delete()     # Delete DeliveryBoyProfile
    user.delete()             # Optionally delete the user account too
    messages.success(request, "Delivery boy deleted successfully.")
    return redirect('owner:view_delivery_boys')


# Inventory management views
def cans_stock_view(request):
    total_cans_in_stock = WaterCan.objects.aggregate(total=Sum('current_stock'))['total'] or 0
    all_cans = WaterCan.objects.all()  # Fetch all cans and their individual stock
    proofs = DeliveryProof.objects.select_related(
        'daily_delivery__schedule__customer__user',
        'bulk_order__customer__user'
    ).order_by('-uploaded_at')

    return render(request, 'owner/cans_stock.html', {
        'cans_in_stock': total_cans_in_stock,
        'cans_list': all_cans,
        'proofs': proofs,
    })

def add_inventory(request):
    if request.method == "POST":
        form = WaterCanForm(request.POST)
        if form.is_valid():
            water_can = form.save(commit=False)

            water_can.current_stock += water_can.total_cans_added
            water_can.save()
            return redirect('owner:owner_dashboard')
    else:
        form = WaterCanForm()
    return render(request, 'owner/add_inventory.html', {'form': form})


# Daily schedule view
def schedule_list_view(request):
    schedules = DailySchedule.objects.select_related('customer', 'water_can').all()
    return render(request, 'owner/schedule_list.html', {'schedules': schedules})


def assign_delivery(request):
    schedules = DailySchedule.objects.filter(assigned=False)
    delivery_boys = DeliveryBoyProfile.objects.all()

    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        boy_id = request.POST.get('boy_id')

        schedule = DailySchedule.objects.get(id=schedule_id)
        delivery_boy = DeliveryBoyProfile.objects.get(id=boy_id)
        water_can = schedule.water_can

        # Check stock
        if water_can.current_stock >= schedule.quantity_per_day:

            # Save assignment
            schedule.assigned = True
            schedule.delivery_boy = delivery_boy
            schedule.save()

            messages.success(request, "Delivery schedule assigned successfully.")
        else:
            messages.error(request, "Not enough stock to assign this delivery.")

        return redirect('owner:assigned_deliveries')

    context = {
        'schedules': schedules,
        'delivery_boys': delivery_boys,
    }
    return render(request, 'owner/assign_delivery.html', context)


def assigned_deliveries_view(request):
    logs = DailyDeliveryLog.objects.select_related('schedule__customer', 'delivery_boy').order_by('-delivery_date')
    return render(request, 'owner/assigned_delivery_list.html', {'logs': logs})



# Login system for owner
PREDEFINED_USERNAME = 'admin'
PREDEFINED_PASSWORD = '12345'

def custom_login(request):
    error = ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username == PREDEFINED_USERNAME and password == PREDEFINED_PASSWORD:
            request.session['authenticated'] = True
            return redirect('owner:owner_dashboard')
        else:
            error = 'Invalid credentials'

    return render(request, 'owner/login.html', {'error': error})

def logout_view(request):
    request.session.flush()
    messages.info(request, 'You have been logged out successfully.')
    return redirect('owner:custom_login')


def assign_bulk_order_view(request, order_id):
    order = get_object_or_404(BulkOrder, id=order_id)

    if request.method == 'POST':
        form = AssignBulkOrderForm(request.POST, instance=order)
        if form.is_valid():
            water_can = order.water_can
            if water_can.current_stock >= order.quantity:

                form.save()
                return redirect('owner:bulk_orders_list')
            else:
                messages.error(request, 'Not enough stock available for this order.')
    else:
        form = AssignBulkOrderForm(instance=order)

    return render(request, 'owner/assign_bulk_order.html', {'form': form, 'order': order})



def bulk_orders_list(request):
    bulk_orders = BulkOrder.objects.select_related('customer', 'delivery_boy').order_by('-delivery_date')
    context = {
        'bulk_orders': bulk_orders,
    }
    return render(request, 'owner/bulk_orders_list.html', context)


def view_delivered_cans(request):
    proofs = DeliveryProof.objects.select_related('delivery').order_by('-uploaded_at')
    return render(request, 'owner/view_delivered_cans.html', {'proofs': proofs})


def view_returned_cans(request):
    proofs = DeliveryProof.objects.select_related('delivery').order_by('-uploaded_at')
    return render(request, 'owner/view_returned_cans.html', {'proofs': proofs})


# owner/views.py
from django.contrib import messages
from django.shortcuts import redirect
from owner.utils import generate_daily_logs

def manual_generate_logs(request):
    generate_daily_logs()
    messages.success(request, "✅ Daily delivery logs generated successfully.")
    return redirect('owner:assigned_deliveries')  # Or wherever you want to redirect



from django.utils.timezone import now
from datetime import datetime
from calendar import monthrange
from owner.models import CustomerProfile, MonthlyBill, DailyDeliveryLog

import qrcode
from io import BytesIO
import base64

def generate_all_bills(request):
    current_time = now()
    month_start = datetime(current_time.year, current_time.month, 1)
    month_end = datetime(current_time.year, current_time.month, monthrange(current_time.year, current_time.month)[1])

    customers = CustomerProfile.objects.all()
    generated_count = 0

    for customer in customers:
        logs = DailyDeliveryLog.objects.filter(
            schedule__customer=customer,
            delivery_date__range=(month_start, month_end),
            status__in=['Delivered', 'Confirmed', 'Auto-Confirmed']
        )

        total_cans = 0
        price = 0

        for log in logs:
            schedule = log.schedule
            quantity = log.modified_quantity if log.modified_quantity is not None else schedule.quantity_per_day
            total_cans += quantity
            if schedule.water_can:
                price = schedule.water_can.price

        amount_due = total_cans * price

        bill, created = MonthlyBill.objects.get_or_create(
            customer=customer,
            month=month_start,
            defaults={
                'total_cans': total_cans,
                'amount_due': amount_due,
                'payment_status': 'Pending'
            }
        )

        if not created:
            bill.total_cans = total_cans
            bill.amount_due = amount_due
            if bill.payment_status != 'Paid':
                bill.payment_status = 'Pending'
            bill.save()

        # OPTIONAL: generate Google Pay-compatible UPI QR code
        upi_id = "yourupi@bank"  # Replace with your UPI ID
        upi_url = f"upi://pay?pa={upi_id}&pn=AquaCan&am={amount_due}&cu=INR"
        qr = qrcode.make(upi_url)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        bill.qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        buffer.close()
        bill.save()

        generated_count += 1

    messages.success(request, f"{generated_count} bills generated or updated successfully.")
    return redirect('owner:generate_bill_view')


from django.shortcuts import render

from django.shortcuts import render
from .models import MonthlyBill, CustomerProfile
from datetime import datetime
from django.utils.timezone import now
from calendar import monthrange

def generate_bill_view(request):
    customers = CustomerProfile.objects.all()
    current_time = now()
    month_start = datetime(current_time.year, current_time.month, 1)

    # Fetch latest bills for the current month
    bills = MonthlyBill.objects.filter(month=month_start).select_related('customer')

    return render(request, 'owner/generate_bill.html', {
        'customers': customers,
        'bills': bills,
        'month_str': month_start.strftime('%B %Y'),
    })


def confirm_payment(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id, customer=request.user.customer)
    if request.method == "POST":
        bill.is_paid = True
        bill.payment_time = now()
        bill.save()
        messages.success(request, "Payment confirmed. Thank you!")
    return redirect('customer:bill_history')


from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.shortcuts import get_object_or_404
from .models import MonthlyBill


def download_bill_pdf(request, bill_id):
    bill = MonthlyBill.objects.select_related('customer').get(id=bill_id)
    template = get_template("owner/bill_pdf_template.html")

    html = template.render({'bill': bill})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Bill_{bill.customer.user.username}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    return response


def view_bill_detail(request, bill_id):
    bill = MonthlyBill.objects.select_related('customer').get(id=bill_id)
    owner = OwnerProfile.objects.first()  # Assuming only one owner

    return render(request, 'owner/view_bill.html', {
        'bill': bill,
        'owner': owner,
    })

