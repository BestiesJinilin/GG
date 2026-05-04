from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.login_view,              name='login'),
    path('login/',                        views.login_view,              name='login'),
    path('homepage/',                     views.homepage_view,           name='homepage'),
    path('add-client/',                   views.add_client_view,         name='add-client'),
    path('records/',                      views.records_view,            name='records'),
    path('client-details/<int:pk>/',      views.client_details_view,     name='client-details'),
    path('edit-details/<int:pk>/',        views.edit_details_view,       name='edit-details'),
    path('delete-client/<int:pk>/',       views.delete_client_view,      name='delete-client'),
    path('add-payment/<int:pk>/',         views.add_payment_view,        name='add-payment'),
    path('payment-history/<int:pk>/',     views.payment_history_view,    name='payment-history'),
    path('monitor/',                      views.monitor_view,            name='monitor'),
    path('plan/<int:pk>/',                views.plan,                    name='plan'),
    path('employee/',                     views.employee_view,           name='employee'),
    path('add-employee/',                 views.add_employee_view,       name='add-employee'),
    path('details-employee/<int:pk>/',    views.details_employee_view,   name='details-employee'),
    path('edit-employee/<int:pk>/',       views.edit_employee_view,      name='edit-employee'),
    path('delete-employee/<int:pk>/',     views.delete_employee_view,    name='delete-employee'),
    path('logout/',                       views.logout,                  name='logout'),
    path('bookings/',                     views.bookings_view,           name='bookings'),
]
