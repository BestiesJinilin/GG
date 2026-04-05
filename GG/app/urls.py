from django.urls import path
from . import views

urlpatterns = [
    path('',views.login_view,name='login'),
    path('login/',views.login_view,name='login'),
    path('homepage/',views.homepage_view,name='homepage'),
    path('add-client/',views.add_client_view,name='add-client'),
    path('records/',views.records_view,name='records'),
    path('client-details/<int:pk>/',views.client_details_view,name='client-details'),
    path('edit-details/<int:pk>/',views.edit_details_view,name='edit-details'),
    path('delete-client/<int:pk>/',views.delete_client_view,name='delete-client'),
    path('add-payment/<int:pk>/',views.add_payment_view,name='add-payment'),
    path('payment-history/<int:pk>/',views.payment_history_view,name='payment-history'),
    path('monitor/',views.monitor_view,name='monitor'),
    path('logout/',views.logout,name='logout'),
    path('plan/<int:pk>/',views.plan_get,name='plan'),
    path('plan/',views.plan_view,name='plan'),
]
