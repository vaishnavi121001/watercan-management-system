
from customerlog.models import DailySchedule, BulkOrder
from owner.models import DeliveryBoyProfile, DailyDeliveryLog
from .models import DeliveryProof
from .forms import DeliveryProofForm, DeliveryLoginForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q


@login_required
def dashboard(request):
    delivery_boy = get_object_or_404(DeliveryBoyProfile, user=request.user)

    today = timezone.now().date()
    now = timezone.now()
    first_day_of_month = now.replace(day=1)

    # Get today's scheduled deliveries
    deliveries = DailyDeliveryLog.objects.filter(
        delivery_boy=delivery_boy,
        delivery_date=today
    )

    # Separate scheduled and delivered
    scheduled = deliveries.filter(status="Scheduled")
    delivered = deliveries.filter(Q(status="Confirmed") | Q(status="Auto-Confirmed"))

    # Counts
    today_count = scheduled.count()
    monthly_orders = DailyDeliveryLog.objects.filter(
        delivery_boy=delivery_boy,
        delivery_date__gte=first_day_of_month
    ).count()

    # Bulk orders with delivery proof
    bulk_orders = BulkOrder.objects.filter(
        delivery_boy=delivery_boy
    ).count()

    # Completed bulk orders with proof
    completed_bulk_with_proof = BulkOrder.objects.filter(
        delivery_boy=delivery_boy,
        delivery_date=today,
        deliveryproof__isnull=False
    )

    context = {
        'delivery_boy': delivery_boy,
        'pending': scheduled,
        'completed': delivered,
        'total_today': today_count,
        'monthly_orders': monthly_orders,
        'bulk_orders': bulk_orders,
        'pending_logs': scheduled[:5],
        'delivered_logs': delivered[:5],
        'completed_bulk': completed_bulk_with_proof[:5],
    }
    return render(request, 'delivery/dashboard.html', context)

from django.shortcuts import render
from django.utils.timezone import now

from calendar import monthrange


def get_monthly_order_cans(delivery_boy):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    end_of_month = today.replace(day=monthrange(today.year, today.month)[1])

    # Get all active daily schedules for customers assigned to this delivery boy
    schedules = DailySchedule.objects.filter(
        customer__assigned_delivery_boy=delivery_boy,
        is_active=True,
        start_date__lte=end_of_month
    )

    total_cans = 0
    for s in schedules:
        effective_start = max(s.start_date, start_of_month)
        days = (end_of_month - effective_start).days + 1
        total_cans += days * s.quantity_per_day

    return total_cans

from django.contrib.auth.decorators import login_required

@login_required
def monthly_orders_detail(request):
    delivery_boy = get_object_or_404(DeliveryBoyProfile, user=request.user)

    start_month = now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    deliveries = DailyDeliveryLog.objects.filter(
        created_at__gte=start_month,
        delivery_boy=delivery_boy  # ✅ Filter by the logged-in delivery boy
    )

    today = now().date()
    for d in deliveries:
        d.delivered_today = (d.status == 'Delivered')

    context = {
        'deliveries': deliveries,
        'title': 'Monthly Orders'
    }
    return render(request, 'delivery/orders_detail.html', context)


@login_required
def bulk_orders_detail(request):
    delivery_boy = get_object_or_404(DeliveryBoyProfile, user=request.user)
    today = timezone.now().date()

    # Only show today's orders
    bulk_orders = BulkOrder.objects.filter(delivery_boy=delivery_boy)

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = get_object_or_404(BulkOrder, id=order_id, delivery_boy=delivery_boy)
        order.status = 'Delivered'
        order.confirmed_by_delivery_boy = True
        order.save()
        return redirect('delivery:bulk_orders_detail')

    return render(request, 'delivery/bulk_orders.html', {'bulk_orders': bulk_orders})


# URL pattern: path('mark-delivered/<str:type>/<int:id>/', views.mark_delivered, name='mark_delivered')
@login_required
def mark_delivered(request, type, id):
    if type == 'daily':
        delivery = get_object_or_404(DailyDeliveryLog, id=id)
        if delivery.delivery_boy.user != request.user:
            messages.error(request, "🚫 Unauthorized action.")
            return redirect('delivery:dashboard')
        try:
            proof_instance = DeliveryProof.objects.get(daily_delivery=delivery)
        except DeliveryProof.DoesNotExist:
            proof_instance = None
    elif type == 'bulk':
        delivery = get_object_or_404(BulkOrder, id=id)
        if delivery.delivery_boy.user != request.user:
            messages.error(request, "🚫 Unauthorized action.")
            return redirect('delivery:dashboard')
        try:
            proof_instance = DeliveryProof.objects.get(bulk_order=delivery)
        except DeliveryProof.DoesNotExist:
            proof_instance = None
    else:
        messages.error(request, "Invalid delivery type.")
        return redirect('delivery:dashboard')

    if request.method == 'POST':
        form = DeliveryProofForm(request.POST, request.FILES, instance=proof_instance)
        if form.is_valid():
            proof = form.save(commit=False)
            if type == 'daily':
                proof.daily_delivery = delivery
                water_can = delivery.schedule.water_can
            else:
                proof.bulk_order = delivery
                water_can = delivery.water_can

            delivered_cans = form.cleaned_data['cans_delivered']
            empty_received = form.cleaned_data['cans_received_empty']

            if water_can.current_stock >= delivered_cans:
                water_can.current_stock -= delivered_cans
                water_can.current_stock += empty_received
                water_can.save()

                proof.save()

                if type == 'daily':
                    delivery.status = 'Delivered'
                    delivery.delivery_time = timezone.localtime(timezone.now())  # Optional
                else:
                    delivery.status = 'Delivered'
                    delivery.confirmed_by_delivery_boy = True

                delivery.save()
                messages.success(request, "✅ Delivery marked as complete. Stock updated.")
            else:
                messages.error(request, f"Only {water_can.current_stock} cans available. Cannot deliver {delivered_cans}.")
                return redirect('delivery:dashboard')

            return redirect('delivery:dashboard')
    else:
        form = DeliveryProofForm(instance=proof_instance)

    return render(request, 'delivery/mark_delivered.html', {
        'form': form,
        'delivery': delivery,
        'type': type,
    })

def login_delivery_boy(request):
    if request.method == 'POST':
        form = DeliveryLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('delivery:dashboard')
            else:
                messages.error(request, "Invalid credentials. Please try again.")
    else:
        form = DeliveryLoginForm()
    return render(request, 'delivery/login.html', {'form': form})


def logout_delivery_boy(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('delivery:login')
