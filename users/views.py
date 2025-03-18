import os
import pythoncom
import zipfile 
from win32com.client import Dispatch

from io import BytesIO
from docxtpl import DocxTemplate
from docx2pdf import convert

from django.contrib.auth import get_user_model
from django.db.models import Q
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
from .models import ( 
    Manuscript, 
    ApplicationDefense,
    PanelDefense,
    Faculty,
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
        context = request.data  # JSON data from request
        user = request.user  # Authenticated user

        template_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_application.docx'
        )

        if not os.path.exists(template_path):
            return JsonResponse({"error": "Template file not found."}, status=404)

        try:
            pythoncom.CoInitialize()

            # Generate filenames
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            docx_filename = f"Application-for-Oral-Defense_{timestamp}.docx"
            pdf_filename = docx_filename.replace('.docx', '.pdf')

            # File paths
            docx_file_path = os.path.join(settings.MEDIA_ROOT, "defense_application", docx_filename)
            pdf_file_path = os.path.join(settings.MEDIA_ROOT, "defense_application", pdf_filename)

            os.makedirs(os.path.dirname(docx_file_path), exist_ok=True)

            # Function to fetch Faculty name by facultyID
            def get_faculty_name(facultyID):
                faculty = Faculty.objects.filter(facultyID=facultyID).first()
                return faculty.name if faculty else "Unknown"

            # Function to safely fetch Faculty objects
            def get_faculty_object(facultyID):
                return Faculty.objects.filter(facultyID=facultyID).first()

            # Preserve faculty IDs for saving, but fetch names for DOCX
            docx_context = context.copy()
            docx_context["panel_chair"] = get_faculty_name(context.get("panel_chair"))
            docx_context["adviser"] = get_faculty_name(context.get("adviser"))
            docx_context["panel1"] = get_faculty_name(context.get("panel1"))
            docx_context["panel2"] = get_faculty_name(context.get("panel2"))
            docx_context["panel3"] = get_faculty_name(context.get("panel3"))

            # Load and render DOCX template
            doc = DocxTemplate(template_path)
            doc.render(docx_context)
            doc.save(docx_file_path)

            # Convert DOCX to PDF (Using Microsoft Word COM Object)
            word = Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(docx_file_path)
            doc.SaveAs(pdf_file_path, FileFormat=17)  # 17 = wdFormatPDF
            doc.Close()
            word.Quit()

            # Save record in the database using faculty objects
            doc_record = ApplicationDefense.objects.create(
                user=user,
                department=context.get("department"),
                lead_researcher=context.get("lead_researcher"),
                lead_contactno=context.get("lead_contactno"),
                co_researcher=context.get("co_researcher"),
                co_researcher1=context.get("co_researcher1"),
                co_researcher2=context.get("co_researcher2"),
                co_researcher3=context.get("co_researcher3"),
                co_researcher4=context.get("co_researcher4"),
                research_title=context.get("research_title"),
                datetime_defense=context.get("datetime_defense"),
                place_defense=context.get("place_defense"),
                panel_chair=get_faculty_object(context.get("panel_chair")),
                adviser=get_faculty_object(context.get("adviser")),
                panel1=get_faculty_object(context.get("panel1")),
                panel2=get_faculty_object(context.get("panel2")),
                panel3=get_faculty_object(context.get("panel3")),
                documenter=context.get("documenter"),
                pdf_file=f"defense_application/{pdf_filename}",
            )

            # Remove DOCX file after conversion (optional)
            os.remove(docx_file_path)

            # Serve the PDF file
            pdf_file = open(pdf_file_path, 'rb')
            response = FileResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'

            return response

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

        finally:
            pythoncom.CoUninitialize()
            
