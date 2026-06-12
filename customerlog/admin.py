
from django.contrib import admin

from .models import (
 DailySchedule,
 BulkOrder, HelpChatLog
)




# --------------------------
# Register Other Models
# --------------------------

@admin.register(DailySchedule)
class DailyScheduleAdmin(admin.ModelAdmin):
    list_display = ('customer', 'water_can', 'quantity_per_day', 'start_date', 'delivery_time', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('customer__username',)



@admin.register(BulkOrder)
class BulkOrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'event_name', 'quantity', 'delivery_date', 'delivery_time', 'status')
    list_filter = ('status',)
    search_fields = ('customer__username', 'event_name')


@admin.register(HelpChatLog)
class HelpChatLogAdmin(admin.ModelAdmin):
    list_display = ('customer', 'question', 'timestamp')
    search_fields = ('customer__username', 'question')