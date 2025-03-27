from django.db import models
from django.conf import settings
from django.utils import timezone
from .managers import UserAccountManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

class UserAccount(AbstractBaseUser, PermissionsMixin):
    userID = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True, max_length=255)
    password = models.CharField(max_length=100)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_dean = models.BooleanField(default=False)
    is_headdept = models.BooleanField(default=False)
    is_faculty = models.BooleanField(default=False)
    is_student = models.BooleanField(default=True)
    
    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "User Account"
        verbose_name_plural = "User Accounts"

    def __str__(self):
        return self.email

class Faculty(models.Model):
    facultyID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)

class Manuscript(models.Model):
    manuscriptID = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200, help_text="Title of the manuscript")
    description = models.TextField(blank=True, help_text="Brief description or abstract of the manuscript")  
    pdf = models.FileField(upload_to='manuscripts/', help_text="Upload the PDF file here")
    created_at = models.DateTimeField(default=timezone.now, help_text="Timestamp of submission")
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name="manuscripts")

    class Meta:
        verbose_name = "Manuscript"
        verbose_name_plural = "Student Manuscripts"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class ApplicationDefense(models.Model):
    applicationID = models.AutoField(primary_key=True)
    department = models.CharField(max_length=255, null=True, blank=True)
    research_title = models.TextField(null=True, blank=True)
    lead_researcher = models.CharField(max_length=255, null=True, blank=True)
    lead_contactno = models.CharField(max_length=15, null=True, blank=True)
    co_researcher = models.CharField(max_length=255, blank=True, null=True)
    co_researcher1 = models.CharField(max_length=255, blank=True, null=True)
    co_researcher2 = models.CharField(max_length=255, blank=True, null=True)
    co_researcher3 = models.CharField(max_length=255, blank=True, null=True)
    co_researcher4 = models.CharField(max_length=255, blank=True, null=True)
    datetime_defense = models.CharField(max_length=255,null=True, blank=True)
    place_defense = models.CharField(max_length=255, null=True, blank=True)
    adviser = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="application_adviser")
    panel_chair = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="application_chair")
    panel1 = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="application_panel1")
    panel2 = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="application_panel2")
    panel3 = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="application_panel3")
    documenter = models.CharField(max_length=255, null=True, blank=True)
    pdf_file = models.FileField(upload_to='defense_application/', blank=True, null=True)    
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name="application_defenses")

    class Meta:
        verbose_name = "Application Defense"
        verbose_name_plural = "Student Application Defenses"

    def __str__(self):
        return self.research_title

class PanelDefense(models.Model):
    panelID = models.AutoField(primary_key=True)
    research_title = models.TextField(blank=True, null=True)
    lead_researcher = models.CharField(max_length=255, blank=True, null=True)
    co_researcher = models.CharField(max_length=255, blank=True, null=True)
    co_researcher1 = models.CharField(max_length=255, blank=True, null=True)
    co_researcher2 = models.CharField(max_length=255, blank=True, null=True)
    co_researcher3 = models.CharField(max_length=255, blank=True, null=True)
    co_researcher4 = models.CharField(max_length=255, blank=True, null=True)
    adviser = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="panel_adviser")
    panel_chair = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="panel_chair")
    panel1 = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="panel_panel1")
    panel2 = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="panel_panel2")
    panel3 = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="panel_panel3")
    docx_file = models.FileField(upload_to='panel_nomination/')
    pdf_file = models.FileField(upload_to='panel_nomination/')
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name="panel_defenses")

    class Meta:
        verbose_name = "Panel Defense"
        verbose_name_plural = "Student Panel Defenses"

    def __str__(self):
        return self.research_title


class SubmissionReview(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    reviewID = models.AutoField(primary_key=True)
    reviewer = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="reviews")
    application_defense = models.ForeignKey(ApplicationDefense, on_delete=models.CASCADE, null=True, blank=True, related_name="reviews")
    panel_defense = models.ForeignKey(PanelDefense, on_delete=models.CASCADE, null=True, blank=True, related_name="reviews")
    comments = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Submission Review"
        verbose_name_plural = "Submission Reviews"

    def __str__(self):
        return f"Review by {self.reviewer.name} - {self.status}"
