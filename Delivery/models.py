from django.db import models

from customerlog.models import BulkOrder
from owner.models import DailyDeliveryLog

class DeliveryProof(models.Model):
    daily_delivery = models.OneToOneField(
        DailyDeliveryLog, on_delete=models.CASCADE, null=True, blank=True
    )
    bulk_order = models.OneToOneField(
        BulkOrder, on_delete=models.CASCADE, null=True, blank=True
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)
    cans_delivered = models.PositiveIntegerField(default=0)
    cans_received_empty = models.PositiveIntegerField(default=0)

    def __str__(self):
        if self.daily_delivery:
            return f"Proof for Daily Delivery - {self.daily_delivery.schedule.customer.user.username} (ID: {self.daily_delivery.id})"
        elif self.bulk_order:
            return f"Proof for Bulk Order - {self.bulk_order.customer.user.username} (ID: {self.bulk_order.id})"
        return "Unlinked Delivery Proof"