class ApplicationAdminDocxView(APIView):
    def post(self, request, *args, **kwargs):
        context = request.data
        template_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_application_ISO.docx'  # Input template
        )
        output_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_application.docx'  # Output file
        )

        # Check if the template file exists
        if not os.path.exists(template_path):
            return JsonResponse({"error": "Template file (template_application_ISO.docx) not found."}, status=404)
        
        try:
            # 1. Read the .docx file as a ZIP archive and store its contents
            zip_data = {}
            with zipfile.ZipFile(template_path, 'r') as zip_ref:
                for item in zip_ref.infolist():
                    zip_data[item.filename] = zip_ref.read(item.filename)

            # 2. Find any XML file containing {{rev}} and {{date}}
            new_rev = context.get('rev', '{{rev}}')
            new_date = context.get('date', '{{date}}')
            updated = False

            for filename in zip_data.keys():
                if filename.endswith('.xml'):  # Check all XML files (headers, footers, document)
                    xml_content = zip_data[filename].decode('utf-8', errors='ignore')
                    if '{{rev}}' in xml_content or '{{date}}' in xml_content:
                        # Update the XML with new rev and date
                        updated_xml = xml_content.replace('{{rev}}', new_rev).replace('{{date}}', new_date)
                        zip_data[filename] = updated_xml.encode('utf-8')
                        updated = True

            if not updated:
                return JsonResponse({"error": "Could not find {{rev}} or {{date}} in any XML file."}, status=500)

            # 3. Create a new .docx file with the updated content
            output = BytesIO()
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                # Write all files
                for filename, content in zip_data.items():
                    zip_out.writestr(filename, content)

            # 4. Save the updated .docx to the output file
            with open(output_path, 'wb') as f:
                f.write(output.getvalue())

            # 5. Serve the updated .docx file as an inline file for preview/download
            docx_file = open(output_path, 'rb')
            response = FileResponse(docx_file, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'inline; filename="template_application.docx"'

            return response

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

#Panel Application Form / User
class PanelDocxView(APIView):
    def post(self, request, *args, **kwargs):
        context = request.data  # JSON data from request
        user = request.user  # Authenticated user

        template_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_panel.docx'
        )

        if not os.path.exists(template_path):
            return JsonResponse({"error": "Template file not found."}, status=404)

        try:
            pythoncom.CoInitialize()

            # Generate filenames
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            docx_filename = f"Panel-Nomination_{timestamp}.docx"
            pdf_filename = docx_filename.replace('.docx', '.pdf')

            # File paths
            docx_file_path = os.path.join(settings.MEDIA_ROOT, "panel_nomination", docx_filename)
            pdf_file_path = os.path.join(settings.MEDIA_ROOT, "panel_nomination", pdf_filename)

            os.makedirs(os.path.dirname(docx_file_path), exist_ok=True)

            # Function to fetch Faculty name by facultyID
            def get_faculty_name(facultyID):
                faculty = Faculty.objects.filter(facultyID=facultyID).first()
                return faculty.name if faculty else "Unknown"

            # Function to safely fetch Faculty objects
            def get_faculty_object(facultyID):
                return Faculty.objects.filter(facultyID=facultyID).first()

            # Preserve faculty IDs for saving, but fetch names for DOCX
            docx_context = context.copy()
            docx_context["adviser"] = get_faculty_name(context.get("adviser"))
            docx_context["panel_chair"] = get_faculty_name(context.get("panel_chair"))
            docx_context["panel1"] = get_faculty_name(context.get("panel1"))
            docx_context["panel2"] = get_faculty_name(context.get("panel2"))
            docx_context["panel3"] = get_faculty_name(context.get("panel3"))

            # Load and render DOCX template
            doc = DocxTemplate(template_path)
            doc.render(docx_context)
            doc.save(docx_file_path)

            # Convert DOCX to PDF
            word = Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(docx_file_path)
            doc.SaveAs(pdf_file_path, FileFormat=17)  # 17 = wdFormatPDF
            doc.Close()
            word.Quit()

            # Save record in the database using faculty objects
            panel_record = PanelDefense.objects.create(
                user=user,
                research_title=context.get("research_title"),
                lead_researcher=context.get("lead_researcher"),
                co_researcher=context.get("co_researcher"),
                co_researcher1=context.get("co_researcher1"),
                co_researcher2=context.get("co_researcher2"),
                co_researcher3=context.get("co_researcher3"),
                co_researcher4=context.get("co_researcher4"),
                adviser=get_faculty_object(context.get("adviser")),
                panel_chair=get_faculty_object(context.get("panel_chair")),
                panel1=get_faculty_object(context.get("panel1")),
                panel2=get_faculty_object(context.get("panel2")),
                panel3=get_faculty_object(context.get("panel3")),
                docx_file=f"panel_nomination/{docx_filename}",
                pdf_file=f"panel_nomination/{pdf_filename}",
            )

            # Remove DOCX file after conversion (optional)
            os.remove(docx_file_path)

            # Serve the PDF file
            pdf_file = open(pdf_file_path, 'rb')
            response = FileResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'

            return response

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

        finally:
            pythoncom.CoUninitialize()

