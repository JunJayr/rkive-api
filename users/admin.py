from django.contrib import admin
from .models import UserAccount, Faculty, Manuscript, ApplicationDefense, PanelDefense, SubmissionReview

class UserAccountAdmin(admin.ModelAdmin):
    list_display = ('userID', 'email', 'password', 'is_active', 'is_staff', 'is_superuser', 'is_dean', 'is_headdept', 'is_faculty', 'is_student')  
    search_fields = ('userID', 'email')

class FacultyAdmin(admin.ModelAdmin):
    list_display = ('facultyID', 'name', 'title', 'department')
    search_fields = ('facultyID', 'title', 'department')

class ManuscriptAdmin(admin.ModelAdmin):
    list_display = ('manuscriptID', 'title', 'description', 'pdf', 'created_at')
    search_fields = ('title', 'description')

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

class SubmissionReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewID', 'reviewer', 'application_defense', 'panel_defense', 'status', 'reviewed_at')
    search_fields = ('reviewer__name', 'application_defense__research_title', 'panel_defense__research_title')
    list_filter = ('status', 'reviewed_at')

admin.site.register(UserAccount, UserAccountAdmin)
admin.site.register(Faculty, FacultyAdmin)
admin.site.register(Manuscript, ManuscriptAdmin)
admin.site.register(ApplicationDefense, ApplicationDefenseAdmin)
admin.site.register(PanelDefense, PanelDefenseAdmin)
admin.site.register(SubmissionReview, SubmissionReviewAdmin)
