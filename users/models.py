from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin
)

# Custom User Manager
class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email).lower()
        extra_fields.setdefault('is_active', True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Creates and returns a superuser with all privileges."""
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)  # Required for Django Admin access
        extra_fields.setdefault("is_superuser", True)  # Grants all permissions

        extra_fields.setdefault("is_dean", False)
        extra_fields.setdefault("is_headdept", False)
        extra_fields.setdefault("is_faculty", False)
        extra_fields.setdefault("is_student", False)  # Superusers are not students

        return self.create_user(email, password, **extra_fields)

# Custom User Model
class UserAccount(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, max_length=255)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Required for Django Admin
    is_superuser = models.BooleanField(default=False)
    is_dean = models.BooleanField(default=False)
    is_headdept = models.BooleanField(default=False)
    is_faculty = models.BooleanField(default=False)
    is_student = models.BooleanField(default=True)  # Default role is student

    objects = UserAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

#Submission and Viewing of Manuscript
class Manuscript(models.Model):
    first_name = models.CharField(max_length=255, null=True)  # Required field
    last_name = models.CharField(max_length=255, null=True)   # Required field
    title = models.CharField(max_length=200, help_text="Title of the manuscript")
    description = models.TextField(blank=True, help_text="Brief description or abstract of the manuscript")  
    pdf = models.FileField(upload_to='manuscripts/', help_text="Upload the PDF file here")
    created_at = models.DateTimeField(default=timezone.now, help_text="Timestamp of submission")

    class Meta:
        verbose_name = "Manuscript"
        verbose_name_plural = "Manuscripts"
        ordering = ['-created_at']  # Show most recent first

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.title}"

    @property
    def filename(self):
        """ Returns the name of the uploaded PDF file. """
        return self.pdf.name.split('/')[-1]

class ApplicationDefense(models.Model):
    first_name = models.CharField(max_length=255, null=True)  # Allow NULL values temporarily
    last_name = models.CharField(max_length=255, null=True)   # Allow NULL values temporarily
    docx_file = models.FileField(upload_to='generated_documents/')
    pdf_file = models.FileField(upload_to='generated_documents/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Application Defense"
        verbose_name_plural = "Application Defenses"

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.pdf_file.name}"