from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login', views.login_view, name='login'),
    path('homepage', views.homepage_view, name='homepage'),
    path('add-payment/<int:pk>/', views.add_payment_view, name='add-payment'),
    path('add-client', views.add_client_view, name='add-client'),
    path('client-details/<int:pk>/', views.client_details_view, name='client-details'),
    path('edit-details/<int:pk>/', views.edit_details_view, name='edit-details'),
    path('monitor', views.monitor_view, name='monitor'),
    path('payment-history', views.payment_history_view, name='payment-history'),
    path('records', views.records_view, name='records'),
    path('logout', views.logout, name='logout'),
]