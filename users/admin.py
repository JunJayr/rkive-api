from django.contrib import admin
from .models import UserAccount

@admin.register(UserAccount)
class UserAccount(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser')  # Fields to display in the list view
    search_fields = ('last_name',)  # Enable search functionality
# Register your models here.
