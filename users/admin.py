from django.contrib import admin
from .models import *
@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = ('userID', 'email', 'password', 'is_active',  'is_staff', 'is_superuser', 'is_dean', 'is_headdept', 'is_faculty', 'is_student')  
    search_fields = ('userID', 'email')

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('facultyID', 'name', 'title', 'department')
    search_fields = ('facultyID', 'title', 'department')

@admin.register(Manuscript)
class ManuscriptAdmin(admin.ModelAdmin):
    list_display = ('manuscriptID', 'title', 'description', 'pdf', 'created_at')
    search_fields = ('title', 'description')

@admin.register(ApplicationDefense)
class ApplicationDefenseAdmin(admin.ModelAdmin):
    list_display = (
        'applicationID', 'user', 'department', 'lead_researcher', 'lead_contactno',
        'co_researcher', 'co_researcher1', 'co_researcher2', 'co_researcher3', 'co_researcher4',
        'research_title', 'datetime_defense', 'place_defense',
        'panel_chair', 'adviser', 'panel1', 'panel2', 'panel3',
        'documenter', 'pdf_file', 'created_at'
    )
    search_fields = (
        'department', 'lead_researcher', 'research_title',
        'panel_chair', 'adviser', 'panel1', 'panel2', 'panel3', 'documenter'
    )

@admin.register(PanelDefense)
class PanelDefenseAdmin(admin.ModelAdmin):
    list_display = (
        'panelID', 'user', 'research_title', 'lead_researcher',
        'co_researcher', 'co_researcher1', 'co_researcher2', 'co_researcher3', 'co_researcher4',
        'adviser', 'panel_chair', 'panel1', 'panel2', 'panel3', 'pdf_file', 'created_at'
    )
    search_fields = (
        'research_title', 'lead_researcher',
        'panel_chair', 'adviser', 'panel1', 'panel2', 'panel3'
    )
    

