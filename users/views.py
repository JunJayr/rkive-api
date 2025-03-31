import os
from datetime import datetime
from io import BytesIO

import pythoncom
import zipfile
from win32com.client import Dispatch
from docxtpl import DocxTemplate
from docx2pdf import convert

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from djoser.social.views import ProviderAuthView
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .models import *
from .serializers import SubmissionReviewSerializer, ContentTypeSerializer

User = get_user_model()

# Authentication Views
class CustomProviderAuthView(ProviderAuthView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 201:
            self._set_auth_cookies(response)
        return response

    def _set_auth_cookies(self, response):
        access_token = response.data.get('access')
        refresh_token = response.data.get('refresh')
        cookie_settings = {
            'max_age': settings.AUTH_COOKIE_MAX_AGE,
            'path': settings.AUTH_COOKIE_PATH,
            'secure': settings.AUTH_COOKIE_SECURE,
            'httponly': settings.AUTH_COOKIE_HTTP_ONLY,
            'samesite': settings.AUTH_COOKIE_SAMESITE,
        }
        response.set_cookie('access', access_token, **cookie_settings)
        response.set_cookie('refresh', refresh_token, **cookie_settings)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            self._set_auth_cookies(response)
        return response

    def _set_auth_cookies(self, response):
        access_token = response.data.get('access')
        refresh_token = response.data.get('refresh')
        cookie_settings = {
            'max_age': settings.AUTH_COOKIE_MAX_AGE,
            'path': settings.AUTH_COOKIE_PATH,
            'secure': settings.AUTH_COOKIE_SECURE,
            'httponly': settings.AUTH_COOKIE_HTTP_ONLY,
            'samesite': settings.AUTH_COOKIE_SAMESITE,
        }
        response.set_cookie('access', access_token, **cookie_settings)
        response.set_cookie('refresh', refresh_token, **cookie_settings)


class UserRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_dean': user.is_dean,
            'is_headdept': user.is_headdept,
            'is_faculty': user.is_faculty,
            'is_student': user.is_student,
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
                samesite=settings.AUTH_COOKIE_SAMESITE,
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


# Document Generation Views
class ApplicationDocxView(APIView):
    def post(self, request, *args, **kwargs):
        context = request.data
        user = request.user
        template_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_application.docx'
        )

        if not os.path.exists(template_path):
            return JsonResponse({'error': 'Template file not found.'}, status=404)

        try:
            pythoncom.CoInitialize()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            docx_filename = f'Application-for-Oral-Defense_{timestamp}.docx'
            pdf_filename = docx_filename.replace('.docx', '.pdf')
            docx_file_path = os.path.join(settings.MEDIA_ROOT, 'defense_application', docx_filename)
            pdf_file_path = os.path.join(settings.MEDIA_ROOT, 'defense_application', pdf_filename)

            os.makedirs(os.path.dirname(docx_file_path), exist_ok=True)

            docx_context = self._prepare_docx_context(context)
            doc = DocxTemplate(template_path)
            doc.render(docx_context)
            doc.save(docx_file_path)

            self._convert_to_pdf(docx_file_path, pdf_file_path)
            doc_record = self._save_application_record(user, context, pdf_filename)
            os.remove(docx_file_path)

            return self._serve_pdf_response(pdf_file_path, pdf_filename)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            pythoncom.CoUninitialize()

    def _prepare_docx_context(self, context):
        docx_context = context.copy()
        for key in ['panel_chair', 'adviser', 'panel1', 'panel2', 'panel3']:
            docx_context[key] = self._get_faculty_name(context.get(key))
        return docx_context

    def _get_faculty_name(self, faculty_id):
        faculty = Faculty.objects.filter(facultyID=faculty_id).first()
        return faculty.name if faculty else 'Unknown'

    def _get_faculty_object(self, faculty_id):
        return Faculty.objects.filter(facultyID=faculty_id).first()

    def _convert_to_pdf(self, docx_path, pdf_path):
        word = Dispatch('Word.Application')
        word.Visible = False
        doc = word.Documents.Open(docx_path)
        doc.SaveAs(pdf_path, FileFormat=17)
        doc.Close()
        word.Quit()

    def _save_application_record(self, user, context, pdf_filename):
        return ApplicationDefense.objects.create(
            user=user,
            department=context.get('department'),
            lead_researcher=context.get('lead_researcher'),
            lead_contactno=context.get('lead_contactno'),
            co_researcher=context.get('co_researcher'),
            co_researcher1=context.get('co_researcher1'),
            co_researcher2=context.get('co_researcher2'),
            co_researcher3=context.get('co_researcher3'),
            co_researcher4=context.get('co_researcher4'),
            research_title=context.get('research_title'),
            datetime_defense=context.get('datetime_defense'),
            place_defense=context.get('place_defense'),
            panel_chair=self._get_faculty_object(context.get('panel_chair')),
            adviser=self._get_faculty_object(context.get('adviser')),
            panel1=self._get_faculty_object(context.get('panel1')),
            panel2=self._get_faculty_object(context.get('panel2')),
            panel3=self._get_faculty_object(context.get('panel3')),
            documenter=context.get('documenter'),
            pdf_file=f'defense_application/{pdf_filename}',
        )

    def _serve_pdf_response(self, pdf_path, pdf_filename):
        pdf_file = open(pdf_path, 'rb')
        response = FileResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
        return response


