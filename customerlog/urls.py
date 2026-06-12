from django.urls import path
from . import views
from .views import manage_daily_schedule, cancel_delivery, confirm_delivery, place_bulk_order, generate_monthly_bill, \
    view_all_bills, pay_bill, help_chat, chat_history

urlpatterns = [
    path('login/', views.customer_login_view, name='customer_login'),
    path('dashboard/', views.customer_dashboard_view, name='customer_dashboard'),
    path('logout/', views.customer_logout_view, name='customer_logout'),
    path('schedule/', manage_daily_schedule, name='manage_schedule'),
    path('delivery/<int:log_id>/cancel/', cancel_delivery, name='cancel_delivery'),
    path('delivery/<int:log_id>/confirm/', confirm_delivery, name='confirm_delivery'),
    path('bulk-order/', place_bulk_order, name='place_bulk_order'),
    path('generate-bill/', generate_monthly_bill, name='generate_bill'),
    path('bills/', views.view_all_bills, name='view_bills'),
    path('bills/confirm_payment/<int:bill_id>/', views.confirm_payment, name='confirm_payment'),
    path('pay-bill/<int:bill_id>/', views.pay_bill, name='pay_bill'),
    path('help-chat/', help_chat, name='help_chat'),

    path('chat-history/', chat_history, name='chat_history'),
    path('request-modification/<int:log_id>/', views.request_modification, name='request_modification'),
path('view-bill/<int:bill_id>/', views.view_bill_detail, name='view_bill_detail'),

]
