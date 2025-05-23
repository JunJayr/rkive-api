from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from .views import(
    CustomProviderAuthView,
    CustomTokenObtainPairView,
    UserRoleView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView,
    FacultyListView,
    ApplicationDocxView,
    ApplicationAdminDocxView,
    ProposalApplicationDocxView,
    FinalApplicationDocxView,
    PanelDocxView,
    PanelAdminDocxView,
    ManuscriptSubmissionView,
    DocumentCountView,
    ListDocumentFilesView,
    ListUsersView,
    SubmissionReviewViewSet,
    ContentTypeViewSet
)

router = DefaultRouter()
router.register(r'submission-reviews', SubmissionReviewViewSet, basename='submission-review')
router.register(r'content-types', ContentTypeViewSet, basename='content-type')

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
    
    path('faculty/', FacultyListView.as_view()),
    path('application-docx/', ApplicationDocxView.as_view()),
    path('proposal-application-docx/', ProposalApplicationDocxView.as_view()),
    path('final-application-docx/', FinalApplicationDocxView.as_view()),
    path('defense-application-admin/', ApplicationAdminDocxView.as_view()),
    path('panel-docx/', PanelDocxView.as_view()),
    path('defense-panel-admin/', PanelAdminDocxView.as_view()),
    path('manuscripts/', ManuscriptSubmissionView.as_view()),

    path('document-count/', DocumentCountView.as_view()),
    path('list-files/', ListDocumentFilesView.as_view()),
    path('list-users/', ListUsersView.as_view()),
    path('list-users/<int:userID>/', ListUsersView.as_view()),
    
    path('', include(router.urls)),
]

