from django.contrib import admin
from .models import UserAccount, Manuscript

@admin.register(UserAccount)
class UserAccount(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser')  
    search_fields = ('first_name',)

@admin.register(Manuscript)
class ManuscriptAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'pdf', 'created_at')
    search_fields = ('title', 'description')