class ApplicationAdminDocxView(APIView):
    def post(self, request, *args, **kwargs):
        context = request.data
        template_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_application_ISO.docx'
        )
        output_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_application.docx'
        )

        if not os.path.exists(template_path):
            return JsonResponse({'error': 'Template file (template_application_ISO.docx) not found.'}, status=404)

        try:
            zip_data = self._read_docx_template(template_path)
            updated = self._update_xml_content(zip_data, context)
            if not updated:
                return JsonResponse({'error': 'Could not find {{rev}} or {{date}} in any XML file.'}, status=500)

            self._write_updated_docx(zip_data, output_path)
            return self._serve_docx_response(output_path)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def _read_docx_template(self, template_path):
        zip_data = {}
        with zipfile.ZipFile(template_path, 'r') as zip_ref:
            for item in zip_ref.infolist():
                zip_data[item.filename] = zip_ref.read(item.filename)
        return zip_data

    def _update_xml_content(self, zip_data, context):
        new_rev = context.get('rev', '{{rev}}')
        new_date = context.get('date', '{{date}}')
        updated = False
        for filename in zip_data.keys():
            if filename.endswith('.xml'):
                xml_content = zip_data[filename].decode('utf-8', errors='ignore')
                if '{{rev}}' in xml_content or '{{date}}' in xml_content:
                    updated_xml = xml_content.replace('{{rev}}', new_rev).replace('{{date}}', new_date)
                    zip_data[filename] = updated_xml.encode('utf-8')
                    updated = True
        return updated

    def _write_updated_docx(self, zip_data, output_path):
        output = BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for filename, content in zip_data.items():
                zip_out.writestr(filename, content)
        with open(output_path, 'wb') as f:
            f.write(output.getvalue())

    def _serve_docx_response(self, output_path):
        docx_file = open(output_path, 'rb')
        response = FileResponse(
            docx_file,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = 'inline; filename="template_application.docx"'
        return response


class PanelDocxView(APIView):
    def post(self, request, *args, **kwargs):
        context = request.data
        user = request.user
        template_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_panel.docx'
        )

        if not os.path.exists(template_path):
            return JsonResponse({'error': 'Template file not found.'}, status=404)

        try:
            pythoncom.CoInitialize()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            docx_filename = f'Panel-Nomination_{timestamp}.docx'
            pdf_filename = docx_filename.replace('.docx', '.pdf')
            docx_file_path = os.path.join(settings.MEDIA_ROOT, 'panel_nomination', docx_filename)
            pdf_file_path = os.path.join(settings.MEDIA_ROOT, 'panel_nomination', pdf_filename)

            os.makedirs(os.path.dirname(docx_file_path), exist_ok=True)

            docx_context = self._prepare_docx_context(context)
            doc = DocxTemplate(template_path)
            doc.render(docx_context)
            doc.save(docx_file_path)

            self._convert_to_pdf(docx_file_path, pdf_file_path)
            panel_record = self._save_panel_record(user, context, docx_filename, pdf_filename)
            os.remove(docx_file_path)

            return self._serve_pdf_response(pdf_file_path, pdf_filename)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            pythoncom.CoUninitialize()

    def _prepare_docx_context(self, context):
        docx_context = context.copy()
        for key in ['adviser', 'panel_chair', 'panel1', 'panel2', 'panel3']:
            docx_context[key] = self._get_faculty_name(context.get(key))
        return docx_context

    def _get_faculty_name(self, faculty_id):
        faculty = Faculty.objects.filter(facultyID=faculty_id).first()
        return faculty.name if faculty else 'Unknown'

    def _get_faculty_object(self, faculty_id):
        return Faculty.objects.filter(facultyID=faculty_id).first()

    def _convert_to_pdf(self, docx_path, pdf_path):
        word = Dispatch('Word.Application')
        word.Visible = False
        doc = word.Documents.Open(docx_path)
        doc.SaveAs(pdf_path, FileFormat=17)
        doc.Close()
        word.Quit()

    def _save_panel_record(self, user, context, docx_filename, pdf_filename):
        return PanelApplication.objects.create(
            user=user,
            research_title=context.get('research_title'),
            lead_researcher=context.get('lead_researcher'),
            co_researcher=context.get('co_researcher'),
            co_researcher1=context.get('co_researcher1'),
            co_researcher2=context.get('co_researcher2'),
            co_researcher3=context.get('co_researcher3'),
            co_researcher4=context.get('co_researcher4'),
            adviser=self._get_faculty_object(context.get('adviser')),
            panel_chair=self._get_faculty_object(context.get('panel_chair')),
            panel1=self._get_faculty_object(context.get('panel1')),
            panel2=self._get_faculty_object(context.get('panel2')),
            panel3=self._get_faculty_object(context.get('panel3')),
            docx_file=f'panel_nomination/{docx_filename}',
            pdf_file=f'panel_nomination/{pdf_filename}',
        )

    def _serve_pdf_response(self, pdf_path, pdf_filename):
        pdf_file = open(pdf_path, 'rb')
        response = FileResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
        return response


