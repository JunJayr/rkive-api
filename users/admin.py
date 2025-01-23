from django.contrib import admin
from .models import UserAccount

@admin.register(UserAccount)
class UserAccount(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser')  
    search_fields = ('first_name',)



