import os

from docxtpl import DocxTemplate
from docx2pdf import convert

from datetime import datetime
from django.http import HttpResponse, JsonResponse, FileResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from djoser.social.views import ProviderAuthView
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

class ApplicationDocxView(APIView):
    def post(self, request, *args, **kwargs):
        context = request.data
        template_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_application.docx'
        )

        if not os.path.exists(template_path):
            return JsonResponse({"error": "Template file not found."}, status=404)
        
        try:
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

            # 3. Convert the .docx to .pdf
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


class PanelDocxView(APIView):
    def post(self, request, *args, **kwargs):
        context = request.data
        template_path = os.path.join(
            settings.BASE_DIR, 'rkive', 'templates', 'word_templates', 'template_panel.docx'
        )

        if not os.path.exists(template_path):
            return JsonResponse({"error": "Template file not found."}, status=404)
        
        try:
            # 1. Render the document
            doc = DocxTemplate(template_path)
            doc.render(context)

            # 2. Generate a unique filename for the .docx
            docx_filename = f"IT-Nomination-of-Members-of-Oral-Examination-Panel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            docx_file_path = os.path.join(settings.MEDIA_ROOT, "generated_documents", docx_filename)
            os.makedirs(os.path.dirname(docx_file_path), exist_ok=True)
            doc.save(docx_file_path)

            # 3. Convert .docx to .pdf
            pdf_filename = docx_filename.replace('.docx', '.pdf')
            pdf_file_path = os.path.join(settings.MEDIA_ROOT, "generated_documents", pdf_filename)
            convert(docx_file_path, pdf_file_path)

            # 4. Remove the .docx file (if you don't need it anymore)
            os.remove(docx_file_path)

            # 5. Serve the PDF as an inline file so the user can preview/download
            pdf_file = open(pdf_file_path, 'rb')
            response = FileResponse(pdf_file, content_type='application/pdf')

            # Inline content-disposition allows preview in the browser and user download from there
            response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
            return response
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)