#Panel Application Form / Admin
class PanelAdminDocxView(APIView):
    def post(self, request, *args, **kwargs):
        context = request.data
        template_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_panel_ISO.docx'  # Input template
        )
        output_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_panel.docx'  # Output file
        )

        # Check if the template file exists
        if not os.path.exists(template_path):
            return JsonResponse({"error": "Template file (template_panel_ISO.docx) not found."}, status=404)
        
        try:
            # 1. Read the .docx file as a ZIP archive and store its contents
            zip_data = {}
            with zipfile.ZipFile(template_path, 'r') as zip_ref:
                for item in zip_ref.infolist():
                    zip_data[item.filename] = zip_ref.read(item.filename)

            # 2. Find any XML file containing {{rev}} and {{date}}
            new_rev = context.get('rev', '{{rev}}')
            new_date = context.get('date', '{{date}}')
            updated = False

            for filename in zip_data.keys():
                if filename.endswith('.xml'):  # Check all XML files (headers, footers, document)
                    xml_content = zip_data[filename].decode('utf-8', errors='ignore')
                    if '{{rev}}' in xml_content or '{{date}}' in xml_content:
                        # Update the XML with new rev and date
                        updated_xml = xml_content.replace('{{rev}}', new_rev).replace('{{date}}', new_date)
                        zip_data[filename] = updated_xml.encode('utf-8')
                        updated = True

            if not updated:
                return JsonResponse({"error": "Could not find {{rev}} or {{date}} in any XML file."}, status=500)

            # 3. Create a new .docx file with the updated content
            output = BytesIO()
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                # Write all files
                for filename, content in zip_data.items():
                    zip_out.writestr(filename, content)

            # 4. Save the updated .docx to the output file
            with open(output_path, 'wb') as f:
                f.write(output.getvalue())

            # 5. Serve the updated .docx file as an inline file for preview/download
            docx_file = open(output_path, 'rb')
            response = FileResponse(docx_file, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'inline; filename="template_panel.docx"'

            return response

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

#Manuscript Submission
class ManuscriptSubmissionView(APIView):
    parser_classes = (MultiPartParser, FormParser)  # Allows file uploads

    def post(self, request, *args, **kwargs):
        user = request.user  # Get the authenticated user

        title = request.data.get("title")
        description = request.data.get("description", "").strip()  # Optional description
        pdf = request.FILES.get("pdf")

        if not title or not pdf:
            return JsonResponse({"error": "Title and PDF file are required."}, status=400)

        # Save manuscript with user info
        manuscript = Manuscript.objects.create(
            user=user,
            title=title,
            description=description,
            pdf=pdf
        )

        return JsonResponse({
            "message": "Manuscript submitted successfully",
            "id": manuscript.id,
            "first_name": manuscript.first_name,
            "last_name": manuscript.last_name,
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
                "first_name": manuscript.first_name,
                "last_name": manuscript.last_name,
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
