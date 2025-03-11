from django.contrib import admin
from .models import UserAccount, Manuscript, ApplicationDefense, PanelDefense

@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'is_active',  'is_staff', 'is_superuser', 'is_dean', 'is_headdept', 'is_faculty', 'is_student')  
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('is_superuser', 'is_dean', 'is_headdept', 'is_faculty', 'is_student')

@admin.register(Manuscript)
class ManuscriptAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'title', 'description', 'pdf', 'created_at')
    search_fields = ('title', 'description')

@admin.register(ApplicationDefense)
class ApplicationDefenseAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 'last_name', 'department', 'lead_researcher', 'lead_contactno',
        'co_researcher', 'co_researcher1', 'co_researcher2', 'co_researcher3', 'co_researcher4',
        'research_title', 'datetime_defense', 'place_defense',
        'panel_chair', 'adviser', 'panel1', 'panel2', 'panel3',
        'documenter', 'pdf_file', 'created_at'
    )
    
    search_fields = (
        'first_name', 'last_name', 'department', 'lead_researcher', 'research_title',
        'panel_chair', 'adviser', 'panel1', 'panel2', 'panel3', 'documenter'
    )
    
    list_filter = ('department', 'datetime_defense', 'place_defense', 'created_at')

@admin.register(PanelDefense)
class PanelDefenseAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'pdf_file', 'created_at')
    search_fields = ('title', 'description')
