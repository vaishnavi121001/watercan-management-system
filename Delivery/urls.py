from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'delivery'

urlpatterns = [
                  path('', views.login_delivery_boy, name='login'),  # Root URL leads to login page

                  path('dashboard/', views.dashboard, name='dashboard'),
                  # urls.py
                  path('mark-delivered/<str:type>/<int:id>/', views.mark_delivered, name='mark_delivered'),

                  path('logout/', views.logout_delivery_boy, name='logout'),
                  path('monthly-orders/', views.monthly_orders_detail, name='monthly_orders_detail'),
                  path('bulk-orders/', views.bulk_orders_detail, name='bulk_orders_detail'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
