# owner/utils.py
from datetime import date
from customerlog.models import DailySchedule
from owner.models import DailyDeliveryLog

def generate_daily_logs():
    today = date.today()
    schedules = DailySchedule.objects.filter(assigned=True)

    for schedule in schedules:
        if not DailyDeliveryLog.objects.filter(schedule=schedule, delivery_date=today).exists():
            DailyDeliveryLog.objects.create(
                schedule=schedule,
                delivery_boy=schedule.delivery_boy,
                delivery_date=today,
                status='Scheduled'
            )
