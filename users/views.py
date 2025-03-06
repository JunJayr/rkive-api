import os
import pythoncom

from docxtpl import DocxTemplate
from docx2pdf import convert

from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Manuscript
from datetime import datetime
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.conf import settings
from djoser.social.views import ProviderAuthView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

#AUTHENTICATION
class CustomProviderAuthView(ProviderAuthView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 201:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')

            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )
            response.set_cookie(
                'refresh',
                refresh_token,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

        return response

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')

            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )
            response.set_cookie(
                'refresh',
                refresh_token,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

        return response

class UserRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response({
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "is_dean": user.is_dean,
            "is_headdept": user.is_headdept,
            "is_faculty": user.is_faculty,
            "is_student": user.is_student,
        })

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh')

        if refresh_token:
            request.data['refresh'] = refresh_token

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get('access')

            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

        return response

class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        access_token = request.COOKIES.get('access')

        if access_token:
            request.data['token'] = access_token

        return super().post(request, *args, **kwargs)

class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access')
        response.delete_cookie('refresh')

        return response

#Defense Application Form / User
class ApplicationDocxView(APIView):
    def post(self, request, *args, **kwargs):
        context = request.data
        template_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_application.docx'
        )

        if not os.path.exists(template_path):
            return JsonResponse({"error": "Template file not found."}, status=404)
        
        try:
            # Initialize COM before calling `convert`
            pythoncom.CoInitialize()

            # 1. Load and render the document
            doc = DocxTemplate(template_path)
            doc.render(context)

            # 2. Generate a unique filename for the .docx
            docx_filename = f"Application-for-Oral-Defense_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            docx_file_path = os.path.join(
                settings.MEDIA_ROOT, "generated_documents", docx_filename
            )
            os.makedirs(os.path.dirname(docx_file_path), exist_ok=True)
            doc.save(docx_file_path)

            # 3. Convert the .docx to .pdf (Ensure COM is initialized)
            pdf_filename = docx_filename.replace('.docx', '.pdf')
            pdf_file_path = os.path.join(
                settings.MEDIA_ROOT, "generated_documents", pdf_filename
            )
            convert(docx_file_path, pdf_file_path)

            # 4. Remove the .docx file (if not needed anymore)
            os.remove(docx_file_path)

            # 5. Serve the PDF as an inline file so the user can preview/download
            pdf_file = open(pdf_file_path, 'rb')
            response = FileResponse(pdf_file, content_type='application/pdf')

            # Inline content-disposition allows preview in the browser and user download from there
            response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'

            return response

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

        finally:
            # Uninitialize COM to free up resources
            pythoncom.CoUninitialize()

#Defense Application Form / Admin
class ApplicationAdminDocxView(APIView):
    def post(self, request, *args, **kwargs):
        context = request.data
        template_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_application.docx'
        )

        # Check if the template file exists
        if not os.path.exists(template_path):
            return JsonResponse({"error": "Template file not found."}, status=404)
        
        try:
            # 1. Load the document
            doc = DocxTemplate(template_path)

            # 2. Create a selective context with only revNo and date from the request data
            selective_context = {
                'revNo': context.get('revNo', '{{revNo}}'),  # Use provided value or keep original placeholder
                'date': context.get('date', '{{date}}')      # Use provided value or keep original placeholder
            }

            # 3. Render the document with the selective context
            doc.render(selective_context)

            # 4. Save the rendered document back to the same file, overwriting the original
            doc.save(template_path)

            # 5. Serve the updated .docx file as an inline file for preview/download
            docx_file = open(template_path, 'rb')
            response = FileResponse(docx_file, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'inline; filename="template_application.docx"'

            return response

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

#Panel Application Form / User
class PanelDocxView(APIView):
    def post(self, request, *args, **kwargs):
        context = request.data
        template_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_panel.docx'
        )

        if not os.path.exists(template_path):
            return JsonResponse({"error": "Template file not found."}, status=404)
        
        try:
            # Initialize COM before using `convert`
            pythoncom.CoInitialize()

            # 1. Render the document
            doc = DocxTemplate(template_path)
            doc.render(context)

            # 2. Generate a unique filename for the .docx
            docx_filename = f"IT-Nomination-of-Members-of-Oral-Examination-Panel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            docx_file_path = os.path.join(settings.MEDIA_ROOT, "generated_documents", docx_filename)
            os.makedirs(os.path.dirname(docx_file_path), exist_ok=True)
            doc.save(docx_file_path)

            # 3. Convert .docx to .pdf (Ensure COM is initialized)
            pdf_filename = docx_filename.replace('.docx', '.pdf')
            pdf_file_path = os.path.join(settings.MEDIA_ROOT, "generated_documents", pdf_filename)
            convert(docx_file_path, pdf_file_path)

            # 4. Remove the .docx file (optional)
            os.remove(docx_file_path)

            # 5. Serve the PDF as an inline file so the user can preview/download
            pdf_file = open(pdf_file_path, 'rb')
            response = FileResponse(pdf_file, content_type='application/pdf')

            # Inline content-disposition allows preview in the browser and user download from there
            response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'

            return response
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

        finally:
            pythoncom.CoUninitialize()  # Ensure COM is cleaned up

