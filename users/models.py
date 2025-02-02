from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin
)

#User Creation
class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        email = email.lower()

        user = self.model(
            email=email,
            **kwargs
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **kwargs):
        user = self.create_user(
            email,
            password=password,
            **kwargs
        )

        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user

#User Viewing
class UserAccount(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, max_length=255)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

#Submission and Viewing of Manuscript
class Manuscript(models.Model):
    """
    Model to store research, thesis, or capstone manuscripts.
    """
    title = models.CharField(max_length=200, help_text="Title of the manuscript")
    description = models.TextField(blank=True, help_text="Brief description or abstract of the manuscript")  # Added field
    pdf = models.FileField(upload_to='manuscripts/', help_text="Upload the PDF file here")
    created_at = models.DateTimeField(default=timezone.now, help_text="Timestamp of submission")

    class Meta:
        verbose_name = "Manuscript"
        verbose_name_plural = "Manuscripts"
        ordering = ['-created_at']  # Show most recent first

    def __str__(self):
        return self.title

    @property
    def filename(self):
        """
        Returns the name of the uploaded PDF file.
        Example: If file is `manuscripts/my_thesis.pdf`, returns `my_thesis.pdf`
        """
        return self.pdf.name.split('/')[-1]