class PanelAdminDocxView(APIView):
    def post(self, request, *args, **kwargs):
        context = request.data
        template_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_panel_ISO.docx'
        )
        output_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_panel.docx'
        )

        if not os.path.exists(template_path):
            return JsonResponse({'error': 'Template file (template_panel_ISO.docx) not found.'}, status=404)

        try:
            zip_data = self._read_docx_template(template_path)
            updated = self._update_xml_content(zip_data, context)
            if not updated:
                return JsonResponse({'error': 'Could not find {{rev}} or {{date}} in any XML file.'}, status=500)

            self._write_updated_docx(zip_data, output_path)
            return self._serve_docx_response(output_path)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def _read_docx_template(self, template_path):
        zip_data = {}
        with zipfile.ZipFile(template_path, 'r') as zip_ref:
            for item in zip_ref.infolist():
                zip_data[item.filename] = zip_ref.read(item.filename)
        return zip_data

    def _update_xml_content(self, zip_data, context):
        new_rev = context.get('rev', '{{rev}}')
        new_date = context.get('date', '{{date}}')
        updated = False
        for filename in zip_data.keys():
            if filename.endswith('.xml'):
                xml_content = zip_data[filename].decode('utf-8', errors='ignore')
                if '{{rev}}' in xml_content or '{{date}}' in xml_content:
                    updated_xml = xml_content.replace('{{rev}}', new_rev).replace('{{date}}', new_date)
                    zip_data[filename] = updated_xml.encode('utf-8')
                    updated = True
        return updated

    def _write_updated_docx(self, zip_data, output_path):
        output = BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for filename, content in zip_data.items():
                zip_out.writestr(filename, content)
        with open(output_path, 'wb') as f:
            f.write(output.getvalue())

    def _serve_docx_response(self, output_path):
        docx_file = open(output_path, 'rb')
        response = FileResponse(
            docx_file,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = 'inline; filename="template_panel.docx"'
        return response


# Manuscript Views
class ManuscriptSubmissionView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        user = request.user
        title = request.data.get('title')
        description = request.data.get('description', '').strip()
        pdf = request.FILES.get('pdf')

        if not title or not pdf:
            return JsonResponse({'error': 'Title and PDF file are required.'}, status=400)

        manuscript = Manuscript.objects.create(
            user=user,
            title=title,
            description=description,
            pdf=pdf,
        )

        return JsonResponse({
            'message': 'Manuscript submitted successfully',
            'manuscriptID': manuscript.manuscriptID,
            'title': manuscript.title,
            'description': manuscript.description,
            'pdf_url': request.build_absolute_uri(manuscript.pdf.url),
            'created_at': manuscript.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }, status=201)

    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('q', '').strip()
        manuscripts = Manuscript.objects.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        ) if search_query else Manuscript.objects.all()

        data = [{
            'manuscriptID': manuscript.manuscriptID,
            'title': manuscript.title,
            'description': manuscript.description,
            'pdf_url': request.build_absolute_uri(manuscript.pdf.url),
            'created_at': manuscript.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        } for manuscript in manuscripts]

        return JsonResponse(data, safe=False, status=200)


