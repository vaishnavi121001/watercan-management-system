app_name = 'owner'

from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.custom_login, name='custom_login'),
    path('', views.home_page, name='home'),
    path('owner_dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('logout/', views.logout_view, name='logout'),

    path('add_customer/', views.add_customer, name='add_customer'),
    path('view-customers/', views.view_customers, name='view_customers'),

    path('view-delivery-boys/', views.view_delivery_boys, name='view_delivery_boys'),
    path('add-delivery-boy/', views.add_delivery_boys, name='add_delivery_boy'),
    path('cans-stock/', views.cans_stock_view, name='cans_stock'),
    path('add/', views.add_inventory, name='add_inventory'),
    path('schedule-list/', views.schedule_list_view, name='schedule_list'),

    path('customers/update/<int:pk>/', views.update_customer, name='update_customer'),
    path('delivery-boy/update/<int:delivery_boy_id>/', views.update_delivery_boy, name='update_delivery_boy'),

    path('delivery-boy/delete/<int:delivery_boy_id>/', views.delete_delivery_boy, name='delete_delivery_boy'),
    path('customers/delete/<int:customer_id>/', views.delete_customer, name='delete_customer'),
    path('assign-delivery/', views.assign_delivery, name='assign_delivery'),
    path('assigned-deliveries/', views.assigned_deliveries_view, name='assigned_deliveries'),

    path('bulk-orders/', views.bulk_orders_list, name='bulk_orders_list'),
    path('bulk-orders/assign/<int:order_id>/', views.assign_bulk_order_view, name='assign_bulk_order'),
    path('view-delivered-cans/', views.view_delivered_cans, name='view_delivered_cans'),
    path('view-returned-cans/', views.view_returned_cans, name='view_returned_cans'),
    path('generate-logs/', views.manual_generate_logs, name='generate_logs'),

    path('update-profile/', views.update_owner_profile, name='update_profile'),
    path('generate-bills/', views.generate_all_bills, name='generate_all_bills'),

    path('generate-bill/', views.generate_bill_view, name='generate_bill_view'),
    path('confirm-payment/<int:bill_id>/', views.confirm_payment, name='confirm_payment'),
path('download-bill/<int:bill_id>/', views.download_bill_pdf, name='download_bill_pdf'),
path('view-bill/<int:bill_id>/', views.view_bill_detail, name='view_bill_detail'),

]
