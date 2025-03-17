from django.db import models
from django.conf import settings
from django.utils import timezone
from .managers import UserAccountManager
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin
)

# Custom User Model
class UserAccount(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, max_length=255)
    password = models.CharField(max_length=100)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_dean = models.BooleanField(default=False)
    is_headdept = models.BooleanField(default=False)
    is_faculty = models.BooleanField(default=False)
    is_student = models.BooleanField(default=True)
    
    objects = UserAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "User Accounts"
        verbose_name_plural = "Accounts"

    def __str__(self):
        return self.email

#Submission and Viewing of Manuscript
class Manuscript(models.Model):
    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    title = models.CharField(max_length=200, help_text="Title of the manuscript")
    description = models.TextField(blank=True, help_text="Brief description or abstract of the manuscript")  
    pdf = models.FileField(upload_to='manuscripts/', help_text="Upload the PDF file here")
    created_at = models.DateTimeField(default=timezone.now, help_text="Timestamp of submission")

    class Meta:
        verbose_name = "Manuscript"
        verbose_name_plural = "Student Manuscripts"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def filename(self):
        """ Returns the name of the uploaded PDF file. """
        return self.pdf.name.split('/')[-1]

class Faculty(models.Model):
    name = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)  # Added department field

    def __str__(self):
        return self.name

class ApplicationDefense(models.Model):
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    department = models.CharField(max_length=255, null=True, blank=True)
    research_title = models.TextField(null=True, blank=True)
    lead_researcher = models.CharField(max_length=255, null=True, blank=True)
    lead_contactno = models.CharField(max_length=15, null=True, blank=True)
    co_researcher = models.CharField(max_length=255, blank=True, null=True)
    co_researcher1 = models.CharField(max_length=255, blank=True, null=True)
    co_researcher2 = models.CharField(max_length=255, blank=True, null=True)
    co_researcher3 = models.CharField(max_length=255, blank=True, null=True)
    co_researcher4 = models.CharField(max_length=255, blank=True, null=True)
    datetime_defense = models.CharField(max_length=255, blank=True, null=True)
    place_defense = models.CharField(max_length=255, null=True, blank=True)

    adviser = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="advised_applications")
    panel_chair = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="chaired_applications")
    panel1 = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="panel1_applications")
    panel2 = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="panel2_applications")
    panel3 = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="panel3_applications")
    
    documenter = models.CharField(max_length=255, null=True, blank=True)
    pdf_file = models.FileField(upload_to='defense_application/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Application Defense"
        verbose_name_plural = "Student Application Defenses"

    def __str__(self):
        return self.research_title

class PanelDefense(models.Model):
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    research_title = models.TextField(blank=True, null=True)
    lead_researcher = models.CharField(max_length=255, blank=True, null=True)
    co_researcher = models.CharField(max_length=255, blank=True, null=True)
    co_researcher1 = models.CharField(max_length=255, blank=True, null=True)
    co_researcher2 = models.CharField(max_length=255, blank=True, null=True)
    co_researcher3 = models.CharField(max_length=255, blank=True, null=True)
    co_researcher4 = models.CharField(max_length=255, blank=True, null=True)

    adviser = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="advised_panels")
    panel_chair = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="chaired_panels")
    panel1 = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="panel1_panels")
    panel2 = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="panel2_panels")
    panel3 = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="panel3_panels")

    docx_file = models.FileField(upload_to='panel_nomination/')
    pdf_file = models.FileField(upload_to='panel_nomination/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Panel Defense"
        verbose_name_plural = "Student Panel Defenses"

    def __str__(self):
        return self.research_title