class ManuscriptPdfView(APIView):
    def get(self, request, manuscript_id, *args, **kwargs):
        try:
            manuscript = Manuscript.objects.get(id=manuscript_id)
            pdf_path = manuscript.pdf.path
            response = FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="manuscript.pdf"'
            return response
        except Manuscript.DoesNotExist:
            raise Http404('Manuscript not found.')


# Utility Views
class DocumentCountView(APIView):
    def get(self, request, *args, **kwargs):
        generated_docs_path = os.path.join(settings.MEDIA_ROOT, 'generated_documents')
        manuscripts_path = os.path.join(settings.MEDIA_ROOT, 'manuscripts')

        generated_docs_count = len([
            f for f in os.listdir(generated_docs_path)
            if os.path.isfile(os.path.join(generated_docs_path, f))
        ])
        manuscripts_count = len([
            f for f in os.listdir(manuscripts_path)
            if os.path.isfile(os.path.join(manuscripts_path, f))
        ])

        return JsonResponse({
            'generated_documents_count': generated_docs_count,
            'manuscripts_count': manuscripts_count,
        }, status=200)


class ListDocumentFilesView(APIView):
    def get(self, request, *args, **kwargs):
        base_generated_documents_path = os.path.join(settings.MEDIA_ROOT, 'generated_documents')
        base_manuscripts_path = os.path.join(settings.MEDIA_ROOT, 'manuscripts')

        generated_documents_files = self._list_files(base_generated_documents_path)
        manuscripts_files = self._list_files(base_manuscripts_path)

        return JsonResponse({
            'generated_documents_files': generated_documents_files,
            'manuscripts_files': manuscripts_files,
        })

    def _list_files(self, directory_path):
        if os.path.exists(directory_path):
            return [
                file for file in os.listdir(directory_path)
                if os.path.isfile(os.path.join(directory_path, file))
            ]
        return []


class ListUsersView(APIView):
    def get(self, request, *args, **kwargs):
        users = User.objects.all().values(
            'userID', 'first_name', 'last_name', 'email', 'is_active', 'is_staff',
            'is_superuser', 'is_dean', 'is_headdept', 'is_faculty', 'is_student',
        )
        return Response(list(users))

    def post(self, request, *args, **kwargs):
        data = request.data

        if User.objects.filter(email=data.get('email')).exists():
            return JsonResponse({'error': 'Email already exists.'}, status=400)

        password = data.get('password')
        repassword = data.get('repassword')
        if not password or password != repassword:
            return JsonResponse({'error': 'Password validation failed.'}, status=400)

        user = User(
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            email=data.get('email'),
        )
        user.set_password(password)
        user.save()

        return JsonResponse({
            'message': 'User created successfully',
            'userID': user.userID,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        }, status=201)

    def put(self, request, *args, **kwargs):
        userID = kwargs.get('userID')
        try:
            user = User.objects.get(userID=userID)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found.'}, status=404)

        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.is_active = request.data.get('is_active', user.is_active)
        user.is_staff = request.data.get('is_staff', user.is_staff)
        user.is_superuser = request.data.get('is_superuser', user.is_superuser)
        user.is_dean = request.data.get('is_dean', user.is_dean)
        user.is_headdept = request.data.get('is_headdept', user.is_headdept)
        user.is_faculty = request.data.get('is_faculty', user.is_faculty)
        user.is_student = request.data.get('is_student', user.is_student)
        user.save()

        return JsonResponse({
            'message': 'User updated successfully',
            'userID': user.userID,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_dean': user.is_dean,
            'is_headdept': user.is_headdept,
            'is_faculty': user.is_faculty,
            'is_student': user.is_student,
        }, status=200)

    def delete(self, request, *args, **kwargs):
        userID = kwargs.get('userID')
        try:
            user = User.objects.get(userID=userID)
            user.delete()
            return JsonResponse({'message': 'User deleted successfully.'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found.'}, status=404)


class SubmissionReviewViewSet(viewsets.ModelViewSet):
    queryset = SubmissionReview.objects.all()
    serializer_class = SubmissionReviewSerializer

class ContentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    permission_classes = [IsAdminUser]  # Optional: Restrict to admin users