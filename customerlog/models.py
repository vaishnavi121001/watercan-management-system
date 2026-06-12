from django.db import models

from owner.models import DeliveryBoyProfile
from watercan import settings


# DO NOT IMPORT CustomerProfile or WaterCan directly
# Use string references instead


class DailySchedule(models.Model):
    customer = models.ForeignKey('owner.CustomerProfile', on_delete=models.CASCADE)
    water_can = models.ForeignKey('owner.WaterCan', on_delete=models.SET_NULL, null=True)
    quantity_per_day = models.PositiveIntegerField()
    start_date = models.DateField()
    delivery_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    delivery_boy = models.ForeignKey(DeliveryBoyProfile, on_delete=models.SET_NULL, null=True, blank=True)
    assigned = models.BooleanField(default=False)

    def __str__(self):
        return f"Schedule for {self.customer.user.username}"


class BulkOrder(models.Model):
    customer = models.ForeignKey('owner.CustomerProfile', on_delete=models.CASCADE)
    water_can = models.ForeignKey('owner.WaterCan', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    delivery_date = models.DateField()
    delivery_time = models.TimeField()
    event_name = models.CharField(max_length=100, blank=True)
    delivery_address = models.TextField()
    delivery_boy = models.ForeignKey('owner.DeliveryBoyProfile', on_delete=models.SET_NULL, null=True, blank=True)  # New field
    status = models.CharField(max_length=20, default='Pending')  # Pending / Delivered / Cancelled
    confirmed_by_delivery_boy = models.BooleanField(default=False)  # New field

    def __str__(self):
        return f"{self.customer.user.username} - {self.event_name or 'Bulk Order'}"



class HelpChatLog(models.Model):
    customer = models.ForeignKey('owner.CustomerProfile', on_delete=models.CASCADE)
    question = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat with {self.customer.username} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
