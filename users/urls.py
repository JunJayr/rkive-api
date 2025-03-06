from django.urls import path, re_path
from .views import(
    CustomProviderAuthView,
    CustomTokenObtainPairView,
    UserRoleView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView,
    ApplicationDocxView,
    ApplicationAdminDocxView,
    PanelDocxView,
    ManuscriptSubmissionView,
    DocumentCountView,
    ListDocumentFilesView,
    ListUsersView,
    
)

urlpatterns = [
    re_path(
        r'^o/(?P<provider>\S+)/$',
        CustomProviderAuthView.as_view(),
        name='provider-auth'
    ),
    path('jwt/create/', CustomTokenObtainPairView.as_view()),
    path('jwt/refresh/', CustomTokenRefreshView.as_view()),
    path('user-role/', UserRoleView.as_view()),
    path('jwt/verify/', CustomTokenVerifyView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('application-docx/', ApplicationDocxView.as_view()),
    path('defense-application-admin/', ApplicationAdminDocxView.as_view()),
    path('panel-docx/', PanelDocxView.as_view()),
    path('manuscripts/', ManuscriptSubmissionView.as_view()),

    path('document-count/', DocumentCountView.as_view()),
    path('list-files/', ListDocumentFilesView.as_view()),
    path('list-users/', ListUsersView.as_view()),
    path('list-users/<int:user_id>/', ListUsersView.as_view()),
]

