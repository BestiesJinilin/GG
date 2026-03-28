from django.contrib import admin
from .models import ClientPersonalInfo, ClientStatus, UserLog, Beneficiary

# Register your models here.
admin.site.register(ClientPersonalInfo)
admin.site.register(ClientStatus)
admin.site.register(UserLog)
admin.site.register(Beneficiary)