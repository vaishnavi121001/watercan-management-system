from django.contrib import admin

# Register your models here.
from django.contrib import admin

from customerlog.models import DailySchedule
from .models import  CustomerProfile, MonthlyBill
from .models import  WaterCan


admin.site.register(CustomerProfile)

from django.contrib import admin
from .models import User, CustomerProfile, DeliveryBoyProfile

admin.site.register(User)

admin.site.register(DeliveryBoyProfile)


@admin.register(WaterCan)
class WaterCanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'total_cans_added')
    search_fields = ('name',)



from django.contrib import admin
from .models import DailyDeliveryLog

@admin.register(DailyDeliveryLog)
class DailyDeliveryLogAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'delivery_date', 'delivery_boy', 'status', 'confirmed_by_customer', 'confirmed_by_system', 'modified_quantity', 'created_at')
    list_filter = ('status', 'delivery_date', 'confirmed_by_customer', 'confirmed_by_system')
    search_fields = ('schedule__customer__username', 'delivery_boy__name')  # Adjust 'name' if your DeliveryBoy model uses a different field name
    readonly_fields = ('created_at',)

@admin.register(MonthlyBill)
class MonthlyBillAdmin(admin.ModelAdmin):
    list_display = ('customer', 'month', 'total_cans', 'amount_due', 'payment_status', 'generated_on')
    list_filter = ('payment_status',)
    search_fields = ('customer__username',)