#Manuscript Submission
class ManuscriptSubmissionView(APIView):
    parser_classes = (MultiPartParser, FormParser)  # Allows file uploads

    def post(self, request, *args, **kwargs):
        title = request.data.get("title")
        description = request.data.get("description", "").strip()  # Optional description
        pdf = request.FILES.get("pdf")

        if not title or not pdf:
            return JsonResponse({"error": "Title and PDF file are required."}, status=400)

        # Save manuscript
        manuscript = Manuscript.objects.create(title=title, description=description, pdf=pdf)

        return JsonResponse({
            "message": "Manuscript submitted successfully",
            "id": manuscript.id,
            "title": manuscript.title,
            "description": manuscript.description,
            "pdf_url": request.build_absolute_uri(manuscript.pdf.url),
            "created_at": manuscript.created_at.strftime("%Y-%m-%d %H:%M:%S"),  # Convert to JSON-friendly format
        }, status=201)

    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('q', '').strip()

        # Filter manuscripts by title or description if search_query is provided
        manuscripts = Manuscript.objects.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        ) if search_query else Manuscript.objects.all()

        # Construct the response data
        data = [
            {
                "id": manuscript.id,
                "title": manuscript.title,
                "description": manuscript.description,
                "pdf_url": request.build_absolute_uri(manuscript.pdf.url),
                "created_at": manuscript.created_at.strftime("%Y-%m-%d %H:%M:%S"),  # JSON-friendly date
            }
            for manuscript in manuscripts
        ]

        return JsonResponse(data, safe=False, status=200)

class ManuscriptPdfView(APIView):
    def get(self, request, manuscript_id, *args, **kwargs):
        try:
            manuscript = Manuscript.objects.get(id=manuscript_id)
            pdf_path = manuscript.pdf.path  # Full path to the file
            response = FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="manuscript.pdf"'  # Ensure it opens in browser/Adobe

            return response
        except Manuscript.DoesNotExist:
            raise Http404("Manuscript not found.")

class DocumentCountView(APIView):
    def get(self, request, *args, **kwargs):
        generated_docs_path = os.path.join(settings.MEDIA_ROOT, "generated_documents")
        manuscripts_path = os.path.join(settings.MEDIA_ROOT, "manuscripts")

        # Count files in the "generated_documents" directory
        generated_docs_count = len(
            [f for f in os.listdir(generated_docs_path) if os.path.isfile(os.path.join(generated_docs_path, f))]
        )

        # Count files in the "manuscripts" directory
        manuscripts_count = len(
            [f for f in os.listdir(manuscripts_path) if os.path.isfile(os.path.join(manuscripts_path, f))]
        )

        return JsonResponse({
            "generated_documents_count": generated_docs_count,
            "manuscripts_count": manuscripts_count
        }, status=200)

class ListDocumentFilesView(APIView):
    def get(self, request, *args, **kwargs):
        base_generated_documents_path = os.path.join(settings.MEDIA_ROOT, 'generated_documents')
        base_manuscripts_path = os.path.join(settings.MEDIA_ROOT, 'manuscripts')

        # Function to list files in a directory
        def list_files_in_directory(directory_path):
            if os.path.exists(directory_path):
                return [file for file in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, file))]
            return []

        # List files in both directories
        generated_documents_files = list_files_in_directory(base_generated_documents_path)
        manuscripts_files = list_files_in_directory(base_manuscripts_path)

        return JsonResponse({
            "generated_documents_files": generated_documents_files,
            "manuscripts_files": manuscripts_files
        })

class ListUsersView(APIView):
    def get(self, request, *args, **kwargs):
        User = get_user_model()
        users = User.objects.all().values('id', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser', 'is_dean', 'is_headdept', 'is_faculty', 'is_student')
        return Response(list(users))

    def post(self, request, *args, **kwargs):
        User = get_user_model()
        data = request.data

        # Check if email already exists
        if User.objects.filter(email=data.get('email')).exists():
            return JsonResponse({"error": "Email already exists."}, status=400)

        # Check if password and repassword are provided and match
        password = data.get('password')
        repassword = data.get('repassword')

        if not password or not repassword:
            return JsonResponse({"error": "Both password and repassword are required."}, status=400)
        if password != repassword:
            return JsonResponse({"error": "Passwords do not match."}, status=400)

        # Create a new user
        user = User.objects.create(
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            email=data.get('email'),
            is_active=True  # Defaulting to active if not set
        )
        user.set_password(password)  # Set the password securely
        user.save()

        return JsonResponse({
            "message": "User created successfully",
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        }, status=201)


    def put(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        try:
            User = get_user_model()
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)

        user.first_name = request.data.get("first_name", user.first_name)
        user.last_name = request.data.get("last_name", user.last_name)
        user.email = request.data.get("email", user.email)
        user.is_active = request.data.get("is_active", user.is_active)
        user.is_staff = request.data.get("is_staff", user.is_staff)
        user.is_superuser = request.data.get("is_superuser", user.is_superuser)
        user.is_dean = request.data.get("is_dean", user.is_dean)
        user.is_headdept = request.data.get("is_headdept", user.is_headdept)
        user.is_faculty = request.data.get("is_faculty", user.is_faculty)
        user.is_student = request.data.get("is_student", user.is_student)
        user.save()

        return JsonResponse({
            "message": "User updated successfully",
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "is_dean": user.is_dean,
            "is_headdept": user.is_headdept,
            "is_faculty": user.is_faculty,
            "is_student": user.is_student,
        }, status=200)

    def delete(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        try:
            User = get_user_model()
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)

        user.delete()
        return JsonResponse({"message": "User deleted successfully."}, status=204)
